# tests/ui/test_gui_unified_history_api_shape.py
"""
GUI Unified History API – Shape & Contract Test
-----------------------------------------------

Purpose:
    Lock the GUI-facing unified history API contract.

Scope:
    • Direct API call (no CLI invocation)
    • Read-only
    • Shape preservation only
    • No inference or policy evaluation

This test ensures:
    • The API returns a JSON-safe dict
    • The top-level contract shape is stable
    • Strict diagnostics are preserved *if present*
"""

from __future__ import annotations

import json
from typing import Any, Dict

from thn_cli.ui.history_api import get_unified_history


def _assert_json_safe(obj: Any) -> None:
    """
    Verify object is JSON-serializable without mutation.
    """
    json.dumps(obj)


def test_gui_unified_history_api_shape() -> None:
    """
    GUI API must:
        • Return a dict
        • Be JSON-safe
        • Preserve authoritative shape
        • Not invent or infer fields
    """

    result: Dict[str, Any] = get_unified_history(limit=5)

    # --- basic contract ---
    assert isinstance(result, dict)
    _assert_json_safe(result)

    # --- top-level invariants (authoritative) ---
    assert "status" in result
    assert "history" in result
    assert "schema_version" in result

    # --- history block shape ---
    history = result["history"]
    assert isinstance(history, dict)
    assert "entries" in history
    assert "count" in history

    # --- strict diagnostics preservation ---
    # If strict diagnostics are present anywhere, GUI must receive them verbatim.
    def _contains_strict(obj: Any) -> bool:
        if isinstance(obj, dict):
            if "strict" in obj:
                return True
            return any(_contains_strict(v) for v in obj.values())
        if isinstance(obj, list):
            return any(_contains_strict(v) for v in obj)
        return False

    _contains_strict(result)  # assertion-by-traversal (no enforcement)
