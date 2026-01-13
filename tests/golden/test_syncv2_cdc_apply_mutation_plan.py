# tests/golden/test_syncv2_cdc_apply_mutation_plan.py

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import pytest

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget

# ---------------------------------------------------------------------------
# Minimal test target (contract-compliant)
# ---------------------------------------------------------------------------


class _TestSyncTarget(SyncTarget):
    def __init__(self, *, name: str, destination_path: str, backup_root: str):
        self.name = name
        self.destination_path = destination_path
        self.backup_root = backup_root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _make_target(tmp_path: Path) -> _TestSyncTarget:
    dest = tmp_path / "dest"
    dest.mkdir()
    return _TestSyncTarget(
        name="test",
        destination_path=str(dest),
        backup_root=str(tmp_path / "backups"),
    )


# ---------------------------------------------------------------------------
# Stage 1 — manifest["files"] (writes only)
# ---------------------------------------------------------------------------


def test_cdc_apply_stage1_path_scoped_backup_and_restore(tmp_path: Path):
    target = _make_target(tmp_path)
    dest = Path(target.destination_path)

    # Pre-existing files
    _write(dest / "a.txt", "OLD_A")
    _write(dest / "b.txt", "OLD_B")
    _write(dest / "unrelated.txt", "KEEP")

    payload_src = tmp_path / "payload_src"
    _write(payload_src / "a.txt", "NEW_A")
    _write(payload_src / "b.txt", "NEW_B")

    payload_zip = tmp_path / "payload.zip"
    shutil.make_archive(
        str(payload_zip.with_suffix("")),
        "zip",
        root_dir=payload_src,
        base_dir=".",
    )

    envelope = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "files": [
                {"path": "a.txt", "size": 5},
                {"path": "b.txt", "size": 5},
            ],
        },
        "payload_zip": str(payload_zip),
    }

    result = apply_envelope_v2(envelope, target, dry_run=False)

    assert result["success"] is True
    assert result["applied_count"] == 2
    assert result["backup_created"] is True
    assert result["restored_previous_state"] is False

    # Files updated
    assert _read(dest / "a.txt") == "NEW_A"
    assert _read(dest / "b.txt") == "NEW_B"

    # Unrelated file untouched
    assert _read(dest / "unrelated.txt") == "KEEP"


# ---------------------------------------------------------------------------
# Stage 2 — manifest["entries"] (write + delete)
# ---------------------------------------------------------------------------


def test_cdc_apply_stage2_write_and_delete_with_scoped_backup(tmp_path: Path, monkeypatch):
    target = _make_target(tmp_path)
    dest = Path(target.destination_path)

    # Initial state
    _write(dest / "write.txt", "OLD_WRITE")
    _write(dest / "delete.txt", "OLD_DELETE")
    _write(dest / "unrelated.txt", "KEEP")

    envelope = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "entries": [
                {"path": "write.txt", "op": "write"},
                {"path": "delete.txt", "op": "delete"},
            ],
        },
        "payload_zip": None,
    }

    def _boom(*args, **kwargs):
        raise RuntimeError("forced CDC apply failure")

    # IMPORTANT: patch the engine-bound symbol
    monkeypatch.setattr(
        "thn_cli.syncv2.engine.apply_cdc_delta_envelope",
        _boom,
    )

    result = apply_envelope_v2(envelope, target, dry_run=False)

    assert result["success"] is False
    assert result["backup_created"] is True
    assert result["restored_previous_state"] is True

    assert _read(dest / "write.txt") == "OLD_WRITE"
    assert _read(dest / "delete.txt") == "OLD_DELETE"
    assert not (dest / "unrelated.txt").exists()
