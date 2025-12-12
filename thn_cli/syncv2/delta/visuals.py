# thn_cli/syncv2/delta/visuals.py
"""
THN Sync V2 – Visual Diagnostics Helpers (Hybrid-Standard)
==========================================================

Purpose
-------
This module provides purely cosmetic, human-readable diagnostic helpers for:
    • printing CDC-delta manifests in compact or expanded form
    • visualizing chunk boundaries
    • summarizing per-file changes
    • generating normalized inspection text for logs/UI

No file I/O, routing, or apply logic occurs here.
All data is returned as strings for callers to print or include in UI output.

Dependencies
------------
This module intentionally depends only on the manifest structure and
chunk IDs; it never touches chunk storage or filesystem operations.
"""

from __future__ import annotations

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Manifest summarization (pretty formatted)
# ---------------------------------------------------------------------------


def format_manifest_summary(manifest: Dict[str, Any]) -> str:
    """
    Return a readable, multi-line summary of a manifest.

    Works for both:
        • raw-zip manifests (file_count / total_size)
        • cdc-delta manifests (entries list)
    """
    mode = manifest.get("mode", "raw-zip")
    version = manifest.get("version")
    file_count = manifest.get("file_count", 0)
    total_size = manifest.get("total_size", 0)
    target = manifest.get("target", "?")

    lines = [
        f"Manifest Summary:",
        f"  Version     : {version}",
        f"  Mode        : {mode}",
        f"  Target      : {target}",
        f"  File Count  : {file_count}",
        f"  Total Size  : {total_size} bytes",
    ]

    if mode == "cdc-delta":
        entries = manifest.get("entries", []) or []
        writes = sum(1 for e in entries if e.get("op") == "write")
        deletes = sum(1 for e in entries if e.get("op") == "delete")
        lines.append(f"  Writes      : {writes}")
        lines.append(f"  Deletes     : {deletes}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Per-file detail formatting
# ---------------------------------------------------------------------------


def format_entry_detail(entry: Dict[str, Any]) -> str:
    """
    Return a detailed multi-line description of a single delta entry.
    """
    path = entry.get("path", "?")
    op = entry.get("op", "write")
    size = entry.get("size")
    chunks = entry.get("chunks", []) or []

    lines = [
        f"Entry:",
        f"  Path   : {path}",
        f"  Op     : {op}",
    ]

    if op == "write":
        lines.append(f"  Size   : {size}")
        lines.append(f"  Chunks : {len(chunks)}")
        for idx, cid in enumerate(chunks):
            lines.append(f"      [{idx:02d}] {cid}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Chunk boundary visualization
# ---------------------------------------------------------------------------


def format_chunk_boundaries(
    *,
    rel_path: str,
    chunk_sizes: List[int],
    chunk_ids: List[str],
) -> str:
    """
    Produce a human-friendly display of how a file was chunked.

    Example output:
        file.txt:
          Chunk 0: 8192 bytes  sha256:abcd...
          Chunk 1: 4096 bytes  sha256:ef01...
    """
    lines = [f"Chunk Boundaries for: {rel_path}", ""]

    for i, (sz, cid) in enumerate(zip(chunk_sizes, chunk_ids)):
        lines.append(f"  Chunk {i:02d}: {sz} bytes  {cid}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Delta-style directory summary
# ---------------------------------------------------------------------------


def format_delta_directory_view(entries: List[Dict[str, Any]]) -> str:
    """
    Produce a compact directory-tree-like display of delta changes.
    """
    lines = ["Delta Directory View:", ""]

    for e in entries:
        op = e.get("op", "write")
        path = e.get("path")

        if op == "delete":
            lines.append(f"  [DEL] {path}")
        else:
            size = e.get("size", 0)
            chunks = e.get("chunks", [])
            lines.append(f"  [WR ] {path}  ({size} bytes, {len(chunks)} chunks)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full delta pretty-printer
# ---------------------------------------------------------------------------


def format_full_delta(manifest: Dict[str, Any]) -> str:
    """
    Pretty-print the entire delta manifest.
    """
    mode = manifest.get("mode")
    if mode != "cdc-delta":
        return "Not a CDC-delta manifest."

    entries = manifest.get("entries", []) or []

    out = [format_manifest_summary(manifest), "", "Entries:"]
    for e in entries:
        out.append("")
        out.append(format_entry_detail(e))

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Compatibility Stubs – required by commands_sync_delta
# ---------------------------------------------------------------------------


def visualize_manifest_full(manifest: dict) -> dict:
    """
    Placeholder for full-manifest visualization.
    Tests only require the symbol to exist.
    """
    return {
        "status": "not_implemented",
        "type": "manifest_full",
        "input_summary": str(type(manifest)),
    }


def visualize_chunk_map(chunk_map: dict) -> dict:
    """
    Placeholder for visualizing chunk distribution.
    """
    return {
        "status": "not_implemented",
        "type": "chunk_map",
        "chunks": len(chunk_map) if hasattr(chunk_map, "__len__") else None,
    }


def visualize_snapshot_diff(diff: dict) -> dict:
    """
    Placeholder for snapshot diff visualization.
    """
    return {
        "status": "not_implemented",
        "type": "snapshot_diff",
        "diff_summary": str(type(diff)),
    }
