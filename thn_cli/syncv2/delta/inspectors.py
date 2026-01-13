# thn_cli/syncv2/delta/inspectors.py

"""
CDC Delta Inspectors (Hybrid-Standard)
======================================

RESPONSIBILITIES
----------------
Reusable, **read-only** inspection helpers for Sync V2 CDC-delta workflows.

This module exists to support:
    • Diagnostics
    • Inspection
    • Strict-mode preflight validation
    • Future GUI tooling

NON-GOALS
---------
This module MUST NOT:
    • Modify on-disk state
    • Apply envelopes
    • Enforce routing or policy
    • Emit CLI output directly
    • Mutate manifests or payloads

CONTRACT STATUS
---------------
⚠️ DIAGNOSTIC-ONLY OUTPUTS

All helpers in this module:
    • Are internal by default
    • Are NOT CLI-stable contracts unless explicitly surfaced
    • May evolve without version bumps until promoted

If any output becomes externally visible, it MUST be:
    • Explicitly wired in commands_sync.py
    • Covered by golden tests
    • Treated as a locked surface thereafter
"""

from __future__ import annotations

import os
import zipfile
from typing import Any, Dict, List, Set

from thn_cli.syncv2 import state as sync_state
from thn_cli.syncv2.delta.mutation_plan import derive_cdc_mutation_plan

from .store import chunk_exists, get_chunk_path

# ---------------------------------------------------------------------------
# CDC Manifest File Inspection
# ---------------------------------------------------------------------------


def inspect_cdc_manifest_files(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Inspect CDC-declared files from a manifest only.

    CONTRACT
    --------
    • Manifest-only inspection
    • Does NOT inspect payload contents
    • Does NOT validate correctness

    Returns a deterministic list:
        [
            {
                "path": "relative/path",
                "declared_size": int | None,
            },
            ...
        ]

    Invalid or malformed entries are skipped safely.
    """
    files = manifest.get("files", []) or []
    result: List[Dict[str, Any]] = []

    for entry in files:
        if not isinstance(entry, dict):
            continue

        path = entry.get("path")
        size = entry.get("size")

        if not isinstance(path, str):
            continue

        result.append(
            {
                "path": path,
                "declared_size": int(size) if isinstance(size, int) else None,
            }
        )

    return result


# ---------------------------------------------------------------------------
# CDC Mutation Plan Inspection (Diagnostic-Only)
# ---------------------------------------------------------------------------


def inspect_cdc_mutation_plan(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inspect the CDC mutation plan derived from a manifest.

    CONTRACT
    --------
    • Read-only
    • Deterministic
    • No filesystem access
    • No payload inspection
    • No validation beyond structural parsing

    This helper exists to surface **intent**, not effect.

    Returns:
        {
            "writes": [ "path", ... ],
            "deletes": [ "path", ... ],
            "total_writes": int,
            "total_deletes": int,
            "mutation_plan": {
                "writes": [ "path", ... ],
                "deletes": [ "path", ... ],
            },
        }

    Errors are reported in-band and never raised.
    """
    try:
        writes, deletes = derive_cdc_mutation_plan(manifest)

        sorted_writes = sorted(writes)
        sorted_deletes = sorted(deletes)

        return {
            "writes": sorted_writes,
            "deletes": sorted_deletes,
            "total_writes": len(sorted_writes),
            "total_deletes": len(sorted_deletes),
            "mutation_plan": {
                "writes": sorted_writes,
                "deletes": sorted_deletes,
            },
        }

    except Exception as exc:
        return {
            "writes": [],
            "deletes": [],
            "total_writes": 0,
            "total_deletes": 0,
            "mutation_plan": {
                "error": str(exc),
            },
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Payload ZIP Inspection
# ---------------------------------------------------------------------------


def inspect_payload_zip_paths(payload_zip: str) -> Set[str]:
    """
    Return all file paths present in payload.zip.

    CONTRACT
    --------
    • Read-only ZIP inspection
    • Paths returned are normalized POSIX-style
    • Directories are excluded
    • Errors are swallowed (diagnostic-only)

    This function does NOT validate payload correctness.
    """
    paths: Set[str] = set()

    if not payload_zip or not os.path.isfile(payload_zip):
        return paths

    try:
        with zipfile.ZipFile(payload_zip, "r") as zf:
            for info in zf.infolist():
                if not info.is_dir():
                    paths.add(info.filename)
    except Exception:
        # Diagnostic-only: never raise
        pass

    return paths


def check_payload_completeness(
    *,
    manifest: Dict[str, Any],
    payload_zip: str,
) -> Dict[str, Any]:
    """
    Compare CDC manifest declarations against payload.zip contents.

    CONTRACT
    --------
    • Read-only
    • Deterministic
    • Does NOT enforce failure
    • Suitable for diagnostics and strict-mode preflight

    Returns:
        {
            "expected": int,
            "present": int,
            "missing": [ "path", ... ],
            "extra": [ "path", ... ],
        }
    """
    declared = {f["path"] for f in inspect_cdc_manifest_files(manifest)}
    present = inspect_payload_zip_paths(payload_zip)

    missing = sorted(declared - present)
    extra = sorted(present - declared)

    return {
        "expected": len(declared),
        "present": len(declared & present),
        "missing": missing,
        "extra": extra,
    }


# ---------------------------------------------------------------------------
# Snapshot (Receiver State) Inspection
# ---------------------------------------------------------------------------


def summarize_snapshot(target_name: str) -> Dict[str, Any]:
    """
    Summarize the last applied snapshot for a target.

    CONTRACT
    --------
    • Read-only
    • Snapshot-level metadata only
    • No chunk validation

    Returns a minimal, stable diagnostic summary.
    """
    snap = sync_state.load_last_manifest(target_name)
    if snap is None:
        return {
            "target": target_name,
            "has_snapshot": False,
            "entries": 0,
            "total_size": 0,
        }

    entries = snap.get("entries", []) or []
    total_size = sum(int(e.get("size", 0)) for e in entries if isinstance(e, dict))

    return {
        "target": target_name,
        "has_snapshot": True,
        "entries": len(entries),
        "total_size": total_size,
        "mode": snap.get("mode"),
        "version": snap.get("version"),
    }


def snapshot_chunk_health(target_name: str) -> Dict[str, Any]:
    """
    Check whether all chunks referenced by the last snapshot exist locally.

    CONTRACT
    --------
    • Read-only
    • Chunk-store presence only
    • Does NOT attempt repair or recovery
    """
    snap = sync_state.load_last_manifest(target_name)
    if snap is None:
        return {
            "target": target_name,
            "has_snapshot": False,
            "unique_chunk_ids": 0,
            "missing_chunks": [],
        }

    entries = snap.get("entries", []) or []
    all_chunk_ids: Set[str] = set()

    for e in entries:
        for cid in e.get("chunks", []) or []:
            if isinstance(cid, str):
                all_chunk_ids.add(cid)

    missing = [cid for cid in sorted(all_chunk_ids) if not chunk_exists(target_name, cid)]

    return {
        "target": target_name,
        "has_snapshot": True,
        "unique_chunk_ids": len(all_chunk_ids),
        "missing_chunks": missing,
    }


# ---------------------------------------------------------------------------
# Chunk Location Helpers
# ---------------------------------------------------------------------------


def locate_chunk(target_name: str, chunk_id: str) -> Dict[str, Any]:
    """
    Return filesystem information for a given chunk ID.

    CONTRACT
    --------
    • Read-only
    • No existence guarantees
    • Diagnostic helper only
    """
    path = get_chunk_path(target_name, chunk_id)
    return {
        "target": target_name,
        "chunk_id": chunk_id,
        "path": path,
        "exists": os.path.isfile(path),
    }
