# thn_cli/syncv2/engine.py

"""
Unified apply engine for Sync V2 (Hybrid-Standard)

Notes
-----
This module is the authoritative apply path for Sync V2.

Observability:
    • This engine emits scaffold-scoped TXLOG transactions under:
        <scaffold_root>/.thn/txlog/<op>-<tx_id>.jsonl
    • Logging is best-effort and MUST NOT interrupt apply semantics.

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
subprocess tests), CDC-delta backups here are path-scoped:

    • Only the files declared in manifest["files"] are backed up (if present)
    • The backup is a zip written under target.backup_root
    • Restore re-extracts those files if apply fails

This preserves rollback for the touched files without zipping an entire tree.

CONTRACT STATUS
---------------
LOCKED CORE INFRASTRUCTURE
"""

from __future__ import annotations

import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import thn_cli.syncv2.state as sync_state
import thn_cli.syncv2.status_db as status_db
from thn_cli.pathing import get_thn_paths
from thn_cli.routing.integration import resolve_routing
from thn_cli.syncv2.delta.apply import apply_cdc_delta_envelope
from thn_cli.syncv2.keys import verify_manifest_signature
from thn_cli.syncv2.targets.base import SyncTarget
from thn_cli.syncv2.utils.fs_ops import (
    extract_zip_to_temp,
    restore_backup_zip,
    safe_backup_folder,
    safe_promote,
    sha256_of_file,
)
from thn_cli.txlog.txlog_writer import TxLogWriter, start_txlog

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
# TXLOG helpers (scaffold-scoped, history-compatible)
# ---------------------------------------------------------------------------


def _find_scaffold_root_upwards(start: Path) -> Optional[Path]:
    """
    Best-effort scaffold discovery for TXLOG emission.

    A scaffold is considered found if:
        <candidate>/.thn/txlog exists (or if <candidate>/.thn exists).
    """
    try:
        p = start.resolve()
    except Exception:
        p = start

    for candidate in [p, *p.parents]:
        thn_dir = candidate / ".thn"
        if thn_dir.exists() and thn_dir.is_dir():
            return candidate
        txlog_dir = candidate / ".thn" / "txlog"
        if txlog_dir.exists() and txlog_dir.is_dir():
            return candidate

    return None


def _resolve_scaffold_root(manifest: Dict[str, Any]) -> Optional[Path]:
    """
    Determine a reasonable scaffold root for TXLOG emission.

    Order:
        1) Current working directory upward
        2) manifest["source"] upward (raw-zip test envelopes provide this)
    """
    found = _find_scaffold_root_upwards(Path.cwd())
    if found is not None:
        return found

    source = manifest.get("source")
    if isinstance(source, str) and source.strip():
        found2 = _find_scaffold_root_upwards(Path(source.strip()))
        if found2 is not None:
            return found2

    return None


def _safe_txlog_begin(
    *,
    scaffold_root: Optional[Path],
    op: str,
    target_path: str,
    meta: Dict[str, Any],
) -> Optional[TxLogWriter]:
    """
    Best-effort begin. Returns TxLogWriter if started, else None.
    """
    if scaffold_root is None:
        return None

    try:
        w = start_txlog(
            scaffold_root=scaffold_root,
            op=op,
            target=Path(target_path),
        )
        w.begin(meta=meta)
        return w
    except Exception:
        return None


def _safe_txlog_commit(writer: Optional[TxLogWriter], summary: Dict[str, Any]) -> None:
    if writer is None:
        return
    try:
        writer.commit(summary=summary)
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


def _safe_txlog_abort(writer: Optional[TxLogWriter], reason: str, error: str = "") -> None:
    if writer is None:
        return
    try:
        writer.abort(reason=reason, error=error or "")
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Status DB helpers (best-effort, write-only, success paths only)
# ---------------------------------------------------------------------------


def _safe_status_record_apply(
    *,
    target_name: str,
    mode: str,
    operation: str,
    dry_run: bool,
    success: bool,
    manifest_hash: Optional[str],
    envelope_path: Optional[str],
    source_root: Optional[str],
    file_count: Optional[int],
    total_size: Optional[int],
    backup_zip: Optional[str],
    destination: str,
    notes: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Best-effort Status DB write. Must never interrupt apply.

    This is intentionally write-only and is invoked only on terminal success paths.
    """
    try:
        status_db.record_apply(
            target=target_name,
            mode=mode,
            operation=operation,
            dry_run=bool(dry_run),
            success=bool(success),
            manifest_hash=manifest_hash,
            envelope_path=envelope_path,
            source_root=source_root,
            file_count=file_count,
            total_size=total_size,
            backup_zip=backup_zip,
            destination=destination,
            notes=notes,
        )
    except Exception:
        # Best-effort only: never block execution.
        pass


def _best_effort_int(v: Any) -> Optional[int]:
    try:
        if isinstance(v, bool):
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str) and v.strip().isdigit():
            return int(v.strip())
    except Exception:
        pass
    return None


def _cdc_file_stats(manifest: Dict[str, Any]) -> tuple[Optional[int], Optional[int]]:
    """
    Best-effort CDC file_count and total_size derived from manifest["files"] only.
    No filesystem inspection.
    """
    raw = manifest.get("files", [])
    if not isinstance(raw, list):
        return (None, None)

    count = 0
    total = 0
    saw_any = False

    for item in raw:
        if not isinstance(item, dict):
            continue
        p = item.get("path")
        if not isinstance(p, str) or not p.strip():
            continue
        count += 1
        saw_any = True
        sz = _best_effort_int(item.get("size"))
        if isinstance(sz, int) and sz >= 0:
            total += sz

    if not saw_any:
        return (None, None)

    return (count, total)


def _best_effort_envelope_path(envelope: Dict[str, Any]) -> Optional[str]:
    # load_envelope_from_file commonly attaches source_path via inspect_envelope; tolerate absence.
    for key in ("source_path", "envelope_path", "path"):
        v = envelope.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


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

    # ------------------------------------------------------------------
    # Begin scaffold TXLOG transaction (best-effort)
    # ------------------------------------------------------------------
    scaffold_root = _resolve_scaffold_root(manifest)
    txlog_writer = _safe_txlog_begin(
        scaffold_root=scaffold_root,
        op="sync_apply",
        target_path=dest,
        meta={
            "dry_run": bool(dry_run),
            "mode": mode,
            "target": target.name,
            "destination": dest,
        },
    )

    validation = validate_envelope(envelope)
    if not validation["valid"]:
        result = {
            "success": False,
            "error": "Envelope validation failed",
            "errors": validation["errors"],
        }
        _safe_txlog_abort(
            txlog_writer,
            reason="validation_failed",
            error="; ".join([str(e) for e in validation.get("errors", [])]),
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
        # DRY-RUN MUST BE SIDE-EFFECT FREE:
        # - no backups
        # - no temp extraction/promotion
        # - no filesystem writes beyond best-effort TXLOG (scaffold-scoped)
        result = {**base, "success": True, "operation": "dry-run"}
        _safe_txlog_commit(
            txlog_writer,
            summary={
                "outcome": "DRY_RUN",
                "mode": mode,
                "target": target.name,
                "destination": dest,
                "routing": routing,
            },
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
            _safe_txlog_abort(txlog_writer, reason="apply_exception", error=str(exc))
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
            _safe_txlog_abort(
                txlog_writer,
                reason="apply_failed",
                error=str(result.get("error") or "cdc_result.success is false"),
            )
            return result

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

        _safe_txlog_commit(
            txlog_writer,
            summary={
                "outcome": "OK",
                "mode": mode,
                "target": target.name,
                "destination": dest,
                "applied_count": applied_count,
                "backup_created": bool(backup_zip),
                "backup_zip": backup_zip,
            },
        )

        fc, tsz = _cdc_file_stats(manifest)
        _safe_status_record_apply(
            target_name=target.name,
            mode=mode,
            operation="apply",
            dry_run=False,
            success=True,
            manifest_hash=None,
            envelope_path=_best_effort_envelope_path(envelope),
            source_root=manifest.get("source") if isinstance(manifest.get("source"), str) else None,
            file_count=fc,
            total_size=tsz,
            backup_zip=backup_zip,
            destination=dest,
            notes={
                "applied_count": applied_count,
            },
        )

        return result

    # ------------------------------------------------------------------
    # RAW ZIP APPLY
    # ------------------------------------------------------------------

    # Preferred default backup root (safe): dest_parent / "_thn_backups" / "sync_apply"
    # This prevents the catastrophic failure mode where backups are written into the
    # destination tree (which can recursively back up prior backups).
    dest_path = Path(dest)
    safe_backup_root = dest_path.parent / "_thn_backups" / "sync_apply"

    try:
        backup_zip = safe_backup_folder(
            src_path=dest,
            backup_dir=str(safe_backup_root),
            prefix=f"backup-{target.name}",
        )
    except Exception as exc:
        result = {
            **base,
            "success": False,
            "error": str(exc),
            "backup_created": False,
            "backup_zip": None,
            "restored_previous_state": False,
        }
        _safe_txlog_abort(txlog_writer, reason="backup_failed", error=str(exc))
        return result

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
        _safe_txlog_abort(txlog_writer, reason="missing_payload", error="Missing payload_zip")
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
        _safe_txlog_abort(txlog_writer, reason="apply_exception", error=str(exc))
        return result

    result = {
        **base,
        "success": True,
        "operation": "apply",
        "backup_created": bool(backup_zip),
        "backup_zip": backup_zip,
        "restored_previous_state": False,
    }

    _safe_txlog_commit(
        txlog_writer,
        summary={
            "outcome": "OK",
            "mode": mode,
            "target": target.name,
            "destination": dest,
            "backup_created": bool(backup_zip),
            "backup_zip": backup_zip,
        },
    )

    _safe_status_record_apply(
        target_name=target.name,
        mode=mode,
        operation="apply",
        dry_run=False,
        success=True,
        manifest_hash=validation.get("hash"),
        envelope_path=_best_effort_envelope_path(envelope),
        source_root=manifest.get("source") if isinstance(manifest.get("source"), str) else None,
        file_count=_best_effort_int(manifest.get("file_count")),
        total_size=_best_effort_int(manifest.get("total_size")),
        backup_zip=backup_zip,
        destination=dest,
        notes=None,
    )

    return result
