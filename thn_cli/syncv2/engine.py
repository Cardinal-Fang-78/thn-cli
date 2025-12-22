# thn_cli/syncv2/engine.py

"""
Unified apply engine for Sync V2 (Hybrid-Standard)

Notes
-----
This module is the authoritative apply path for Sync V2.

Observability:
    • This engine emits an append-only transaction log record via syncv2.txlog.
    • The log is best-effort and MUST NOT interrupt apply semantics.

Status DB:
    • Status DB integration is handled separately.
    • status_db is authoritative history, not an execution controller.

CDC-delta backup semantics (important)
--------------------------------------
Historically, the engine backed up the *entire destination folder* before apply.

That is safe, but on Windows it can be extremely slow or appear to "hang" if the
destination is large (which can happen in tests if the default target destination
resolves to a non-temporary folder).

To keep CDC apply deterministic and fast (and avoid deadlocks/timeouts in golden
subprocess tests), CDC-delta backups here are **path-scoped**:

    • Only the files declared in manifest["files"] are backed up (if present)
    • The backup is a zip written under target.backup_root
    • Restore re-extracts those files if apply fails

This preserves rollback for the touched files without zipping an entire tree.

CONTRACT STATUS
---------------
LOCKED CORE INFRASTRUCTURE
"""

from __future__ import annotations

import os
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import thn_cli.syncv2.state as sync_state
import thn_cli.syncv2.status_db as status_db
from thn_cli.pathing import get_thn_paths
from thn_cli.routing.integration import resolve_routing
from thn_cli.syncv2.delta.apply import apply_cdc_delta_envelope
from thn_cli.syncv2.keys import verify_manifest_signature
from thn_cli.syncv2.targets.base import SyncTarget
from thn_cli.syncv2.txlog import log_transaction
from thn_cli.syncv2.utils.fs_ops import (
    extract_zip_to_temp,
    restore_backup_zip,
    safe_backup_folder,
    safe_promote,
    sha256_of_file,
)

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _manifest_declares_signature(manifest: Dict[str, Any]) -> bool:
    return bool(
        manifest.get("signature") or manifest.get("signature_type") or manifest.get("public_key")
    )


def _validate_raw_zip(envelope: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    manifest = envelope.get("manifest", {}) or {}
    payload_zip = envelope.get("payload_zip")

    if not payload_zip:
        return {"valid": False, "errors": ["Missing payload_zip"], "hash": None}

    if _manifest_declares_signature(manifest):
        errors.extend(verify_manifest_signature(manifest))

    try:
        payload_hash = sha256_of_file(payload_zip)
    except Exception as exc:
        errors.append(str(exc))
        payload_hash = None

    return {"valid": not errors, "errors": errors, "hash": payload_hash}


def validate_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envelope validation is intentionally policy-neutral.

    Signature material is verified ONLY when explicitly declared in the manifest.
    Requiring signatures is a future, opt-in strict-mode policy (env flag or CLI flag),
    not default engine behavior. This keeps validation deterministic and goldens stable.
    """
    manifest = envelope.get("manifest", {}) or {}
    mode = manifest.get("mode", "raw-zip")

    if mode == "cdc-delta":
        errors: List[str] = []
        if _manifest_declares_signature(manifest):
            errors.extend(verify_manifest_signature(manifest))
        return {"valid": not errors, "errors": errors, "hash": None}

    return _validate_raw_zip(envelope)


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _normalize_routing_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "project": raw.get("project"),
        "module": raw.get("module"),
        "category": raw.get("category") or "assets",
        "subfolder": raw.get("subfolder"),
        "source": raw.get("source", "auto"),
        "confidence": float(raw.get("confidence", 0.0)),
    }


def _resolve_routing_for_envelope(envelope: Dict[str, Any], mode: str) -> Dict[str, Any]:
    manifest = envelope.get("manifest", {}) or {}
    override = manifest.get("routing_override") or manifest.get("routing")

    if isinstance(override, dict):
        return _normalize_routing_dict(override)

    try:
        routing = resolve_routing(
            tag=manifest.get("tag", "sync_v2"),
            zip_bytes=None,
            paths=get_thn_paths(),
        )
        return _normalize_routing_dict(routing)
    except Exception:
        return {
            "project": None,
            "module": None,
            "category": "assets",
            "subfolder": None,
            "source": "routing-error",
            "confidence": 0.0,
        }


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------


def _tx_id_for_call(envelope: Dict[str, Any]) -> str:
    """
    Provide a best-effort tx_id for observability.

    This tx_id is used ONLY for logging and does not affect apply semantics.
    """
    existing = envelope.get("tx_id")
    if isinstance(existing, str) and existing.strip():
        return existing.strip()
    return uuid.uuid4().hex


def _safe_log(entry: Dict[str, Any]) -> None:
    """
    Best-effort log emission. Must never interrupt apply.
    """
    try:
        log_transaction(entry)
    except Exception:
        # txlog.log_transaction already swallows write failures, but keep engine safe.
        pass


# ---------------------------------------------------------------------------
# CDC backup helpers (path-scoped)
# ---------------------------------------------------------------------------


def _cdc_declared_paths(manifest: Dict[str, Any]) -> List[str]:
    raw = manifest.get("files", [])
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        p = item.get("path")
        if isinstance(p, str) and p.strip():
            out.append(p.strip())
    return out


def _safe_backup_cdc_paths(
    *,
    dest_root: str,
    backup_dir: str,
    prefix: str,
    logical_paths: List[str],
) -> str | None:
    """
    Create a best-effort backup zip containing only the files declared in the CDC manifest.

    Returns the backup zip path, or None if nothing was backed up.
    """
    dest_path = Path(dest_root)
    backup_root = Path(backup_dir)

    if not logical_paths:
        return None

    # If destination doesn't exist, there is nothing to back up.
    if not dest_path.exists():
        return None

    # Collect existing files to back up.
    to_backup: List[tuple[Path, str]] = []
    for logical in logical_paths:
        # CDC manifests are POSIX-style. Normalize safely for host OS.
        rel = Path(*logical.split("/"))
        abs_path = dest_path / rel
        if abs_path.exists() and abs_path.is_file():
            # Store in zip using POSIX arcname for deterministic restore.
            arcname = "/".join(rel.parts)
            to_backup.append((abs_path, arcname))

    if not to_backup:
        return None

    backup_root.mkdir(parents=True, exist_ok=True)

    # Deterministic, collision-resistant name.
    # (Avoid timestamps to keep tests deterministic if paths are inspected.)
    backup_zip = backup_root / f"{prefix}-{uuid.uuid4().hex}.zip"

    try:
        with zipfile.ZipFile(backup_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for abs_path, arcname in to_backup:
                zf.write(abs_path, arcname=arcname)
    except Exception:
        # If backup fails, treat as "no backup" rather than blocking apply.
        try:
            if backup_zip.exists():
                backup_zip.unlink()
        except Exception:
            pass
        return None

    return str(backup_zip)


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_envelope_v2(
    envelope: Dict[str, Any],
    target: SyncTarget,
    dry_run: bool,
) -> Dict[str, Any]:
    manifest = envelope.get("manifest", {}) or {}
    payload_zip = envelope.get("payload_zip")
    mode = manifest.get("mode", "raw-zip")
    dest = target.destination_path

    tx_id = _tx_id_for_call(envelope)

    validation = validate_envelope(envelope)
    if not validation["valid"]:
        result = {
            "success": False,
            "error": "Envelope validation failed",
            "errors": validation["errors"],
        }
        _safe_log(
            {
                "tx_id": tx_id,
                "status": "FAILED",
                "dry_run": bool(dry_run),
                "target": target.name,
                "mode": mode,
                "routing": {"target": target.name},
                "result": result,
            }
        )
        return result

    routing = _resolve_routing_for_envelope(envelope, mode)

    base = {
        "target": target.name,
        "destination": dest,
        "mode": mode,
        "routing": routing,
    }

    if dry_run:
        result = {**base, "success": True, "operation": "dry-run"}
        _safe_log(
            {
                "tx_id": tx_id,
                "status": "DRY_RUN",
                "dry_run": True,
                "target": target.name,
                "mode": mode,
                "routing": {**routing, "target": target.name},
                "result": result,
            }
        )
        return result

    # ------------------------------------------------------------------
    # CDC-DELTA APPLY
    # ------------------------------------------------------------------
    if mode == "cdc-delta":
        declared_paths = _cdc_declared_paths(manifest)

        # Path-scoped backup: only declared files that currently exist under dest.
        backup_zip = _safe_backup_cdc_paths(
            dest_root=dest,
            backup_dir=target.backup_root,
            prefix=f"backup-{target.name}",
            logical_paths=declared_paths,
        )

        try:
            cdc_result = apply_cdc_delta_envelope(
                envelope=envelope,
                payload_zip=payload_zip,
                dest_root=dest,
            )
        except Exception as exc:
            if backup_zip:
                restore_backup_zip(backup_zip, dest)
            result = {
                **base,
                "success": False,
                "error": str(exc),
                "backup_created": bool(backup_zip),
                "backup_zip": backup_zip,
                "restored_previous_state": bool(backup_zip),
            }
            _safe_log(
                {
                    "tx_id": tx_id,
                    "status": "FAILED",
                    "dry_run": False,
                    "target": target.name,
                    "mode": mode,
                    "routing": {**routing, "target": target.name},
                    "result": result,
                }
            )
            return result

        if not cdc_result.get("success"):
            if backup_zip:
                restore_backup_zip(backup_zip, dest)
            result = {
                **base,
                **cdc_result,
                "backup_created": bool(backup_zip),
                "backup_zip": backup_zip,
                "restored_previous_state": bool(backup_zip),
            }
            _safe_log(
                {
                    "tx_id": tx_id,
                    "status": "FAILED",
                    "dry_run": False,
                    "target": target.name,
                    "mode": mode,
                    "routing": {**routing, "target": target.name},
                    "result": result,
                }
            )
            return result

        # ------------------------------------------------------------------
        # CDC APPLY REPORTING CONTRACT
        #
        # CDC-delta apply reporting is DECLARATIVE, not inferential.
        #
        # - applied_count reflects the number of files declared in the manifest
        # - files[] is derived from manifest["files"] (or entries->paths if needed),
        #   not from filesystem diffing
        # - No attempt is made here to compute per-file change deltas
        #
        # Rationale:
        #   • Deterministic output for CLI / GUI / CI consumers
        #   • Stable golden tests
        #   • Avoid simulated or inferred semantics
        # ------------------------------------------------------------------

        declared_files = manifest.get("files", [])
        if not isinstance(declared_files, list):
            declared_files = []

        files = cdc_result.get("files")
        if not isinstance(files, list) or not files:
            files = [
                {
                    "logical_path": f.get("path"),
                    "dest": str(dest),
                    "size": f.get("size"),
                }
                for f in declared_files
                if isinstance(f, dict) and f.get("path")
            ]

        applied_count = cdc_result.get("applied_count")
        if not isinstance(applied_count, int):
            applied_count = len(files) if files else len(declared_files)

        # Snapshot/status DB updates remain staged for later; keep behavior explicit.
        _ = sync_state
        _ = status_db

        result = {
            **base,
            "success": True,
            "operation": "apply",
            "applied_count": applied_count,
            "files": files,
            "backup_created": bool(backup_zip),
            "backup_zip": backup_zip,
            "restored_previous_state": False,
        }
        _safe_log(
            {
                "tx_id": tx_id,
                "status": "OK",
                "dry_run": False,
                "target": target.name,
                "mode": mode,
                "routing": {**routing, "target": target.name},
                "result": result,
            }
        )
        return result

    # ------------------------------------------------------------------
    # RAW ZIP APPLY
    # ------------------------------------------------------------------
    backup_zip = safe_backup_folder(
        src_path=dest,
        backup_dir=target.backup_root,
        prefix=f"backup-{target.name}",
    )

    if not payload_zip:
        if backup_zip:
            restore_backup_zip(backup_zip, dest)
        result = {
            **base,
            "success": False,
            "error": "Missing payload_zip",
            "backup_created": bool(backup_zip),
            "backup_zip": backup_zip,
            "restored_previous_state": bool(backup_zip),
        }
        _safe_log(
            {
                "tx_id": tx_id,
                "status": "FAILED",
                "dry_run": False,
                "target": target.name,
                "mode": mode,
                "routing": {**routing, "target": target.name},
                "result": result,
            }
        )
        return result

    try:
        temp_dir = extract_zip_to_temp(payload_zip, prefix=f"thn-sync-{target.name}-")
        safe_promote(temp_dir, dest)
    except Exception as exc:
        if backup_zip:
            restore_backup_zip(backup_zip, dest)
        result = {
            **base,
            "success": False,
            "error": str(exc),
            "backup_created": bool(backup_zip),
            "backup_zip": backup_zip,
            "restored_previous_state": bool(backup_zip),
        }
        _safe_log(
            {
                "tx_id": tx_id,
                "status": "FAILED",
                "dry_run": False,
                "target": target.name,
                "mode": mode,
                "routing": {**routing, "target": target.name},
                "result": result,
            }
        )
        return result

    result = {
        **base,
        "success": True,
        "operation": "apply",
        "backup_created": bool(backup_zip),
        "backup_zip": backup_zip,
        "restored_previous_state": False,
    }
    _safe_log(
        {
            "tx_id": tx_id,
            "status": "OK",
            "dry_run": False,
            "target": target.name,
            "mode": mode,
            "routing": {**routing, "target": target.name},
            "result": result,
        }
    )
    return result
