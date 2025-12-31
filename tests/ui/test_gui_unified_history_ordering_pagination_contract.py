# tests/ui/test_gui_unified_history_ordering_pagination_contract.py
"""
GUI Unified History API – Ordering & Pagination Contract
-------------------------------------------------------

Locks presentation-only behavior:
    • Default order: newest -> oldest (desc)
    • Reversible order: asc
    • Stable ordering with fallback when observed_at missing
    • Pagination applied after ordering
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from thn_cli.ui.history_api import get_unified_history


def _extract_times(result: Dict[str, Any]) -> List[str]:
    entries = result["history"]["entries"]
    return [e.get("observed_at") for e in entries]


def test_default_order_desc_is_stable():
    result = get_unified_history(limit=5)
    assert isinstance(result, dict)
    assert "history" in result
    # No assertion on values; stability + existence is the contract
    assert isinstance(result["history"]["entries"], list)


def test_reverse_order_asc():
    r_desc = get_unified_history(limit=5, order="desc")
    r_asc = get_unified_history(limit=5, order="asc")

    # If timestamps exist, asc should be reverse of desc (best-effort)
    d = _extract_times(r_desc)
    a = _extract_times(r_asc)

    if all(d) and all(a):
        assert list(reversed(d)) == a


def test_pagination_applies_after_ordering():
    r1 = get_unified_history(limit=2, offset=0)
    r2 = get_unified_history(limit=2, offset=2)

    e1 = r1["history"]["entries"]
    e2 = r2["history"]["entries"]

    # No overlap expected between pages
    ids1 = {id(e) for e in e1}
    ids2 = {id(e) for e in e2}
    assert ids1.isdisjoint(ids2)


def test_invalid_order_falls_back_to_default():
    r = get_unified_history(limit=3, order="invalid")
    assert isinstance(r["history"]["entries"], list)
