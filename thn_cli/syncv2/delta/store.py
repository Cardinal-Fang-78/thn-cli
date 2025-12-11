# thn_cli/syncv2/delta/store.py

"""
Chunk Store (Hybrid-Standard)
=============================

Authoritative low-level storage backend for Sync V2 CDC-delta mode.

Responsibilities:
    • Persist de-duplicated variable/fixed-size chunks
    • Expose uniform read/write primitives
    • Provide deterministic sharded directory layout
    • Act as foundational infrastructure for:
          - delta generation (make_delta)
          - delta apply (apply.py)
          - chunk GC (gc.py)
          - index inspection tools (inspectors.py, visuals.py)
          - remote chunk-index synchronization (remote_chunk_index.py)

Layout
------

THN_SYNC_ROOT/
    chunks/
        <target_name>/
            <shard>/             # 2-hex prefix, e.g. "af/"
                <chunk_id>       # full SHA-256 hex

Where:
    chunk_id = SHA-256(data).hex()
    shard    = chunk_id[0:2] or "xx" if malformed (should never occur)

All chunk operations are idempotent: storing an existing chunk never overwrites.
"""

from __future__ import annotations

import os
import hashlib
from typing import Optional


# ---------------------------------------------------------------------------
# Root Resolution
# ---------------------------------------------------------------------------

def _sync_root() -> str:
    """
    Resolve the Sync V2 root.

    Default:
        C:\\THN\\sync

    Overridable:
        Environment variable THN_SYNC_ROOT.
    """
    return os.environ.get("THN_SYNC_ROOT", r"C:\THN\sync")


def _chunk_root(target_name: str) -> str:
    """
    Base directory under which target-specific chunk namespaces live.

    Example:
        C:\\THN\\sync\\chunks\\web
        C:\\THN\\sync\\chunks\\cli
        C:\\THN\\sync\\chunks\\docs
    """
    return os.path.join(_sync_root(), "chunks", target_name)


# ---------------------------------------------------------------------------
# Sharded Chunk Path Resolution
# ---------------------------------------------------------------------------

def _chunk_path(target_name: str, chunk_id: str) -> str:
    """
    Determine the full path for a chunk based on its SHA-256 ID.

    A two-character prefix shard is used to avoid large flat directories.
    """
    if not chunk_id or len(chunk_id) < 2:
        shard = "xx"  # extremely rare; fallback for malformed IDs
    else:
        shard = chunk_id[:2]

    root = _chunk_root(target_name)
    shard_dir = os.path.join(root, shard)
    return os.path.join(shard_dir, chunk_id)


# ---------------------------------------------------------------------------
# Store Operations
# ---------------------------------------------------------------------------

def store_chunk(target_name: str, data: bytes) -> str:
    """
    Store the given chunk and return its chunk_id (hex SHA-256).

    Behavior:
        • Computes SHA-256(data)
        • Creates shard directory if needed
        • Writes file unless already present (dedup friendly)
    """
    h = hashlib.sha256()
    h.update(data)
    chunk_id = h.hexdigest()

    path = _chunk_path(target_name, chunk_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Deduplicated write — never overwrite
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(data)

    return chunk_id


def chunk_exists(target_name: str, chunk_id: str) -> bool:
    """
    Return True if a chunk with the given ID exists.
    """
    path = _chunk_path(target_name, chunk_id)
    return os.path.isfile(path)


def load_chunk(target_name: str, chunk_id: str) -> bytes:
    """
    Load a chunk’s raw bytes.

    Raises:
        FileNotFoundError if the chunk does not exist.

    Used by:
        • apply_cdc_delta_envelope()
        • inspectors
        • future GC logic
    """
    path = _chunk_path(target_name, chunk_id)

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Missing chunk {chunk_id!r} for target {target_name!r} at {path!r}"
        )

    with open(path, "rb") as f:
        return f.read()


def get_chunk_path(target_name: str, chunk_id: str) -> str:
    """
    Return the absolute filesystem location of a chunk.

    Useful for:
        • Visualizers
        • Remote-index tools
        • Offline inspection
    """
    return _chunk_path(target_name, chunk_id)
