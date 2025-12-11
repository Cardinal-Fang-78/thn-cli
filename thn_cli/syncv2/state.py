"""
Sync V2 Receiver State Management (Hybrid-Standard)
---------------------------------------------------

Each SyncTarget maintains a *receiver-side* snapshot describing the files
that currently exist after the most recent successful APPLY.

Storage:
    <THN_SYNC_ROOT>/state/<target>/manifest.json

Snapshot types:
    • raw-zip applies   → snapshot *not updated* (no structured file info)
    • cdc-delta applies → snapshot updated (entries list)

A snapshot contains:
    {
        "version": 2,
        "mode": "cdc-delta",
        "target": "<name>",
        "source_root": "<sender-path>",
        "entries": [
            { "path": "...", "size": int, ... },
            ...
        ],
        "file_count": int,
        "total_size": int
    }

Only CDC applies modify the receiver snapshot.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Root / Path Helpers
# ---------------------------------------------------------------------------

def _sync_root() -> str:
    """
    Resolve the sync root used for receiver snapshots.
    Allows override via THN_SYNC_ROOT.
    """
    return os.environ.get("THN_SYNC_ROOT", r"C:\THN\sync")


def _target_state_dir(target_name: str) -> str:
    """
    Ensure and return the directory holding per-target state.
    """
    root = os.path.join(_sync_root(), "state", target_name)
    os.makedirs(root, exist_ok=True)
    return root


def _manifest_state_path(target_name: str) -> str:
    """
    Path to the JSON snapshot file.
    """
    return os.path.join(_target_state_dir(target_name), "manifest.json")


# ---------------------------------------------------------------------------
# Load Snapshot
# ---------------------------------------------------------------------------

def load_last_manifest(target_name: str) -> Optional[Dict[str, Any]]:
    """
    Load the last snapshot for this target.
    Returns None if no snapshot exists.
    """
    path = _manifest_state_path(target_name)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corruption or read error: treat as no snapshot
        return None


# ---------------------------------------------------------------------------
# Save Snapshot (CDC-only)
# ---------------------------------------------------------------------------

def save_manifest_snapshot(target_name: str, manifest: Dict[str, Any]) -> None:
    """
    Save a **structured** snapshot representing the receiver's full file state.

    This is ONLY used for CDC-delta mode; raw-zip applies do not alter the
    receiver snapshot.

    Snapshot normalization:
        • Ensure entries is a list
        • Recompute file_count
        • Recompute total_size
    """
    path = _manifest_state_path(target_name)

    # Normalize
    entries = manifest.get("entries") or []
    if not isinstance(entries, list):
        entries = []

    total_size = 0
    for e in entries:
        try:
            total_size += int(e.get("size", 0))
        except Exception:
            pass

    snap = dict(manifest)
    snap["entries"] = entries
    snap["file_count"] = len(entries)
    snap["total_size"] = total_size

    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2)


# ---------------------------------------------------------------------------
# Entry Index Builder
# ---------------------------------------------------------------------------

def _entries_index(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Convert manifest['entries'] into a path → entry dict for easy merging.
    """
    index: Dict[str, Dict[str, Any]] = {}
    entries = manifest.get("entries") or []

    for e in entries:
        path = e.get("path")
        if not isinstance(path, str) or not path:
            continue
        index[path] = dict(e)

    return index


# ---------------------------------------------------------------------------
# Merge Logic for CDC Delta
# ---------------------------------------------------------------------------

def merge_snapshot_with_delta(
    old_snapshot: Optional[Dict[str, Any]],
    delta_manifest: Dict[str, Any],
    target_name: str,
) -> Dict[str, Any]:
    """
    Merge the receiver snapshot (old_snapshot) with changes from a CDC-delta
    manifest to produce a new full receiver snapshot.

    Delta entry semantics:
        op == "write"   → insert/replace entry
        op == "delete"  → remove entry
        missing op      → treated as "write"

    Any unmentioned path is preserved from old_snapshot.
    """

    # Start with old snapshot or an empty index
    if old_snapshot is None:
        base: Dict[str, Dict[str, Any]] = {}
    else:
        base = _entries_index(old_snapshot)

    # Apply delta operations
    delta_entries = delta_manifest.get("entries") or []
    for entry in delta_entries:
        path = entry.get("path")
        if not isinstance(path, str) or not path:
            continue

        op = entry.get("op", "write").lower()

        if op == "write":
            base[path] = dict(entry)
        elif op == "delete":
            base.pop(path, None)
        else:
            # Unknown ops are ignored gracefully
            continue

    # Rebuild final entry list
    final_entries = list(base.values())

    # Build new snapshot manifest
    new_snapshot = {
        "version": 2,
        "mode": "cdc-delta",
        "target": target_name,
        "source_root": delta_manifest.get("source_root"),
        "entries": final_entries,
    }

    return new_snapshot
