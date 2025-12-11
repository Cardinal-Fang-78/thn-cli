# thn_cli/syncv2/delta/filters.py
"""
THN Sync V2 – Delta Filters (Hybrid-Standard)
============================================

Purpose
-------
This module provides *non-destructive*, purely functional filtering helpers
for CDC-delta manifests and their entries.

These filters serve purposes such as:
    • reducing a delta manifest to only certain directories or file patterns
    • excluding binary assets during dry-run inspections
    • partitioning write/delete operations for debugging
    • selecting only changed files larger/smaller than thresholds
    • safely manipulating complex manifests without mutating originals

All functions return *new structures* and never modify inputs.

No filesystem I/O. No chunk store I/O. No routing.
"""

from __future__ import annotations

from typing import Dict, Any, List, Callable, Optional


# ---------------------------------------------------------------------------
# Core filter utilities
# ---------------------------------------------------------------------------

def filter_entries(
    *,
    entries: List[Dict[str, Any]],
    predicate: Callable[[Dict[str, Any]], bool],
) -> List[Dict[str, Any]]:
    """
    Return a NEW list of entries for which predicate(entry) is True.

    This function forms the foundation for all other specialized filters.
    """
    return [e for e in entries if predicate(e)]


def filter_manifest_entries(
    manifest: Dict[str, Any],
    predicate: Callable[[Dict[str, Any]], bool],
) -> Dict[str, Any]:
    """
    Return a NEW manifest with its entries filtered by predicate().

    Only applies to CDC-delta manifests (mode="cdc-delta").
    Raw-zip manifests are returned unchanged.
    """
    if manifest.get("mode") != "cdc-delta":
        return dict(manifest)

    new_entries = filter_entries(
        entries=manifest.get("entries", []) or [],
        predicate=predicate,
    )

    new_manifest = dict(manifest)
    new_manifest["entries"] = new_entries
    new_manifest["file_count"] = len(new_entries)
    new_manifest["total_size"] = sum(int(e.get("size", 0)) for e in new_entries)

    return new_manifest


# ---------------------------------------------------------------------------
# Common predicates
# ---------------------------------------------------------------------------

def only_writes(entry: Dict[str, Any]) -> bool:
    return entry.get("op") == "write"


def only_deletes(entry: Dict[str, Any]) -> bool:
    return entry.get("op") == "delete"


def by_extension(*exts: str) -> Callable[[Dict[str, Any]], bool]:
    """
    Keep only entries whose path ends with one of the provided extensions.
    Extensions are matched case-insensitively.

    Example:
        filter_entries(entries=my_entries, predicate=by_extension(".txt", ".md"))
    """
    exts = tuple(ext.lower() for ext in exts)

    def _p(e: Dict[str, Any]) -> bool:
        path = e.get("path", "").lower()
        return any(path.endswith(x) for x in exts)

    return _p


def by_prefix(prefix: str) -> Callable[[Dict[str, Any]], bool]:
    """
    Keep only entries whose path begins with prefix.
    """
    def _p(e: Dict[str, Any]) -> bool:
        return e.get("path", "").startswith(prefix)
    return _p


def by_min_size(min_bytes: int) -> Callable[[Dict[str, Any]], bool]:
    """
    Keep only entries whose size >= min_bytes.
    Applies only to write entries (delete entries have no size).
    """
    def _p(e: Dict[str, Any]) -> bool:
        if e.get("op") != "write":
            return False
        try:
            return int(e.get("size", 0)) >= min_bytes
        except Exception:
            return False
    return _p


def by_max_size(max_bytes: int) -> Callable[[Dict[str, Any]], bool]:
    """
    Keep only entries whose size <= max_bytes.
    """
    def _p(e: Dict[str, Any]) -> bool:
        if e.get("op") != "write":
            return False
        try:
            return int(e.get("size", 0)) <= max_bytes
        except Exception:
            return False
    return _p


def by_chunk_count(min_chunks: Optional[int] = None, max_chunks: Optional[int] = None):
    """
    Keep only write entries whose chunk count is within provided bounds.

    Example:
        predicate = by_chunk_count(min_chunks=2)
    """
    def _p(e: Dict[str, Any]) -> bool:
        if e.get("op") != "write":
            return False
        chunks = e.get("chunks", []) or []
        n = len(chunks)
        if min_chunks is not None and n < min_chunks:
            return False
        if max_chunks is not None and n > max_chunks:
            return False
        return True
    return _p


# ---------------------------------------------------------------------------
# Composite helpers
# ---------------------------------------------------------------------------

def keep_only_writes(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a new manifest containing only write operations.
    """
    return filter_manifest_entries(manifest, only_writes)


def keep_only_deletes(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a new manifest containing only delete operations.
    """
    return filter_manifest_entries(manifest, only_deletes)


def keep_only_paths_with_prefix(manifest: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    return filter_manifest_entries(manifest, by_prefix(prefix))


def keep_only_matching_extensions(manifest: Dict[str, Any], *exts: str) -> Dict[str, Any]:
    return filter_manifest_entries(manifest, by_extension(*exts))


def keep_only_large_files(manifest: Dict[str, Any], min_size: int) -> Dict[str, Any]:
    return filter_manifest_entries(manifest, by_min_size(min_size))


def keep_only_small_files(manifest: Dict[str, Any], max_size: int) -> Dict[str, Any]:
    return filter_manifest_entries(manifest, by_max_size(max_size))


# ---------------------------------------------------------------------------
# Set operations (without mutating original manifests)
# ---------------------------------------------------------------------------

def intersect_entries(
    a: List[Dict[str, Any]],
    b: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute intersection by path.
    Entries with the same path in both lists are returned from list A.
    """
    b_paths = {e.get("path") for e in b}
    return [e for e in a if e.get("path") in b_paths]


def subtract_entries(
    a: List[Dict[str, Any]],
    b: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute A - B by path.
    Returns entries from A whose paths do not appear in B.
    """
    b_paths = {e.get("path") for e in b}
    return [e for e in a if e.get("path") not in b_paths]
