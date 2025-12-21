from __future__ import annotations

from typing import Dict, List


def present_compare_status(*, has_changes: bool) -> Dict[str, str]:
    if has_changes:
        return {
            "code": "changes_detected",
            "message": "Snapshots differ (changes detected)",
        }
    return {
        "code": "no_change",
        "message": "Snapshots match (no changes detected)",
    }


def present_snapshot_changes(
    *,
    added: List[str],
    removed: List[str],
) -> List[Dict[str, str]]:
    """
    Convert a snapshot-to-snapshot structural comparison into a user-friendly list.

    added   → expected paths that appear in AFTER but not BEFORE
    removed → expected paths that appear in BEFORE but not AFTER
    """
    out: List[Dict[str, str]] = []

    for p in sorted(added):
        out.append(
            {
                "action": "added",
                "location": p,
                "description": "Expected path was added between snapshots",
            }
        )

    for p in sorted(removed):
        out.append(
            {
                "action": "removed",
                "location": p,
                "description": "Expected path was removed between snapshots",
            }
        )

    return out
