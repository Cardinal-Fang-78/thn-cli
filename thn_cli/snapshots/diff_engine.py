from __future__ import annotations

"""
Snapshot Structural Diff Engine (Hybrid-Standard)
=================================================

RESPONSIBILITIES
----------------
Provide a **deterministic, read-only structural diff** between two
immutable scaffold snapshots.

This module is responsible for:
    • Extracting canonical path sets from snapshot objects
    • Computing added / removed / unchanged paths
    • Producing a stable diff shape required by golden tests
    • Translating snapshot diffs into unified drift-style operations

This engine is used by:
    • snapshot comparison tooling
    • drift history reconstruction
    • replay / migration diagnostics
    • future GUI timeline views

CONTRACT STATUS
---------------
⚠️ SNAPSHOT DIAGNOSTICS — OUTPUT SURFACE STABLE

This module:
    • MUST NOT mutate snapshots
    • MUST NOT touch the filesystem
    • MUST NOT infer intent or policy
    • MUST remain deterministic across runs

The output shapes of:
    • diff_snapshots()
    • diff_to_ops()

are **externally consumed** and must remain backward compatible
unless explicitly versioned.

AUTHORITATIVE BOUNDARIES
------------------------
This module is NOT authoritative for:
    • accepting or rejecting drift
    • applying changes
    • enforcing correctness

Authoritative state transitions occur in:
    • post_make snapshot capture
    • drift accept / migrate flows
    • recovery / replay engines

NON-GOALS
---------
• This module does NOT validate snapshot integrity
• This module does NOT resolve conflicts
• This module does NOT persist history
• This module does NOT interpret semantics
"""

from typing import Dict, List, Set, TypedDict

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class PathItem(TypedDict):
    path: str


class DiffOp(TypedDict):
    op: str  # "add" | "remove"
    path: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_tree(snapshot: Dict) -> Set[str]:
    """
    Extract the canonical path set from a snapshot.

    Snapshots store paths under the `tree` key.
    """
    tree = snapshot.get("tree")
    if isinstance(tree, list):
        return {str(p) for p in tree}
    return set()


# ---------------------------------------------------------------------------
# Snapshot diff
# ---------------------------------------------------------------------------


def diff_snapshots(
    *,
    before: Dict,
    after: Dict,
) -> Dict[str, List[PathItem]]:
    """
    Compute a deterministic structural diff between two snapshots.

    Snapshots are expected to contain:
      - tree: List[str]

    Returns (stable legacy shape required by golden tests):
      {
          "added":     [{ "path": str }],
          "removed":   [{ "path": str }],
          "unchanged": [{ "path": str }],
      }
    """
    before_paths = _extract_tree(before)
    after_paths = _extract_tree(after)

    added = sorted(after_paths - before_paths)
    removed = sorted(before_paths - after_paths)
    unchanged = sorted(before_paths & after_paths)

    return {
        "added": [{"path": p} for p in added],
        "removed": [{"path": p} for p in removed],
        "unchanged": [{"path": p} for p in unchanged],
    }


# ---------------------------------------------------------------------------
# Diff → unified ops
# ---------------------------------------------------------------------------


def diff_to_ops(raw_diff: Dict[str, List[Dict[str, str]]]) -> List[DiffOp]:
    """
    Convert the snapshot diff shape into unified drift-compatible ops:

        [{"op": "add"|"remove", "path": "..."}]

    Ordering is deterministic:
      - all adds first (sorted)
      - then all removes (sorted)
    """
    added = raw_diff.get("added") or []
    removed = raw_diff.get("removed") or []

    ops: List[DiffOp] = []

    add_paths = sorted(
        str(item.get("path", ""))
        for item in added
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    )

    rem_paths = sorted(
        str(item.get("path", ""))
        for item in removed
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    )

    for p in add_paths:
        if p:
            ops.append({"op": "add", "path": p})

    for p in rem_paths:
        if p:
            ops.append({"op": "remove", "path": p})

    return ops


def diff_snapshots_ops(
    *,
    before: Dict,
    after: Dict,
) -> List[DiffOp]:
    """
    Convenience wrapper that returns unified ops directly from two snapshots.
    """
    return diff_to_ops(diff_snapshots(before=before, after=after))
