from __future__ import annotations

from fnmatch import fnmatch
from typing import Dict, List, Literal, Optional, TypedDict

from thn_cli.post_make.diff_builder import DiffRecord, build_diff

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

DriftStatus = Literal["clean", "drifted"]


class DriftNote(TypedDict):
    code: str
    path: str
    message: str


class DriftClassification(TypedDict):
    status: DriftStatus
    missing: List[str]
    extra: List[str]
    notes: List[DriftNote]
    diff: List[DiffRecord]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _matches_any(path: str, patterns: List[str]) -> bool:
    return any(fnmatch(path, pat) for pat in patterns)


# ---------------------------------------------------------------------------
# Core classifier
# ---------------------------------------------------------------------------


def classify_drift(
    *,
    expected: List[str],
    missing: List[str],
    extra: List[str],
    rules: Optional[Dict[str, List[str]]] = None,
) -> DriftClassification:
    """
    Classify raw drift results using explicit rules.

    This function:
      - applies ignore / allow_children rules
      - emits structured notes
      - builds a canonical diff via diff_builder

    Output is suitable for:
      - CLI inspect
      - explain mode
      - snapshot replay
      - GUI timelines
    """
    rules = rules or {}

    allow_children = rules.get("allow_children", [])
    ignore = rules.get("ignore", [])

    filtered_missing: List[str] = []
    filtered_extra: List[str] = []
    notes: List[DriftNote] = []

    # ------------------------------------------------------------------
    # Missing paths
    # ------------------------------------------------------------------

    for path in missing:
        if _matches_any(path, ignore):
            notes.append(
                {
                    "code": "IGNORED_PATH",
                    "path": path,
                    "message": f"{path} ignored by rules",
                }
            )
            continue

        filtered_missing.append(path)
        notes.append(
            {
                "code": "MISSING_EXPECTED",
                "path": path,
                "message": f"{path} expected but missing",
            }
        )

    # ------------------------------------------------------------------
    # Extra paths
    # ------------------------------------------------------------------

    for path in extra:
        if _matches_any(path, ignore):
            notes.append(
                {
                    "code": "IGNORED_PATH",
                    "path": path,
                    "message": f"{path} ignored by rules",
                }
            )
            continue

        if _matches_any(path, allow_children):
            notes.append(
                {
                    "code": "OWNED_SUB_SCAFFOLD",
                    "path": path,
                    "message": f"{path} classified as owned sub-scaffold",
                }
            )
            continue

        filtered_extra.append(path)
        notes.append(
            {
                "code": "UNEXPECTED_EXTRA",
                "path": path,
                "message": f"{path} is an unexpected extra path",
            }
        )

    # ------------------------------------------------------------------
    # Status + diff
    # ------------------------------------------------------------------

    status: DriftStatus = "clean"
    if filtered_missing or filtered_extra:
        status = "drifted"

    diff = build_diff(
        added=filtered_extra,
        removed=filtered_missing,
        modified=[],
        rules=rules,
        origin="drift",
    )

    return {
        "status": status,
        "missing": filtered_missing,
        "extra": filtered_extra,
        "notes": notes,
        "diff": diff,
    }
