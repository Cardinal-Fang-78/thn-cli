# thn_cli/syncv2/delta/gc.py
"""
THN Sync V2 – Chunk Garbage Collection (Hybrid-Standard)
=======================================================

Purpose
-------
This module provides *local* garbage-collection helpers for the CDC-delta
chunk store.

Responsibilities:
    • Discover all chunk IDs on disk for a given target.
    • Discover all chunk IDs currently referenced by the latest snapshot
      for that target.
    • Compute which chunks are unused (on disk but not referenced).
    • Optionally delete unused chunks (with dry-run support).

Design constraints:
    • No network access.
    • No remote negotiation.
    • No mutations without explicit calls to delete/gc functions.
    • All public APIs return structured dicts for CLI/UI consumption.

Layout reminder (shared with store.py):

    THN_SYNC_ROOT (env or C:\\THN\\sync)
      chunks/
        <target_name>/
          <first2hex>/
            <chunk_id>

Snapshot source:
    thn_cli.syncv2.state.load_last_manifest(target_name)

The snapshot manifest uses:
    {
        "entries": [
            {
                "path": "...",
                "size": ...,
                "chunks": ["<chunk_id>", ...],
                ...
            },
            ...
        ],
        ...
    }
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Set

from thn_cli.syncv2.delta.store import get_chunk_path
import thn_cli.syncv2.state as sync_state


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sync_root() -> str:
    """
    Resolve the root path for THN sync data.
    """
    return os.environ.get("THN_SYNC_ROOT", r"C:\THN\sync")


def _chunks_root_for_target(target_name: str) -> str:
    """
    Root directory containing all chunks for the given target.
    """
    return os.path.join(_sync_root(), "chunks", target_name)


def list_chunks_on_disk(target_name: str) -> List[str]:
    """
    Walk the chunk store on disk and return a list of *chunk IDs* discovered
    for the given target.

    This inspects:
        THN_SYNC_ROOT/chunks/<target_name>/**

    and returns the filenames (chunk IDs), not absolute paths.
    """
    root = _chunks_root_for_target(target_name)
    if not os.path.isdir(root):
        return []

    ids: List[str] = []
    for dirpath, _, files in os.walk(root):
        for name in files:
            # leaf filename = chunk_id
            ids.append(name)
    return ids


def referenced_chunks_from_snapshot(target_name: str) -> List[str]:
    """
    Inspect the latest manifest snapshot for target_name and collect all
    chunk IDs referenced by entries.

    If no snapshot exists, returns an empty list.
    """
    snapshot = sync_state.load_last_manifest(target_name)
    if not snapshot:
        return []

    entries = snapshot.get("entries", []) or []
    result: List[str] = []

    for e in entries:
        chunks = e.get("chunks", []) or []
        for cid in chunks:
            if isinstance(cid, str):
                result.append(cid)

    return result


# ---------------------------------------------------------------------------
# Public GC helpers
# ---------------------------------------------------------------------------

def compute_unused_chunks(target_name: str) -> Dict[str, Any]:
    """
    Compute which chunks are currently unused for a given target.

    Returns a dict:
        {
            "target": "<target_name>",
            "all_on_disk": [chunk_id, ...],
            "referenced": [chunk_id, ...],
            "unused": [chunk_id, ...],
            "stats": {
                "total_on_disk": int,
                "total_referenced": int,
                "total_unused": int,
            },
        }
    """
    all_ids = list_chunks_on_disk(target_name)
    ref_ids = referenced_chunks_from_snapshot(target_name)

    all_set: Set[str] = set(all_ids)
    ref_set: Set[str] = set(ref_ids)
    unused_set = all_set - ref_set

    unused_sorted = sorted(unused_set)

    return {
        "target": target_name,
        "all_on_disk": sorted(all_set),
        "referenced": sorted(ref_set),
        "unused": unused_sorted,
        "stats": {
            "total_on_disk": len(all_set),
            "total_referenced": len(ref_set),
            "total_unused": len(unused_set),
        },
    }


def delete_chunks(
    target_name: str,
    chunk_ids: List[str],
    *,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Delete a specific list of chunk IDs for the given target.

    When dry_run=True:
        • No files are removed.
        • The function returns what *would* be removed.

    Returns:
        {
            "target": "<target_name>",
            "dry_run": bool,
            "requested_ids": [...],
            "deleted_ids": [...],
            "missing_ids": [...],
        }
    """
    deleted: List[str] = []
    missing: List[str] = []

    for cid in chunk_ids:
        path = get_chunk_path(target_name, cid)
        if not os.path.isfile(path):
            missing.append(cid)
            continue

        if dry_run:
            deleted.append(cid)
            continue

        try:
            os.remove(path)
            deleted.append(cid)
        except Exception:
            # If deletion fails, treat it as "missing" for reporting.
            missing.append(cid)

    return {
        "target": target_name,
        "dry_run": dry_run,
        "requested_ids": list(chunk_ids),
        "deleted_ids": deleted,
        "missing_ids": missing,
    }


def gc_unused_chunks(
    target_name: str,
    *,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    High-level garbage-collection helper for a single target.

    Steps:
        1. Compute unused chunks vs current snapshot.
        2. Delete (or simulate deletion of) unused chunks.

    Returns:
        {
            "target": "<target_name>",
            "dry_run": bool,
            "stats_before": {...},
            "delete_result": {... from delete_chunks(...)},
        }
    """
    info = compute_unused_chunks(target_name)
    unused_ids = info["unused"]

    delete_result = delete_chunks(
        target_name,
        unused_ids,
        dry_run=dry_run,
    )

    return {
        "target": target_name,
        "dry_run": dry_run,
        "stats_before": info["stats"],
        "delete_result": delete_result,
    }
