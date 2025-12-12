# thn_cli/syncv2/delta/make_delta.py

"""
CDC Delta Manifest Builder (Hybrid-Standard Edition)
----------------------------------------------------

Stage 2 (Delta Option B):
    Walk source_root → fixed-size chunking → per-chunk storage →
    compare with receiver snapshot → emit delta manifest.

This Hybrid-Standard version provides:
    • Normalized field names matching Sync V2 engine state expectations
    • Deterministic chunk ordering + deterministic manifest assembly
    • POSIX-safe relative paths for all platforms
    • Consistent signature behavior via sign_manifest()
    • Explicit treatment of "no changes" deltas (legal, useful, allowed)

Manifest format (delta form):

    {
        "version": 2,
        "mode": "cdc-delta",
        "target": "<target>",
        "source_root": "<abs source>",
        "file_count": <N>,
        "total_size": <bytes>,
        "entries": [
            {
                "path": "rel/path.txt",
                "op": "write",
                "size": <bytes>,
                "chunks": [ "<chunk_id>", ... ]
            },
            {
                "path": "obsolete.txt",
                "op": "delete"
            },
            ...
        ],
        "signature": "...",
        "signature_type": "ed25519",
        "public_key": "..."
    }

Receiver behavior:
    The Sync Engine merges (old snapshot + delta) into a new snapshot.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Set, Tuple

import thn_cli.syncv2.state as sync_state
from thn_cli.syncv2.keys import sign_manifest

from .store import store_chunk

# ---------------------------------------------------------------------------
# Fixed-size chunk size for Stage 2
# (CDC-true chunking is in chunker.py; this module intentionally
#  uses fixed chunking for predictable early-stage behavior.)
# ---------------------------------------------------------------------------

CHUNK_SIZE = 256 * 1024  # 256 KiB


# ---------------------------------------------------------------------------
# Filesystem scanning
# ---------------------------------------------------------------------------


def _iter_files(source_root: str) -> List[str]:
    """
    Recursively locate all regular files under source_root.
    Returns absolute paths.
    """
    results: List[str] = []
    for root, _, files in os.walk(source_root):
        for name in files:
            full = os.path.join(root, name)
            if os.path.isfile(full):
                results.append(full)
    return results


def _rel_path(source_root: str, full_path: str) -> str:
    """
    Produce a POSIX-style relative path, regardless of OS.
    """
    rel = os.path.relpath(full_path, source_root)
    return rel.replace("\\", "/")


# ---------------------------------------------------------------------------
# Chunking (fixed-size)
# ---------------------------------------------------------------------------


def _chunk_file(full_path: str, target_name: str) -> Tuple[int, List[str]]:
    """
    Chunk a file into fixed-size segments and store each chunk.

    Returns:
        (total_bytes, [chunk_id, ...])
    """
    total_bytes = 0
    chunks: List[str] = []

    with open(full_path, "rb") as f:
        while True:
            data = f.read(CHUNK_SIZE)
            if not data:
                break
            total_bytes += len(data)
            chunk_id = store_chunk(target_name, data)
            chunks.append(chunk_id)

    return total_bytes, chunks


def inspect_file_chunks(full_path: str, target_name: str):
    """
    Debug-only helper: return (chunk_sizes, chunk_ids).
    """
    sizes = []
    ids = []

    with open(full_path, "rb") as f:
        while True:
            block = f.read(CHUNK_SIZE)
            if not block:
                break
            sizes.append(len(block))
            ids.append(store_chunk(target_name, block))

    return sizes, ids


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------


def _snapshot_index(snapshot: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Convert a snapshot manifest into:
        { rel_path: [chunk_ids] }
    """
    entries = snapshot.get("entries", []) or []
    index: Dict[str, List[str]] = {}

    for e in entries:
        path = e.get("path")
        if not path:
            continue
        index[str(path)] = list(e.get("chunks", []) or [])

    return index


# ---------------------------------------------------------------------------
# Delta Manifest Builder
# ---------------------------------------------------------------------------


def build_cdc_delta_manifest(
    *,
    source_root: str,
    target_name: str,
) -> Dict[str, Any]:
    """
    Build a complete CDC-delta manifest for the given target.

    Delta includes:
        • write entries for changed/new files
        • delete entries for files absent in current source_root
    """

    source_root = os.path.abspath(source_root)

    # Receiver snapshot (last applied state)
    prev_snapshot = sync_state.load_last_manifest(target_name)
    prev_index = _snapshot_index(prev_snapshot) if prev_snapshot else {}

    # List all source files
    files = _iter_files(source_root)

    entries: List[Dict[str, Any]] = []
    total_size = 0
    current_paths: Set[str] = set()  # paths present in source_root

    # ---------------------------------------------------------------
    # Phase 1 — Detect new/modified files
    # ---------------------------------------------------------------
    for full in files:
        rel = _rel_path(source_root, full)
        current_paths.add(rel)

        file_size, chunk_ids = _chunk_file(full, target_name)

        prev_chunks = prev_index.get(rel)

        # Unchanged files (same chunk sequence)
        if prev_chunks is not None and prev_chunks == chunk_ids:
            continue

        # File changed or new
        total_size += file_size
        entries.append(
            {
                "path": rel,
                "op": "write",
                "size": file_size,
                "chunks": chunk_ids,
            }
        )

    # ---------------------------------------------------------------
    # Phase 2 — Detect deletions
    # ---------------------------------------------------------------
    if prev_snapshot:
        prev_paths = set(prev_index.keys())
        deleted = prev_paths - current_paths

        for rel in sorted(deleted):
            entries.append({"path": rel, "op": "delete"})

    # ---------------------------------------------------------------
    # Assemble manifest (unsigned first)
    # ---------------------------------------------------------------
    manifest: Dict[str, Any] = {
        "version": 2,
        "mode": "cdc-delta",
        "target": target_name,
        "source_root": source_root,
        "file_count": len(entries),
        "total_size": total_size,
        "entries": entries,
    }

    # Signature attaches: public_key + signature fields
    manifest = sign_manifest(manifest)

    return manifest
