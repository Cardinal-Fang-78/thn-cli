"""
SyncV2 Execution Layer (Hybrid-Standard)
=======================================

This module provides the developer-facing execution helper that builds a
transaction workspace, computes routing, and prepares a file movement plan.

It does *not* perform real SyncV2 apply operations. The authoritative apply
path is `syncv2.engine.apply_envelope_v2()`.

Use cases:
    • Diagnostics
    • Pre-apply previews
    • Blueprint / tooling integrations
"""

from __future__ import annotations

import os
import io
import json
import uuid
import zipfile
from typing import Dict, Any, List

from thn_cli.pathing import get_thn_paths
from thn_cli.routing.integration import resolve_routing
from .txlog import log_transaction


class SyncExecutionError(Exception):
    """Raised when a Sync V2 routing/pre-apply computation fails."""


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

    All routing fields guaranteed present due to Hybrid-Standard routing rules.
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
    Build a SyncV2 execution plan.

    This does NOT apply any changes to real destination trees.

    Steps:
        1. Prepare transaction workspace.
        2. Write manifest.json into workspace.
        3. Materialize envelope files into workspace/files/
        4. Run routing engine once.
        5. Compute per-file source/destination pairs.
        6. If dry_run=True, return plan only.
        7. If dry_run=False, move files to destinations.

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

    manifest = envelope.get("manifest", {})
    files_map = envelope.get("files", {})

    # payload used for ZIP classification
    payload = envelope.get("payload", None)

    paths = get_thn_paths()
    sync_root = paths["sync_root"]

    tx_id = _new_tx_id()
    workspace_root = os.path.join(sync_root, "temp", "v2", tx_id)
    files_root = os.path.join(workspace_root, "files")
    manifest_path = os.path.join(workspace_root, "manifest.json")

    os.makedirs(files_root, exist_ok=True)

    files_info: List[Dict[str, Any]] = []

    try:
        # ------------------------------------------------------------------
        # Write manifest into workspace
        # ------------------------------------------------------------------
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=4, ensure_ascii=False)

        # ------------------------------------------------------------------
        # Materialize envelope payload files to workspace
        # ------------------------------------------------------------------
        for rel_path, data in files_map.items():
            out_path = os.path.join(files_root, rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(data)

        # ------------------------------------------------------------------
        # Routing (single call per envelope)
        # ------------------------------------------------------------------
        routing_result = resolve_routing(
            tag=tag,
            zip_bytes=payload,
            paths=paths,
        )

        # ------------------------------------------------------------------
        # Compute per-file plan
        # ------------------------------------------------------------------
        file_entries = manifest.get("files", [])
        for entry in file_entries:
            logical_path = entry.get("path")
            if not logical_path:
                continue

            source_path = os.path.join(files_root, logical_path)
            if not os.path.isfile(source_path):
                raise SyncExecutionError(
                    f"Expected file missing from envelope: {logical_path}"
                )

            dest_path = _compute_destination(paths, routing_result, logical_path)

            files_info.append(
                {
                    "logical_path": logical_path,
                    "source": source_path,
                    "dest": dest_path,
                }
            )

        # ------------------------------------------------------------------
        # DRY-RUN: return plan only
        # ------------------------------------------------------------------
        if dry_run:
            tx_rec = {
                "tx_id": tx_id,
                "status": "DRY_RUN",
                "dry_run": True,
                "workspace": workspace_root,
                "routing": routing_result,
                "files": files_info,
                "manifest": {
                    "version": manifest.get("version"),
                    "file_count": len(file_entries),
                    "mode": manifest.get("mode"),
                },
            }
            log_transaction(tx_rec)
            return tx_rec

        # ------------------------------------------------------------------
        # APPLY: Move workspace files -> destination
        # (Developer tooling only — real Sync uses engine.apply_envelope_v2.)
        # ------------------------------------------------------------------
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
            "manifest": {
                "version": manifest.get("version"),
                "file_count": len(file_entries),
                "mode": manifest.get("mode"),
            },
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
