# tests/ui/test_gui_unified_history_capabilities_contract.py
"""
GUI Unified History API – Capability Declaration Contract
---------------------------------------------------------

Locks the presence, shape, and semantics of the GUI-facing capability
declaration block.

These tests:
    - Do not require real history data
    - Do not enforce implementation details
    - Lock declaration surface only

Contract:
    - If present, "capabilities" MUST be a JSON-safe dict
    - Capabilities MUST NOT replace/mutate authoritative top-level blocks
    - Capability values, if present, MUST be boolean feature flags
"""

from __future__ import annotations

import json
from typing import Any, Dict

from thn_cli.ui.history_api import get_unified_history


def _assert_json_safe(obj: Any) -> None:
    json.dumps(obj)


def test_capabilities_block_is_optional() -> None:
    result: Dict[str, Any] = get_unified_history(limit=1)

    # Capabilities may be absent; absence is valid.
    assert isinstance(result, dict)

    caps = result.get("capabilities")
    if caps is not None:
        assert isinstance(caps, dict)
        _assert_json_safe(caps)


def test_capabilities_do_not_mutate_authoritative_blocks() -> None:
    result: Dict[str, Any] = get_unified_history(limit=1)

    # Authoritative blocks must always exist
    assert "status" in result
    assert "history" in result
    assert "schema_version" in result


def test_capability_values_are_boolean_if_present() -> None:
    result: Dict[str, Any] = get_unified_history(limit=1)
    caps = result.get("capabilities")

    if isinstance(caps, dict):
        for key, value in caps.items():
            assert isinstance(key, str)
            assert isinstance(value, bool)
