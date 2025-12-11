# thn_cli/syncv2/delta/inspectors.py

"""
CDC Delta Inspectors (Hybrid-Standard)
======================================

Purpose
-------
This module provides reusable inspection helpers for the Sync V2
CDC-delta pipeline. It is intentionally *read-only* and does not
modify on-disk state.

Capabilities:
    • Compute CDC chunk statistics for a source tree
    • Summarize receiver snapshots (last applied state)
    • Check for missing chunks referenced by a snapshot
    • Locate chunk files on disk for diagnostics

Designed to work with:
    - make_delta.build_cdc_delta_manifest
    - apply_cdc_delta_envelope
    - syncv2.state (snapshot management)
    - syncv2.delta.store (chunk storage)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

from thn_cli.syncv2 import state as sync_state
from .make_delta import _iter_files, _rel_path, inspect_file_chunks
from .store import get_chunk_path, chunk_exists


# ---------------------------------------------------------------------------
# CDC stats for a source tree
# ---------------------------------------------------------------------------

def compute_cdc_stats_for_tree(
    *,
    source_root: str,
    target_name: str,
) -> Dict[str, Any]:
    """
    Compute high-level CDC statistics for all files under source_root.

    Returns a dict:
        {
            "source_root": "<abs-path>",
            "target": "<target_name>",
            "files_scanned": int,
            "total_chunks": int,
            "unique_chunks": int,
            "dedup_hits": int,
            "total_bytes": int,
        }

    Note:
        This uses inspect_file_chunks(), which may cause chunks to be
        stored in the chunk store as a side-effect (for now). It is
        primarily intended for *diagnostics* and *planning*.
    """
    source_root = os.path.abspath(source_root)
    files = _iter_files(source_root)

    total_chunks = 0
    unique_chunk_ids: set[str] = set()
    total_bytes = 0

    for full in files:
        sizes, chunk_ids = inspect_file_chunks(full, target_name=target_name)
        total_chunks += len(chunk_ids)
        unique_chunk_ids.update(chunk_ids)
        total_bytes += sum(sizes)

    dedup_hits = total_chunks - len(unique_chunk_ids)

    return {
        "source_root": source_root,
        "target": target_name,
        "files_scanned": len(files),
        "total_chunks": total_chunks,
        "unique_chunks": len(unique_chunk_ids),
        "dedup_hits": dedup_hits,
        "total_bytes": total_bytes,
    }


# ---------------------------------------------------------------------------
# Snapshot (receiver state) inspection
# ---------------------------------------------------------------------------

def summarize_snapshot(target_name: str) -> Dict[str, Any]:
    """
    Summarize the last applied manifest snapshot for a target.

    Returns a dict:
        {
            "target": "<target_name>",
            "has_snapshot": bool,
            "version": int | None,
            "mode": str | None,
            "entries": int,
            "total_size": int,
            "source_root": str | None,
        }
    """
    snap = sync_state.load_last_manifest(target_name)
    if snap is None:
        return {
            "target": target_name,
            "has_snapshot": False,
            "version": None,
            "mode": None,
            "entries": 0,
            "total_size": 0,
            "source_root": None,
        }

    entries = snap.get("entries", []) or []
    total_size = snap.get("total_size")
    if total_size is None:
        # Fallback: recompute if snapshot was created by older code.
        total_size = 0
        for e in entries:
            try:
                total_size += int(e.get("size", 0))
            except Exception:
                pass

    return {
        "target": target_name,
        "has_snapshot": True,
        "version": snap.get("version"),
        "mode": snap.get("mode"),
        "entries": len(entries),
        "total_size": int(total_size),
        "source_root": snap.get("source_root"),
    }


def snapshot_chunk_health(target_name: str) -> Dict[str, Any]:
    """
    Check whether all chunks referenced by the last snapshot exist
    in the local chunk store.

    Returns:
        {
            "target": "<target_name>",
            "has_snapshot": bool,
            "entries_scanned": int,
            "unique_chunk_ids": int,
            "missing_chunks": [ "<chunk_id>", ... ],
        }
    """
    snap = sync_state.load_last_manifest(target_name)
    if snap is None:
        return {
            "target": target_name,
            "has_snapshot": False,
            "entries_scanned": 0,
            "unique_chunk_ids": 0,
            "missing_chunks": [],
        }

    entries = snap.get("entries", []) or []
    all_chunk_ids: set[str] = set()

    for e in entries:
        for cid in e.get("chunks", []) or []:
            if isinstance(cid, str):
                all_chunk_ids.add(cid)

    missing: List[str] = []
    for cid in sorted(all_chunk_ids):
        if not chunk_exists(target_name, cid):
            missing.append(cid)

    return {
        "target": target_name,
        "has_snapshot": True,
        "entries_scanned": len(entries),
        "unique_chunk_ids": len(all_chunk_ids),
        "missing_chunks": missing,
    }


# ---------------------------------------------------------------------------
# Chunk location helpers
# ---------------------------------------------------------------------------

def locate_chunk(target_name: str, chunk_id: str) -> Dict[str, Any]:
    """
    Return filesystem information for a given chunk ID.

    Result:
        {
            "target": "<target_name>",
            "chunk_id": "<chunk_id>",
            "path": "<full-path>",
            "exists": bool,
        }
    """
    path = get_chunk_path(target_name, chunk_id)
    return {
        "target": target_name,
        "chunk_id": chunk_id,
        "path": path,
        "exists": os.path.isfile(path),
    }
