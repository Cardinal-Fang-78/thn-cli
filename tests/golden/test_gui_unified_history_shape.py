# tests/golden/test_gui_unified_history_shape.py
"""
Golden: GUI Unified History API (Shape Only)
-------------------------------------------

Locks the GUI-facing unified history payload shape.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from thn_cli.ui.history_api import get_unified_history


def _assert_keys(obj: Dict[str, Any], keys: set[str]) -> None:
    assert isinstance(obj, dict)
    assert set(obj.keys()) == keys


def test_gui_unified_history_shape_only(tmp_path: Path) -> None:
    result = get_unified_history(scaffold_root=str(tmp_path))

    _assert_keys(
        result,
        {
            "schema_version",
            "status",
            "history",
            "notes",
        },
    )

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
