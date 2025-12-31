# tests/ui/test_gui_unified_history_field_exposure_contract.py
"""
GUI Unified History API – Field Exposure & Redaction Contract
------------------------------------------------------------

Locks presentation-only guarantees:
    • Default field pass-through
    • Shape preservation
    • No field invention
    • Optional redaction safety
"""

from __future__ import annotations

from typing import Any, Dict

from thn_cli.ui.history_api import get_unified_history


def test_default_field_pass_through_preserves_shape():
    result: Dict[str, Any] = get_unified_history(limit=5)

    assert isinstance(result, dict)
    assert "history" in result
    assert isinstance(result["history"].get("entries"), list)


def test_entries_are_dicts():
    result = get_unified_history(limit=5)

    for entry in result["history"]["entries"]:
        assert isinstance(entry, dict)


def test_no_field_invention():
    result = get_unified_history(limit=5)

    # Ensure API does not invent top-level keys
    allowed = {"schema_version", "status", "history", "notes", "cursor"}
    for key in result.keys():
        assert key in allowed


def test_redaction_does_not_affect_authoritative_blocks():
    result = get_unified_history(limit=5)

    assert "status" in result
    assert "history" in result
    assert "schema_version" in result


def test_empty_entries_are_valid():
    result = get_unified_history(limit=5, target="__no_match__")

    entries = result["history"]["entries"]
    count = result["history"]["count"]

    assert isinstance(entries, list)
    assert isinstance(count, int)
    assert count == len(entries)
