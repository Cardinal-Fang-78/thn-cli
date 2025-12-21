from __future__ import annotations

"""
Post-Make Snapshot Engine (Hybrid-Standard)
===========================================

RESPONSIBILITIES
----------------
This module defines the **authoritative snapshot mechanism** used after
make, accept, and migrate operations to capture the expected filesystem
state of a scaffold.

It is responsible for:
    • Enumerating actual filesystem paths under a scaffold
    • Applying blueprint-defined allow/ignore rules
    • Producing deterministic expected_paths lists
    • Writing immutable, timestamped snapshot files
    • Supporting recovery, drift detection, and audit workflows

Snapshots written by this module are consumed by:
    • drift preview / explain
    • drift accept
    • migrate
    • recovery and inspection tooling
    • future GUI audit views

CONTRACT STATUS
---------------
⚠️ AUTHORITATIVE SNAPSHOT SEMANTICS — LOCKED

Behavioral guarantees:
    • Snapshot contents are deterministic for a given filesystem state
    • expected_paths ordering is stable and sorted
    • Snapshots are immutable once written
    • Snapshot IDs are time-based and collision-resistant
    • Manifest rules are applied conservatively

Any change to:
    • path normalization
    • rule application logic
    • snapshot JSON shape
    • naming conventions

MUST be accompanied by:
    • drift / migration review
    • golden test updates
    • explicit contract acknowledgement

NON-GOALS
---------
• This module does NOT modify filesystem state
• This module does NOT validate manifests
• This module does NOT classify drift
• This module does NOT enforce policy decisions

Drift semantics live in scaffolds/.
Policy enforcement lives in post_make/.
"""

import json
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

MANIFEST_NAME = ".thn-tree.json"
SNAPSHOT_DIR_NAME = ".thn-snapshots"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def norm_rel(p: str) -> str:
    """
    Normalize a relative path to a stable, forward-slash form.
    """
    p = p.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.strip("/")


def walk_rel_paths(root: Path) -> Set[str]:
    """
    Walk a scaffold root and return all file and directory paths
    relative to root, excluding the manifest itself.
    """
    rels: Set[str] = set()
    for item in root.rglob("*"):
        if item.name == MANIFEST_NAME:
            continue
        try:
            rel = item.relative_to(root).as_posix()
        except Exception:
            continue
        rels.add(norm_rel(rel))
    return rels


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------


def _as_list_of_str(val) -> List[str]:
    if not isinstance(val, list):
        return []
    return [norm_rel(x) for x in val if isinstance(x, str)]


def extract_rules(manifest_rules) -> Dict[str, List[str]]:
    """
    Normalize manifest rules (schema v2+) into a stable structure:
        {
            "allow_children": [...],
            "ignore": [...]
        }
    """
    if not isinstance(manifest_rules, dict):
        return {}

    out: Dict[str, List[str]] = {}

    allow_children = _as_list_of_str(manifest_rules.get("allow_children"))
    ignore = _as_list_of_str(manifest_rules.get("ignore"))

    if allow_children:
        out["allow_children"] = allow_children
    if ignore:
        out["ignore"] = ignore

    return out


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    """
    Return True if path matches any glob pattern in patterns.
    """
    for pat in patterns:
        if pat and fnmatch(path, pat):
            return True
    return False


def compute_allowed_child_roots(
    actual_paths: Set[str],
    allow_children_patterns: Iterable[str],
) -> Set[str]:
    """
    Identify root paths that are explicitly allowed to have children.
    """
    patterns = [norm_rel(p) for p in allow_children_patterns if isinstance(p, str)]
    child_roots: Set[str] = set()

    for p in actual_paths:
        if matches_any(p, patterns):
            child_roots.add(p)

    return child_roots


def is_within_any_child(path: str, child_roots: Set[str]) -> bool:
    """
    Return True if path is equal to or nested under any child root.
    """
    for root in child_roots:
        if path == root:
            return True
        if root and path.startswith(root + "/"):
            return True
    return False


# ---------------------------------------------------------------------------
# Snapshot core
# ---------------------------------------------------------------------------


def snapshot_expected_paths(
    *,
    root: Path,
    rules: Optional[Dict[str, List[str]]] = None,
) -> List[str]:
    """
    Produce a deterministic expected_paths snapshot for a scaffold.

    Applies ignore rules first, then child-root exclusions.
    """
    actual = walk_rel_paths(root)

    allow_children = (rules or {}).get("allow_children", [])
    ignore = (rules or {}).get("ignore", [])

    child_roots = compute_allowed_child_roots(actual, allow_children)

    kept: List[str] = []
    for p in actual:
        if ignore and matches_any(p, ignore):
            continue
        if child_roots and is_within_any_child(p, child_roots):
            continue
        kept.append(p)

    return sorted(set(kept))


def write_snapshot(
    *,
    root: Path,
    expected_paths: List[str],
    snapshot_type: str,
    note: Optional[str],
    blueprint: Dict[str, str],
) -> Path:
    """
    Write an immutable snapshot with rich metadata to disk.

    Snapshots are written under:
        <scaffold>/.thn-snapshots/<timestamp>.json
    """
    snap_dir = root / SNAPSHOT_DIR_NAME
    snap_dir.mkdir(exist_ok=True)

    created_at = _utc_now_iso()
    snap_id = created_at.replace(":", "_")

    payload = {
        "snapshot": {
            "id": snap_id,
            "type": snapshot_type,
            "created_at": created_at,
            "blueprint": {
                "id": blueprint.get("id"),
                "version": blueprint.get("version"),
            },
        },
        "expected_paths": expected_paths,
    }

    if note:
        payload["snapshot"]["note"] = note

    path = snap_dir / f"{snap_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return path
