# tests/golden/test_sync_unified_history_read_shape.py
"""
Golden: Unified History Read Model (Shape Only)
-----------------------------------------------

This test locks ONLY the composite JSON shape.

It intentionally does not assert:
    - Specific values
    - Ordering
    - Presence of real status data
    - Presence of real txlog entries

It asserts:
    - Required top-level keys
    - Authority labeling
    - Explicit absence semantics
    - Stable container structure
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from thn_cli.syncv2.history_read import read_unified_history


def _assert_keys(obj: Dict[str, Any], keys: set[str]) -> None:
    assert isinstance(obj, dict)
    assert set(obj.keys()) == keys


def test_unified_history_shape_only(tmp_path: Path) -> None:
    result = read_unified_history(scaffold_root=tmp_path)

    # ------------------------------------------------------------------
    # Top-level shape
    # ------------------------------------------------------------------

    _assert_keys(
        result,
        {
            "schema_version",
            "status",
            "history",
            "notes",
        },
    )

    assert result["schema_version"] == 1
    assert isinstance(result["notes"], list)

    # ------------------------------------------------------------------
    # Status block shape
    # ------------------------------------------------------------------

    status = result["status"]
    _assert_keys(
        status,
        {
            "authority",
            "contract",
            "present",
            "record",
            "notes",
        },
    )

    assert status["authority"] == "status_db"
    assert status["contract"] in ("live", "diagnostic_stub")
    assert isinstance(status["present"], bool)
    assert "record" in status
    assert isinstance(status["notes"], list)

    # ------------------------------------------------------------------
    # History block shape
    # ------------------------------------------------------------------

    history = result["history"]
    _assert_keys(
        history,
        {
            "authority",
            "contract",
            "count",
            "truncated",
            "entries",
            "notes",
        },
    )

    assert history["authority"] == "txlog"
    assert history["contract"] == "diagnostic_read_only"
    assert isinstance(history["count"], int)
    assert isinstance(history["truncated"], bool)
    assert isinstance(history["entries"], list)
    assert isinstance(history["notes"], list)
