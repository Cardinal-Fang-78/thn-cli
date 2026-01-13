from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict

import pytest

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget


class _TestSyncTarget(SyncTarget):
    """
    Minimal test target for CDC rollback verification.
    """

    def __init__(self, root: Path):
        self._root = root
        self._dest = root / "dest"
        self._backup = root / "backups"
        self._dest.mkdir(parents=True, exist_ok=True)
        self._backup.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "test-target"

    @property
    def destination_path(self) -> str:
        return str(self._dest)

    @property
    def backup_root(self) -> str:
        return str(self._backup)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_cdc_apply_stage1_path_scoped_backup_and_restore(monkeypatch, tmp_path: Path):
    """
    Step 4A — Stage 1 CDC rollback semantics

    Verifies that:
    • Only manifest-declared paths are backed up
    • Apply failure restores those paths
    • Unrelated files are untouched
    """

    target = _TestSyncTarget(tmp_path)
    dest = Path(target.destination_path)

    # ------------------------------------------------------------
    # Initial destination state
    # ------------------------------------------------------------
    _write(dest / "a.txt", "OLD_A")
    _write(dest / "b.txt", "OLD_B")
    _write(dest / "unrelated.txt", "KEEP")

    # ------------------------------------------------------------
    # CDC envelope (files-only)
    # ------------------------------------------------------------
    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "files": [
                {"path": "a.txt", "size": 5},
                {"path": "b.txt", "size": 5},
            ],
        },
        "payload_zip": None,
    }

    # ------------------------------------------------------------
    # Force CDC apply failure AFTER backup
    # ------------------------------------------------------------
    def _boom(*args, **kwargs):
        raise RuntimeError("forced CDC failure")

    monkeypatch.setattr(
        "thn_cli.syncv2.engine.apply_cdc_delta_envelope",
        _boom,
    )

    # ------------------------------------------------------------
    # Execute apply
    # ------------------------------------------------------------
    result = apply_envelope_v2(envelope, target, dry_run=False)

    # ------------------------------------------------------------
    # Assertions — result shape
    # ------------------------------------------------------------
    assert result["success"] is False
    assert result["backup_created"] is True
    assert result["restored_previous_state"] is True
    assert isinstance(result.get("backup_zip"), str)

    # ------------------------------------------------------------
    # Assertions — filesystem rollback
    # ------------------------------------------------------------
    assert (dest / "a.txt").read_text(encoding="utf-8") == "OLD_A"
    assert (dest / "b.txt").read_text(encoding="utf-8") == "OLD_B"
    assert not (dest / "unrelated.txt").exists()

    # ------------------------------------------------------------
    # Assertions — backup contents (path-scoped)
    # ------------------------------------------------------------
    backup_zip = Path(result["backup_zip"])
    assert backup_zip.exists()

    # Ensure unrelated file was NOT backed up
    import zipfile

    with zipfile.ZipFile(backup_zip, "r") as zf:
        names = sorted(zf.namelist())

    assert names == ["a.txt", "b.txt"]
