"""
GUI Unified History – Pagination & Ordering Contract Test
---------------------------------------------------------

Purpose:
    Lock pagination and ordering guarantees for GUI consumers
    without enforcing irreversible ordering direction.

Scope:
    • Direct API usage (no CLI)
    • Read-only
    • Presentation contract only
"""

from __future__ import annotations

from typing import Any, Dict, List

from thn_cli.ui.history_api import get_unified_history


def _extract_entries(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    history = result.get("history", {})
    entries = history.get("entries", [])
    assert isinstance(entries, list)
    return entries


def test_gui_history_default_ordering_is_stable() -> None:
    """
    Ordering must be stable across calls with identical inputs.
    Direction is not asserted (future-safe).
    """

    result_1 = get_unified_history(limit=10)
    result_2 = get_unified_history(limit=10)

    entries_1 = _extract_entries(result_1)
    entries_2 = _extract_entries(result_2)

    assert entries_1 == entries_2


def test_gui_history_pagination_respects_limit() -> None:
    """
    Pagination must respect the requested limit
    after ordering has been applied.
    """

    limit = 5
    result = get_unified_history(limit=limit)

    entries = _extract_entries(result)
    assert len(entries) <= limit


def test_gui_history_ordering_uses_observed_at_when_present() -> None:
    """
    If observed_at timestamps are present, ordering must
    be consistent with a single deterministic key.
    This test does NOT assert direction.
    """

    result = get_unified_history(limit=20)
    entries = _extract_entries(result)

    timestamps = [
        e.get("observed_at") for e in entries if isinstance(e, dict) and "observed_at" in e
    ]

    # If timestamps exist, ordering must be deterministic
    if timestamps:
        assert timestamps == sorted(timestamps) or timestamps == sorted(timestamps, reverse=True)


def test_gui_history_does_not_invent_pagination_fields() -> None:
    """
    GUI API must not invent cursor, offset, or page tokens.
    """

    result = get_unified_history(limit=5)

    forbidden_fields = {
        "cursor",
        "offset",
        "page",
        "page_token",
        "next_page",
        "prev_page",
    }

    def _contains_forbidden(obj: Any) -> bool:
        if isinstance(obj, dict):
            if any(k in forbidden_fields for k in obj.keys()):
                return True
            return any(_contains_forbidden(v) for v in obj.values())
        if isinstance(obj, list):
            return any(_contains_forbidden(v) for v in obj)
        return False

    assert not _contains_forbidden(result)
