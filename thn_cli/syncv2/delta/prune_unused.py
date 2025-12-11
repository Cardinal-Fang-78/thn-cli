# thn_cli/syncv2/delta/prune_unused.py

"""
CDC Chunk Store Garbage Collection (Hybrid-Standard)
====================================================

Purpose
-------
Remove unused (unreferenced) chunks from the local chunk store.

A chunk is considered *unused* when:
    • It does NOT appear in the receiver snapshot for the target, AND
    • It is present on disk under THN_SYNC_ROOT/chunks/<target>/...

This module is intentionally conservative:
    • If no snapshot exists for the target, NOTHING is deleted.
    • Deletion only occurs when a chunk is definitely unreferenced.
    • Supports dry-run and detailed reporting.

Public entry points:
    prune_unused_chunks_for_target(target_name, dry_run)
    prune_unused_chunks_all_targets(dry_run)

Directory layout (recap):
    THN_SYNC_ROOT/
        chunks/
            <target>/
                <shard>/         # first two hex chars of chunk_id
                    <chunk_id>   # full SHA256 hex
"""

from __future__ import annotations

import os
from typing import Dict, Any, List

from thn_cli.syncv2 import state as sync_state
from .store import _chunk_root, chunk_exists


# ---------------------------------------------------------------------------
# Internal: gather referenced chunks from snapshot
# ---------------------------------------------------------------------------

def _collect_snapshot_chunk_ids(target_name: str) -> List[str]:
    """
    Return a list of all chunk_ids referenced by the last snapshot
    for the given target.

    If no snapshot exists, return an empty list.
    """
    snap = sync_state.load_last_manifest(target_name)
    if snap is None:
        return []

    refs: set[str] = set()
    for entry in snap.get("entries", []) or []:
        for cid in entry.get("chunks", []) or []:
            if isinstance(cid, str):
                refs.add(cid)
    return list(refs)


# ---------------------------------------------------------------------------
# Internal: scan store for actual chunk files
# ---------------------------------------------------------------------------

def _scan_chunk_store(target_name: str) -> List[str]:
    """
    Return list of chunk_ids present on disk under:
        THN_SYNC_ROOT/chunks/<target>/...

    Result includes only filenames that *look* like valid chunk IDs,
    but we do not validate SHA256 format — file presence is what matters.
    """
    root = _chunk_root(target_name)
    results: List[str] = []

    if not os.path.isdir(root):
        return []

    for shard in os.listdir(root):
        shard_dir = os.path.join(root, shard)
        if not os.path.isdir(shard_dir):
            continue

        for filename in os.listdir(shard_dir):
            full = os.path.join(shard_dir, filename)
            if os.path.isfile(full):
                # Treat the filename as a chunk_id
                results.append(filename)

    return results


# ---------------------------------------------------------------------------
# Main: prune for a single target
# ---------------------------------------------------------------------------

def prune_unused_chunks_for_target(
    target_name: str,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Remove (or plan to remove) unused chunks for a single target.

    Returns:
        {
            "target": <target_name>,
            "snapshot_exists": bool,
            "referenced": [...],
            "present": [...],
            "unused": [...],
            "deleted": [...],        # dry_run=False only
            "dry_run": bool,
        }
    """
    referenced = _collect_snapshot_chunk_ids(target_name)
    present = _scan_chunk_store(target_name)

    snapshot_exists = len(referenced) > 0
    referenced_set = set(referenced)
    present_set = set(present)

    # If no snapshot exists, do NOT delete anything
    if not snapshot_exists:
        return {
            "target": target_name,
            "snapshot_exists": False,
            "referenced": [],
            "present": present,
            "unused": [],
            "deleted": [],
            "dry_run": dry_run,
            "note": "No snapshot exists; pruning is disabled.",
        }

    unused = sorted(present_set - referenced_set)
    deleted: List[str] = []

    if not dry_run:
        for cid in unused:
            # Use the public API to locate the chunk file
            # (but avoid importing load_chunk which expects file existence)
            try:
                # Build path manually via get_chunk_path from store module
                from .store import get_chunk_path
                path = get_chunk_path(target_name, cid)

                if os.path.isfile(path):
                    os.remove(path)
                    deleted.append(cid)
            except Exception:
                # If removal fails, we leave the file and skip
                pass

    return {
        "target": target_name,
        "snapshot_exists": True,
        "referenced": referenced,
        "present": present,
        "unused": unused,
        "deleted": deleted,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Multi-target pruning
# ---------------------------------------------------------------------------

def prune_unused_chunks_all_targets(
    *,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Scan THN_SYNC_ROOT/chunks/<target>/... and prune for each target.

    Returns:
        {
            "dry_run": bool,
            "targets": {
                "<target>": { ... result from prune_unused_chunks_for_target ... },
                ...
            }
        }
    """
    # Discover targets by directory names
    from .store import _sync_root
    root = os.path.join(_sync_root(), "chunks")

    targets: List[str] = []
    if os.path.isdir(root):
        for name in os.listdir(root):
            if os.path.isdir(os.path.join(root, name)):
                targets.append(name)

    results: Dict[str, Any] = {}
    for t in sorted(targets):
        results[t] = prune_unused_chunks_for_target(t, dry_run=dry_run)

    return {
        "dry_run": dry_run,
        "targets": results,
    }
