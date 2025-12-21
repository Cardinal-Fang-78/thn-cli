# thn_cli/syncv2/executor.py

"""
Sync V2 Execution Layer (Hybrid-Standard)
========================================

RESPONSIBILITIES
----------------
Provides the **developer-facing execution helper** that builds a transaction
workspace, computes routing, and prepares a file movement plan.

This module is responsible for:
    • Preparing a temporary transaction workspace
    • Computing routing results once per envelope
    • Enumerating file-level execution plans
    • Supporting dry-run and diagnostic tooling
    • Logging execution metadata for inspection

It does *not* perform authoritative Sync V2 apply operations.

The only supported production apply path is:

    syncv2.engine.apply_envelope_v2()

INTENDED USE
------------
This module exists to support:
    • Diagnostics
    • Pre-apply previews
    • Developer tooling
    • Blueprint and integration experiments
    • GUI or CI plan visualization

It must never:
    • Mutate authoritative state implicitly
    • Bypass engine validation
    • Introduce alternative apply semantics

AUTHORITY BOUNDARY
------------------
This module is **non-authoritative**.

All correctness, safety, and mutation guarantees are enforced by:
    • syncv2.engine.validate_envelope()
    • syncv2.engine.apply_envelope_v2()

Any behavior here must remain a strict subset of engine semantics.

LIFECYCLE OWNERSHIP
-------------------
Transaction workspaces created under:
    <sync_root>/temp/v2/<tx_id>/

are:
    • Owned by the caller or tooling layer
    • Intended to be ephemeral
    • Not cleaned up automatically by this module

Long-term retention, inspection, or GC policies belong elsewhere.

CDC SCOPE
---------
CDC-delta handling here is **planning-only**.

This module:
    • Reads manifest-declared CDC file lists
    • Computes routing and destinations
    • Does NOT validate CDC integrity
    • Does NOT enforce CDC safety contracts

CDC validation and enforcement belong exclusively to syncv2.engine.

Envelope expectations (normalized):
    envelope["manifest"]: dict
    envelope["payload_zip"]: str (path to extracted payload.zip)
    envelope["source_path"]: str (original envelope zip path)
    envelope["work_dir"]: str (temporary extraction dir holding manifest/payload)

NOTE
----
This module must never be treated as an alternative apply engine.
Any filesystem mutation performed here is explicitly
developer-scoped and non-authoritative.
"""

from __future__ import annotations

import json
import os
import uuid
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from thn_cli.pathing import get_thn_paths
from thn_cli.routing.integration import resolve_routing

from .txlog import log_transaction


class SyncExecutionError(Exception):
    """Raised when a Sync V2 routing or execution-plan computation fails."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_tx_id() -> str:
    return uuid.uuid4().hex


def _compute_destination(
    paths: Dict[str, str],
    routing: Dict[str, Any],
    logical_path: str,
) -> str:
    """
    Compute final destination path for a file.

    Routing hierarchy:
        1. project + module
        2. project
        3. base/incoming/<category>

    CONTRACT
    --------
    • Deterministic
    • Path-only (no filesystem mutation)
    • Mirrors engine routing semantics (non-authoritative mirror)
    """
    base = paths["base"]
    projects_active = paths["projects_active"]

    project = routing.get("project")
    module = routing.get("module")
    category = routing.get("category") or "unclassified"
    subfolder = routing.get("subfolder") or None

    filename = os.path.basename(logical_path)

    if project and module:
        dest_dir = os.path.join(projects_active, project, "modules", module, category)
    elif project:
        dest_dir = os.path.join(projects_active, project, category)
    else:
        dest_dir = os.path.join(base, "incoming", category)

    if subfolder:
        dest_dir = os.path.join(dest_dir, subfolder)

    return os.path.join(dest_dir, filename)


def _zip_list_files(payload_zip_path: str) -> List[Tuple[str, int]]:
    """
    Return a list of (path, size) entries from payload.zip.

    Directories are skipped.

    NOTE
    ----
    Ordering is the ZIP's internal order. This is typically stable for a given
    payload, but callers should not treat ordering as a contract.
    """
    files: List[Tuple[str, int]] = []
    with zipfile.ZipFile(payload_zip_path, "r") as z:
        for info in z.infolist():
            name = info.filename
            if not name or name.endswith("/"):
                continue
            files.append((name, int(getattr(info, "file_size", 0) or 0)))
    return files


def _zip_extract_all(payload_zip_path: str, dest_root: str) -> None:
    """
    Extract payload.zip into a workspace directory.

    NOTE
    ----
    No validation is performed here.
    Validation is assumed to have occurred upstream (engine path).
    """
    with zipfile.ZipFile(payload_zip_path, "r") as z:
        z.extractall(dest_root)


def _manifest_file_entries(
    manifest: Dict[str, Any],
    payload_zip_path: str,
) -> List[Dict[str, Any]]:
    """
    Normalize file entries for execution planning.

    Behavior:
        • CDC-delta: uses manifest["files"]
        • raw-zip: enumerates payload.zip contents

    This mirrors engine planning behavior but omits validation.
    """
    mode = str(manifest.get("mode", "raw-zip") or "raw-zip").lower()

    if mode == "cdc-delta":
        files = manifest.get("files", [])
        if isinstance(files, list):
            return [f for f in files if isinstance(f, dict)]
        return []

    entries: List[Dict[str, Any]] = []
    for path, size in _zip_list_files(payload_zip_path):
        entries.append({"path": path, "size": size})
    return entries


def _entry_logical_path(entry: Dict[str, Any]) -> Optional[str]:
    """
    Extract logical path from a manifest entry.

    Supported shapes:
        • {"path": "..."}
        • {"name": "..."} (fallback)
    """
    p = entry.get("path")
    if isinstance(p, str) and p.strip():
        return p
    n = entry.get("name")
    if isinstance(n, str) and n.strip():
        return n
    return None


# ---------------------------------------------------------------------------
# Core Execution (Routing + Workspace Build)
# ---------------------------------------------------------------------------


def execute_envelope_plan(
    envelope: Dict[str, Any],
    *,
    tag: str = "sync_v2",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Build a Sync V2 execution plan.

    This function never mutates authoritative destination trees unless
    explicitly used in non-production developer tooling.

    Steps:
        1. Prepare transaction workspace
        2. Write manifest.json into workspace
        3. Extract payload.zip into workspace/files/
        4. Run routing engine once (envelope-level)
        5. Compute per-file source/destination pairs
        6. If dry_run=True, return plan only
        7. If dry_run=False, move files (DEV TOOLING ONLY)

    Returns:
        {
            "tx_id": str,
            "status": "OK" | "DRY_RUN" | "FAILED",
            "dry_run": bool,
            "workspace": "<path>",
            "routing": { ... },
            "files": [...],
            "manifest": {...}
        }
    """
    manifest = envelope.get("manifest", {}) or {}
    payload_zip_path = envelope.get("payload_zip")

    if not isinstance(payload_zip_path, str) or not payload_zip_path.strip():
        raise SyncExecutionError("Envelope missing payload_zip (normalized envelope required).")

    if not os.path.isfile(payload_zip_path):
        raise SyncExecutionError(f"Envelope payload_zip does not exist: {payload_zip_path}")

    paths = get_thn_paths()
    sync_root = paths["sync_root"]

    tx_id = _new_tx_id()
    workspace_root = os.path.join(sync_root, "temp", "v2", tx_id)
    files_root = os.path.join(workspace_root, "files")
    manifest_path = os.path.join(workspace_root, "manifest.json")

    os.makedirs(files_root, exist_ok=True)

    files_info: List[Dict[str, Any]] = []

    try:
        # Write manifest (workspace-local; non-authoritative)
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=4, ensure_ascii=False)

        # Extract payload.zip (workspace-local; non-authoritative)
        _zip_extract_all(payload_zip_path, files_root)

        # Routing (single call per envelope)
        routing_result = resolve_routing(
            tag=tag,
            zip_bytes=None,
            paths=paths,
        )

        # Build execution plan
        file_entries = _manifest_file_entries(manifest, payload_zip_path)

        for entry in file_entries:
            logical_path = _entry_logical_path(entry)
            if not logical_path:
                continue

            source_path = os.path.join(files_root, logical_path)
            if not os.path.isfile(source_path):
                raise SyncExecutionError(f"Expected file missing from payload: {logical_path}")

            dest_path = _compute_destination(paths, routing_result, logical_path)

            files_info.append(
                {
                    "logical_path": logical_path,
                    "source": source_path,
                    "dest": dest_path,
                    "size": int(entry.get("size", 0) or 0),
                }
            )

        tx_manifest = {
            "version": manifest.get("version"),
            "file_count": len(files_info),
            "mode": manifest.get("mode"),
        }

        if dry_run:
            tx_rec = {
                "tx_id": tx_id,
                "status": "DRY_RUN",
                "dry_run": True,
                "workspace": workspace_root,
                "routing": routing_result,
                "files": files_info,
                "manifest": tx_manifest,
            }
            log_transaction(tx_rec)
            return tx_rec

        # Developer-only apply (non-authoritative)
        for f in files_info:
            os.makedirs(os.path.dirname(f["dest"]), exist_ok=True)
            os.replace(f["source"], f["dest"])

        tx_rec = {
            "tx_id": tx_id,
            "status": "OK",
            "dry_run": False,
            "workspace": workspace_root,
            "routing": routing_result,
            "files": files_info,
            "manifest": tx_manifest,
        }
        log_transaction(tx_rec)
        return tx_rec

    except Exception as exc:
        tx_rec = {
            "tx_id": tx_id,
            "status": "FAILED",
            "dry_run": dry_run,
            "workspace": workspace_root,
            "error": str(exc),
        }
        log_transaction(tx_rec)
        raise
