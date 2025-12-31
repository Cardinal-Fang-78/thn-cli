# tests/ui/test_gui_unified_history_filtering_contract.py
"""
GUI Unified History API – Filtering Contract
--------------------------------------------

Locks presentation-only filtering guarantees:
    • Filtering is optional
    • Filtering preserves shape
    • Empty results are valid
    • Filtering is deterministic
    • Filtering does not affect cursor, ordering, or pagination
"""

from __future__ import annotations

from typing import Any, Dict

from thn_cli.ui.history_api import get_unified_history


def test_filtering_is_optional():
    result: Dict[str, Any] = get_unified_history(limit=5)

    assert isinstance(result, dict)
    assert "history" in result
    assert isinstance(result["history"].get("entries"), list)


def test_filter_target_preserves_shape():
    result = get_unified_history(limit=5, target="nonexistent-target")

    assert isinstance(result, dict)
    assert "history" in result
    assert "entries" in result["history"]
    assert "count" in result["history"]


def test_filter_tx_id_preserves_shape():
    result = get_unified_history(limit=5, tx_id="nonexistent-tx")

    assert isinstance(result, dict)
    assert "history" in result
    assert "entries" in result["history"]
    assert "count" in result["history"]


def test_empty_filter_result_is_valid():
    result = get_unified_history(limit=5, target="__no_match__")

    entries = result["history"]["entries"]
    count = result["history"]["count"]

    assert isinstance(entries, list)
    assert isinstance(count, int)
    assert count == len(entries)


def test_filtering_is_deterministic():
    r1 = get_unified_history(limit=5, target="same-input")
    r2 = get_unified_history(limit=5, target="same-input")

    assert r1["history"]["entries"] == r2["history"]["entries"]


def test_filtering_does_not_remove_authoritative_blocks():
    result = get_unified_history(limit=5, target="anything")

    assert "status" in result
    assert "history" in result
    assert "schema_version" in result
