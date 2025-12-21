from __future__ import annotations

from typing import Dict, List, Literal, Optional, TypedDict

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

DiffOp = Literal["add", "remove", "modify"]
ImpactLevel = Literal["low", "medium", "high"]


class DiffRecord(TypedDict):
    op: DiffOp
    path: str
    classification: str
    rule: Optional[str]
    impact: ImpactLevel
    reason_code: str
    meta: Dict[str, object]


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------


def build_diff(
    *,
    added: List[str],
    removed: List[str],
    modified: Optional[List[str]] = None,
    rules: Optional[Dict[str, List[str]]] = None,
    origin: Literal["drift", "snapshot"] = "drift",
) -> List[DiffRecord]:
    """
    Build a normalized diff list.

    This function is the single canonical diff builder for:
      - drift detection
      - snapshot comparison
      - explain mode
      - replay / GUI timelines

    `origin` controls classification semantics, not structure.
    """
    diff: List[DiffRecord] = []

    # --- removals ---
    for path in removed:
        diff.append(
            {
                "op": "remove",
                "path": path,
                "classification": _classify_removal(origin),
                "rule": None,
                "impact": "high",
                "reason_code": _reason_code(origin, "remove"),
                "meta": {},
            }
        )

    # --- additions ---
    for path in added:
        diff.append(
            {
                "op": "add",
                "path": path,
                "classification": _classify_addition(origin),
                "rule": None,
                "impact": "medium",
                "reason_code": _reason_code(origin, "add"),
                "meta": {},
            }
        )

    # --- modifications (future-safe, optional) ---
    for path in modified or []:
        diff.append(
            {
                "op": "modify",
                "path": path,
                "classification": "content_changed",
                "rule": None,
                "impact": "medium",
                "reason_code": "CONTENT_CHANGED",
                "meta": {},
            }
        )

    return diff


# ---------------------------------------------------------------------------
# Backward-compatible wrapper (drift callers)
# ---------------------------------------------------------------------------


def build_drift_diff(
    *,
    missing: List[str],
    extra: List[str],
    notes: List[str],
    rules: Dict[str, List[str]] | None,
) -> List[DiffRecord]:
    """
    Backward-compatible wrapper for existing drift code paths.

    Internally maps to build_diff().
    """
    return build_diff(
        added=extra,
        removed=missing,
        modified=[],
        rules=rules,
        origin="drift",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _classify_removal(origin: str) -> str:
    if origin == "snapshot":
        return "snapshot_removed"
    return "required_missing"


def _classify_addition(origin: str) -> str:
    if origin == "snapshot":
        return "snapshot_added"
    return "unexpected_extra"


def _reason_code(origin: str, op: DiffOp) -> str:
    if origin == "snapshot":
        if op == "add":
            return "SNAPSHOT_PATH_ADDED"
        if op == "remove":
            return "SNAPSHOT_PATH_REMOVED"
    else:
        if op == "add":
            return "UNEXPECTED_EXTRA_PATH"
        if op == "remove":
            return "MISSING_REQUIRED_PATH"

    return "UNKNOWN"
