from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set


def _norm_path(p: str) -> str:
    return p.replace("\\", "/").strip().lstrip("./").strip("/")


def _as_path_set(values: Iterable[Any]) -> Set[str]:
    out: Set[str] = set()
    for v in values or []:
        if isinstance(v, str):
            out.add(_norm_path(v))
    return out


def compute_replay_tree(
    *,
    snapshot: Dict[str, Any],  # kept for signature stability; no longer authoritative
    diff: Dict[str, Any],
) -> List[str]:
    """
    Deterministically compute the replayed tree from a snapshot diff.

    Replay definition (authoritative):
      - unchanged paths are preserved
      - added paths are included
      - removed paths are excluded implicitly
      - snapshot tree is NOT used as a base

    Output:
      Sorted unique normalized relative paths.
    """
    unchanged = _as_path_set(
        item.get("path") for item in diff.get("unchanged", []) or [] if isinstance(item, dict)
    )

    added = _as_path_set(
        item.get("path") for item in diff.get("added", []) or [] if isinstance(item, dict)
    )

    # Removed paths are intentionally ignored here; unchanged is authoritative
    out = unchanged | added
    return sorted(out)
