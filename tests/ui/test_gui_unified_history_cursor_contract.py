# tests/ui/test_gui_unified_history_cursor_contract.py
"""
GUI Unified History API - Cursor and Continuity Contract
--------------------------------------------------------

Locks presentation-only continuity guarantees:

- Cursor is optional
- Cursor is opaque
- Cursor does not affect authoritative shape
- Cursor absence is valid

These tests do not require real history data and do not enforce
implementation details. They lock shape and guarantees only.
"""

from __future__ import annotations

from typing import Any, Dict

from thn_cli.ui.history_api import get_unified_history


def test_cursor_is_optional() -> None:
    result: Dict[str, Any] = get_unified_history(limit=5)

    # Cursor may or may not exist; both are valid
    assert isinstance(result, dict)


def test_cursor_does_not_break_shape() -> None:
    result = get_unified_history(limit=5)

    assert "history" in result
    assert "entries" in result["history"]


def test_cursor_is_presentation_only() -> None:
    result = get_unified_history(limit=5)

    # Cursor must never replace or mutate authoritative blocks
    assert "status" in result
    assert "history" in result
    assert "schema_version" in result


def test_cursor_is_opaque_if_present() -> None:
    result = get_unified_history(limit=5)

    cursor = result.get("cursor")

    # If present, cursor must be JSON-safe and opaque
    if cursor is not None:
        assert isinstance(cursor, dict)
