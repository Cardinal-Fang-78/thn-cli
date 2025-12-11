# thn_cli/syncv2/delta/chunker.py

"""
CDC Chunker (Hybrid-Standard Edition)
-------------------------------------

Perform content-defined chunking (CDC) using a Gear-style rolling hash.

Goals:
    • Stable and platform-independent chunk boundaries
    • Predictable average chunk size
    • Clear min/avg/max size bounds
    • Deterministic chunk ID generation (SHA-256)
    • Unified, inspection-friendly structure for downstream Sync V2 tools

This implementation supports:
    • chunk_bytes(data)
    • chunk_stream(fileobj)

Each produced chunk is returned as a Chunk dataclass:

    Chunk(
        offset=<absolute offset>,
        length=<bytes>,
        chunk_id=<sha256 hex>,
    )

This Hybrid-Standard version clarifies:
    • Mask calculation for expected boundary rate
    • Boundary rules
    • Deterministic tail behavior
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, BinaryIO


# ---------------------------------------------------------------------------
# Rolling Hash Table (Gear-like)
# ---------------------------------------------------------------------------
# 256-entry table repeated for simplicity and cross-language reproducibility.
# (We do NOT rely on Python's random or platform-specific values.)
_GEAR_TABLE = [
    0x1f3d5b79, 0x2a8e0e5b, 0x3b190f6d, 0x4c2a7b91,
    0x5ddc9e13, 0x6eedf721, 0x712b0c9f, 0x8a1d2b45,
] * 32    # → 256 total entries


# ---------------------------------------------------------------------------
# Chunk Dataclass
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    offset: int
    length: int
    chunk_id: str  # SHA-256 hex string


# ---------------------------------------------------------------------------
# CDC Chunker
# ---------------------------------------------------------------------------

class CDCChunker:
    """
    Content-defined chunker with Hybrid-Standard behavior.

    Parameters:
        min_chunk_size  Minimum allowable chunk length before boundary allowed
        avg_chunk_size  Target mean chunk size (dictates mask)
        max_chunk_size  Hard limit for chunk length
    """

    def __init__(
        self,
        min_chunk_size: int = 4 * 1024,   # 4 KiB
        avg_chunk_size: int = 8 * 1024,   # 8 KiB
        max_chunk_size: int = 64 * 1024,  # 64 KiB
    ) -> None:

        if not (0 < min_chunk_size <= avg_chunk_size <= max_chunk_size):
            raise ValueError(
                "Chunk size bounds must satisfy: 0 < min_chunk_size <= avg_chunk_size <= max_chunk_size"
            )

        self.min_chunk_size = min_chunk_size
        self.avg_chunk_size = avg_chunk_size
        self.max_chunk_size = max_chunk_size

        # Mask for approximate average chunk size:
        # If avg ≈ 2^k, we want ~1 boundary per avg, thus mask=(2^k - 1).
        # bit_length()-1 is the position of the highest bit.
        # Example: avg_chunk_size=8192 → bit_length=14 → mask=(1<<13)-1 = 8191.
        highest_bit_position = avg_chunk_size.bit_length() - 1
        self._mask = (1 << highest_bit_position) - 1

    # -----------------------------------------------------------------------
    # Boundary Logic (internal)
    # -----------------------------------------------------------------------

    def _boundary(self, rolling_hash: int, chunk_len: int) -> bool:
        """
        Determine whether a chunk boundary should be placed.

        Rules:
            • Must be ≥ min_chunk_size
            • Force cut at ≥ max_chunk_size
            • Otherwise: boundary if (rolling_hash & mask) == 0
        """

        if chunk_len < self.min_chunk_size:
            return False

        if chunk_len >= self.max_chunk_size:
            return True

        # Preferred natural boundary
        return (rolling_hash & self._mask) == 0

    # -----------------------------------------------------------------------
    # Chunking: Bytes
    # -----------------------------------------------------------------------

    def chunk_bytes(self, data: bytes, start_offset: int = 0) -> List[Chunk]:
        """
        Chunk a bytes object into content-defined chunks.
        Produces Chunk() records with absolute offsets.
        """

        n = len(data)
        if n == 0:
            return []

        chunks: List[Chunk] = []
        pos = 0
        chunk_start = 0
        rolling_hash = 0

        while pos < n:
            b = data[pos]
            rolling_hash = ((rolling_hash << 1) ^ _GEAR_TABLE[b]) & 0xFFFFFFFF
            pos += 1

            curr_len = pos - chunk_start

            if self._boundary(rolling_hash, curr_len):
                block = data[chunk_start:pos]
                chunk_id = hashlib.sha256(block).hexdigest()

                chunks.append(
                    Chunk(
                        offset=start_offset + chunk_start,
                        length=curr_len,
                        chunk_id=chunk_id,
                    )
                )

                chunk_start = pos
                rolling_hash = 0

        # Final tail chunk
        if chunk_start < n:
            block = data[chunk_start:n]
            chunk_id = hashlib.sha256(block).hexdigest()

            chunks.append(
                Chunk(
                    offset=start_offset + chunk_start,
                    length=n - chunk_start,
                    chunk_id=chunk_id,
                )
            )

        return chunks

    # -----------------------------------------------------------------------
    # Chunking: Stream
    # -----------------------------------------------------------------------

    def chunk_stream(self, f: BinaryIO, start_offset: int = 0) -> List[Chunk]:
        """
        Chunk an entire file-like object (read into memory).
        Hybrid-Standard note:
            Stage 3 will switch to true streaming CDC for large files.
        """
        data = f.read()
        return self.chunk_bytes(data, start_offset=start_offset)
