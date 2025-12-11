# thn_cli/syncv2/engine.py

"""
Unified apply engine for Sync V2 (Hybrid-Standard)

Features:
    • Signature verification (Ed25519, persistent keys)
    • Per-file hashing for raw-zip mode
    • CDC-delta mode (mode: "cdc-delta") using the chunk store
    • Sync Status DB recording of operations (apply + dry-run)
    • Always-on routing decision with manual override support

Routing behavior:
    • For every envelope (any mode), a routing decision is computed.
    • Manual override is honored when present:

          manifest["routing_override"]  (preferred)
          manifest["routing"]           (fallback)

      Example structure:

          "routing_override": {
              "project": "NyxForge",
              "module": "cli",
              "category": "assets",
              "subfolder": "sync_v2",
              "source": "manual",
              "confidence": 1.0
          }

    • If no override exists, the engine calls:

          thn_cli.routing.integration.resolve_routing(
              tag=manifest.get("tag", "sync_v2"),
              zip_bytes=None,     # classifier disabled at engine level
              paths=get_thn_paths()
          )

    • Routing is currently used for metadata + logging:
          - included in the returned result dict
          - persisted inside Sync Status DB notes field

      File placement behavior for raw-zip and CDC-delta remains unchanged.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import zipfile
import hashlib
import os

from thn_cli.syncv2.targets.base import SyncTarget
from thn_cli.syncv2.utils.fs_ops import (
    sha256_of_file,
    safe_backup_folder,
    restore_backup_zip,
    extract_zip_to_temp,
    safe_promote,
)
from thn_cli.syncv2.keys import verify_manifest_signature
from thn_cli.syncv2.delta.apply import apply_cdc_delta_envelope
import thn_cli.syncv2.status_db as status_db
import thn_cli.syncv2.state as sync_state

# Routing + pathing (Hybrid-Standard integration)
from thn_cli.routing.integration import resolve_routing
from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_raw_zip(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validation for raw-zip envelopes:

      1. Signature verification
      2. Per-file hash verification (if present)
      3. Overall payload hash

    Expects envelope to contain:
        manifest: dict
        payload_zip: path to the payload ZIP on disk
    """
    errors: List[str] = []
    manifest = envelope.get("manifest", {})
    payload_zip = envelope.get("payload_zip")

    if not payload_zip:
        return {
            "valid": False,
            "errors": ["Missing payload_zip in envelope."],
            "hash": None,
        }

    # 1) Signature
    sig_errors = verify_manifest_signature(manifest)
    errors.extend(sig_errors)

    # 2) Per-file hashes (optional, based on 'file_hashes' in manifest)
    expected_hashes = manifest.get("file_hashes", {})
    if expected_hashes:
        try:
            computed: Dict[str, str] = {}
            with zipfile.ZipFile(payload_zip, "r") as z:
                for name in z.namelist():
                    if name.endswith("/"):
                        continue
                    with z.open(name) as f:
                        h = hashlib.sha256()
                        for chunk in iter(lambda: f.read(65536), b""):
                            h.update(chunk)
                        computed[name] = h.hexdigest()
            for name, expected in expected_hashes.items():
                actual = computed.get(name)
                if actual != expected:
                    errors.append(f"Hash mismatch for {name}")
        except Exception as exc:
            errors.append(f"Failed to hash payload contents: {exc}")

    # 3) Overall payload hash
    try:
        payload_hash = sha256_of_file(payload_zip)
    except Exception as exc:
        errors.append(f"Failed to compute payload hash: {exc}")
        payload_hash = None

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "hash": payload_hash,
    }


def validate_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatch validation based on manifest['mode'].

      mode == "raw-zip"   → _validate_raw_zip()
      mode == "cdc-delta" → signature only; structural checks during apply

    Returns:
        {
            "valid": bool,
            "errors": [str, ...],
            "hash": Optional[str],   # payload hash for raw-zip
        }
    """
    manifest = envelope.get("manifest", {})
    mode = manifest.get("mode", "raw-zip")

    if mode == "cdc-delta":
        # Minimal upfront validation: signature only; chunk availability and
        # structure are validated during apply.
        errors: List[str] = []
        sig_errors = verify_manifest_signature(manifest)
        errors.extend(sig_errors)
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "hash": None,
        }

    # Default to raw-zip validation
    return _validate_raw_zip(envelope)


# ---------------------------------------------------------------------------
# Routing integration (always-on with manual override)
# ---------------------------------------------------------------------------

def _normalize_routing_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a routing dict to the standard shape:

        {
            "project": str | None,
            "module": str | None,
            "category": str,
            "subfolder": str | None,
            "source": str,
            "confidence": float,
        }
    """
    return {
        "project": raw.get("project"),
        "module": raw.get("module"),
        "category": raw.get("category") or "assets",
        "subfolder": raw.get("subfolder"),
        "source": raw.get("source", "manual"),
        "confidence": float(raw.get("confidence", 1.0)),
    }


def _resolve_routing_for_envelope(
    envelope: Dict[str, Any],
    mode: str,
) -> Dict[str, Any]:
    """
    Resolve routing for an envelope, honoring manual overrides when present.

    Manual override (preferred):
        manifest["routing_override"]: dict

    Legacy/manual override (fallback):
        manifest["routing"]: dict

    If no override is present:
        uses resolve_routing(tag, zip_bytes=None, paths=get_thn_paths()).

    Any errors in routing resolution fall back to a safe default and do NOT
    cause the sync operation to fail.
    """
    manifest = envelope.get("manifest", {}) or {}
    override = manifest.get("routing_override") or manifest.get("routing")

    # Manual override path
    if isinstance(override, dict):
        return _normalize_routing_dict(override)

    # Automatic routing path
    paths = get_thn_paths()
    tag = manifest.get("tag", "sync_v2")

    try:
        # At engine level we do not depend on payload bytes; classifier is
        # effectively disabled here. The routing engine will still provide
        # tag-based decisions and defaults.
        routing = resolve_routing(
            tag=tag,
            zip_bytes=None,
            paths=paths,
        )
        # Ensure normalized shape
        return _normalize_routing_dict(
            {
                "project": routing.get("project"),
                "module": routing.get("module"),
                "category": routing.get("category"),
                "subfolder": routing.get("subfolder"),
                "source": routing.get("source", "auto"),
                "confidence": routing.get("confidence", 0.0),
            }
        )
    except Exception:
        # Routing failures must never break sync; fall back to a safe default.
        return {
            "project": None,
            "module": None,
            "category": "assets",
            "subfolder": "incoming",
            "source": "routing-error",
            "confidence": 0.0,
        }


# ---------------------------------------------------------------------------
# Main apply function
# ---------------------------------------------------------------------------

def apply_envelope_v2(
    envelope: Dict[str, Any],
    target: SyncTarget,
    dry_run: bool,
) -> Dict[str, Any]:
    """
    Apply or simulate apply of an envelope to a given SyncTarget.

    Supports:

      - mode "raw-zip"   (existing behavior)
      - mode "cdc-delta" (CDC-based delta apply)

    On successful dry-run or apply, records an entry in the Sync Status DB.

    Routing:
      - A routing decision is always computed (with manual override support).
      - Routing is attached to the returned result and logged in status_db
        under the 'notes' column as JSON.
      - Current implementation does not yet change filesystem placement based
        on routing; target.destination_path semantics are preserved.
    """
    manifest = envelope.get("manifest", {}) or {}
    payload_zip = envelope.get("payload_zip")
    dest = target.destination_path
    mode = manifest.get("mode", "raw-zip")

    # Precheck
    pre = target.precheck(envelope)
    if not pre.get("ok", True):
        return {
            "success": False,
            "error": "Target precheck failed",
            "reason": pre.get("reason"),
        }

    # Validation (signature + mode-specific checks)
    validation = validate_envelope(envelope)
    if not validation["valid"]:
        return {
            "success": False,
            "error": "Envelope validation failed",
            "errors": validation["errors"],
        }

    manifest_hash = validation["hash"]
    # Attempt to extract source_root/source_zip for logging
    source_root = manifest.get("source_root") or manifest.get("source_zip")
    file_count = manifest.get("file_count")
    total_size = manifest.get("total_size")

    # Envelope path: we may not have a dedicated field; payload_zip is the
    # primary artifact for raw-zip mode. For cdc-delta this may be None.
    envelope_path = payload_zip if isinstance(payload_zip, str) else None

    # Always-on routing resolve (with manual override)
    routing = _resolve_routing_for_envelope(envelope, mode=mode)

    # Base result (extended later)
    base_result: Dict[str, Any] = {
        "target": target.name,
        "destination": dest,
        "mode": mode,
        "manifest_hash": manifest_hash,
        "routing": routing,
    }

    # Dry-run: do not touch filesystem, but log as a status entry
    if dry_run:
        result = {
            **base_result,
            "success": True,
            "operation": "dry-run",
            "file_count": file_count,
            "dry_run": True,
        }

        status_db.record_apply(
            target=target.name,
            mode=mode,
            operation="dry-run",
            dry_run=True,
            success=True,
            manifest_hash=manifest_hash,
            envelope_path=envelope_path,
            source_root=source_root,
            file_count=file_count,
            total_size=total_size,
            backup_zip=None,
            destination=dest,
            notes={"routing": routing},
        )

        return result

    # ----------------------------------------------------------------------
    # Real APPLY
    # ----------------------------------------------------------------------

    # CDC-delta path
    if mode == "cdc-delta":
        backup_zip = safe_backup_folder(
            src_path=dest,
            backup_dir=target.backup_root,
            prefix=f"backup-{target.name}",
        )

        try:
            result = apply_cdc_delta_envelope(
                envelope=envelope,
                payload_zip=payload_zip,
                dest_root=dest,
            )
            if not result.get("success"):
                if backup_zip:
                    restore_backup_zip(backup_zip, dest)
                result.update(
                    {
                        "backup_zip": backup_zip,
                        "restored_previous_state": bool(backup_zip),
                    }
                )
                # Attach routing to error result as well
                result.setdefault("routing", routing)
                return result
        except Exception as exc:
            if backup_zip:
                restore_backup_zip(backup_zip, dest)
            return {
                **base_result,
                "success": False,
                "error": "CDC-delta apply failed; previous backup restored",
                "exception": str(exc),
                "backup_zip": backup_zip,
                "restored_previous_state": bool(backup_zip),
            }

        # Merge snapshot and save new receiver state
        old_snapshot = sync_state.load_last_manifest(target.name)
        new_snapshot = sync_state.merge_snapshot_with_delta(
            old_snapshot=old_snapshot,
            delta_manifest=manifest,
            target_name=target.name,
        )
        sync_state.save_manifest_snapshot(target.name, new_snapshot)

        result = {
            **base_result,
            "success": True,
            "operation": "apply",
            "backup_created": bool(backup_zip),
            "backup_zip": backup_zip,
            "restored_previous_state": False,
        }

        # Record successful apply in status DB
        status_db.record_apply(
            target=target.name,
            mode=mode,
            operation="apply",
            dry_run=False,
            success=True,
            manifest_hash=manifest_hash,
            envelope_path=envelope_path,
            source_root=source_root,
            file_count=file_count,
            total_size=total_size,
            backup_zip=backup_zip,
            destination=dest,
            notes={"routing": routing},
        )

        return result

    # ----------------------------------------------------------------------
    # mode: raw-zip
    # ----------------------------------------------------------------------
    backup_zip = safe_backup_folder(
        src_path=dest,
        backup_dir=target.backup_root,
        prefix=f"backup-{target.name}",
    )

    temp_dir: Optional[str] = None
    try:
        temp_dir = extract_zip_to_temp(
            zip_path=payload_zip,
            prefix=f"thn-sync-{target.name}-",
        )
        safe_promote(temp_dir, dest)

        # Postcheck
        post = target.postcheck(envelope)
        if not post.get("ok", True):
            if backup_zip:
                restore_backup_zip(backup_zip, dest)
            return {
                **base_result,
                "success": False,
                "error": "Target postcheck failed; previous backup restored",
                "reason": post.get("reason"),
                "restored_previous_state": bool(backup_zip),
                "backup_zip": backup_zip,
            }

    except Exception as exc:
        if backup_zip:
            restore_backup_zip(backup_zip, dest)

        return {
            **base_result,
            "success": False,
            "error": "Apply operation failed; previous backup restored",
            "exception": str(exc),
            "restored_previous_state": bool(backup_zip),
            "backup_zip": backup_zip,
        }

    result = {
        **base_result,
        "success": True,
        "operation": "apply",
        "backup_created": bool(backup_zip),
        "backup_zip": backup_zip,
        "file_count": file_count,
        "restored_previous_state": False,
    }

    # Record successful apply in status DB
    status_db.record_apply(
        target=target.name,
        mode=mode,
        operation="apply",
        dry_run=False,
        success=True,
        manifest_hash=manifest_hash,
        envelope_path=envelope_path,
        source_root=source_root,
        file_count=file_count,
        total_size=total_size,
        backup_zip=backup_zip,
        destination=dest,
        notes={"routing": routing},
    )

    return result
