from __future__ import annotations

import json
from pathlib import Path

from thn_cli.snapshots.diff_engine import diff_snapshots

GOLDEN_DIR = Path(__file__).parent / "snapshots_diff"


def _load(name: str):
    return json.loads((GOLDEN_DIR / name).read_text(encoding="utf-8"))


def _assert_diff(before_name: str, after_name: str, golden_name: str):
    before = _load(before_name)
    after = _load(after_name)
    expected = _load(golden_name)

    result = diff_snapshots(before=before, after=after)
    assert result == expected


def test_diff_no_changes():
    _assert_diff(
        "snap_a.json",
        "snap_a.json",
        "diff_none.json",
    )


def test_diff_added_paths():
    _assert_diff(
        "snap_a.json",
        "snap_b_added.json",
        "diff_added.json",
    )


def test_diff_removed_paths():
    _assert_diff(
        "snap_b_added.json",
        "snap_a.json",
        "diff_removed.json",
    )


def test_diff_mixed_changes():
    _assert_diff(
        "snap_b_added.json",
        "snap_c_mixed.json",
        "diff_mixed.json",
    )
