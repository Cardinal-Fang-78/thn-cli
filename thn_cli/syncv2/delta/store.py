"""
Sync V2 CDC Chunk Store (Hybrid-Standard)
----------------------------------------

RESPONSIBILITIES
----------------
This module provides the **authoritative low-level storage backend**
for Sync V2 CDC-delta mode.

It is responsible for:
    • Persisting de-duplicated content-addressed chunks
    • Computing chunk IDs using SHA-256
    • Providing deterministic, sharded on-disk layout
    • Exposing uniform read/write primitives for chunk data

This store is foundational infrastructure used by:
    • CDC delta generation
    • CDC delta apply
    • Chunk inspection and diagnostics
    • Future garbage collection tooling
    • Remote chunk-index synchronization

CONTRACT STATUS
---------------
⚠️ CORE STORAGE LAYER — SEMANTICS LOCKED

Changes to this module may:
    • Break CDC-delta correctness
    • Corrupt stored chunk data
    • Invalidate receiver state
    • Break backward compatibility with existing chunk stores

Any modification MUST preserve:
    • Content-addressed storage (SHA-256)
    • Idempotent writes (never overwrite existing chunks)
    • Deterministic shard layout
    • Stable on-disk paths for existing chunks

NON-GOALS
---------
• This module does NOT perform delta computation
• This module does NOT perform routing
• This module does NOT enforce chunk GC policies
• This module does NOT perform network I/O
• This module does NOT validate higher-level CDC manifests

Higher-level CDC semantics belong to delta planning and apply layers.
"""

from __future__ import annotations

import hashlib
import os

# ---------------------------------------------------------------------------
# Root Resolution
# ---------------------------------------------------------------------------


def _sync_root() -> str:
    """
    Resolve the Sync V2 root directory.

    Default:
        C:\\THN\\sync

    Overridable via:
        Environment variable THN_SYNC_ROOT
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
    Determine the full filesystem path for a chunk.

    A two-character prefix shard is used to avoid large flat directories.

    shard = first two hex characters of chunk_id
    """
    if not chunk_id or len(chunk_id) < 2:
        shard = "xx"  # Defensive fallback; should never occur in practice
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
    Store the given chunk and return its chunk_id (SHA-256 hex).

    CONTRACT
    --------
    • Chunk ID = SHA-256(data)
    • Writes are idempotent
    • Existing chunks are never overwritten
    • Shard directories are created automatically
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
        • CDC-delta apply
        • Diagnostics and inspection tooling
        • Future GC logic
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

    Intended for:
        • Visualizers
        • Remote index tooling
        • Offline inspection
    """
    return _chunk_path(target_name, chunk_id)
