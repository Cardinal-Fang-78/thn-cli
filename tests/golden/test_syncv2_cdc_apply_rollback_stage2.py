# tests/golden/test_syncv2_cdc_apply_rollback_stage2.py

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget


class _TestSyncTarget(SyncTarget):
    """
    Minimal SyncTarget stub for engine-level CDC rollback tests.
    """

    def __init__(self, root: Path):
        self._root = root
        self._dest = root / "dest"
        self._dest.mkdir(parents=True, exist_ok=True)

        self._backup_root = root / "backups"

    @property
    def name(self) -> str:
        return "test"

    @property
    def destination_path(self) -> str:
        return str(self._dest)

    @property
    def backup_root(self) -> str:
        return str(self._backup_root)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_cdc_apply_stage2_write_and_delete_path_scoped_backup_and_restore(
    monkeypatch, tmp_path: Path
) -> None:
    """
    Step 4B — Stage 2 CDC rollback semantics (entries: write + delete)

    Verifies that:
    • Only manifest-declared paths (writes + deletes) are backed up
    • Apply failure restores those paths
    • Unrelated files are NOT preserved (destination is replaced)
    """

    target = _TestSyncTarget(tmp_path)
    dest = Path(target.destination_path)

    # ------------------------------------------------------------
    # Initial destination state
    # ------------------------------------------------------------
    _write(dest / "write.txt", "OLD_WRITE")
    _write(dest / "delete.txt", "OLD_DELETE")
    _write(dest / "unrelated.txt", "KEEP")

    # ------------------------------------------------------------
    # CDC envelope (entries: write + delete)
    # NOTE: payload_zip is irrelevant here because we force apply failure.
    # ------------------------------------------------------------
    envelope: Dict[str, Any] = {
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

    # ------------------------------------------------------------
    # Force CDC apply failure AFTER backup
    # (patch the engine-bound symbol)
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

    backup_zip = Path(result["backup_zip"])
    assert backup_zip.exists()

    # ------------------------------------------------------------
    # Assertions — backup contents are path-scoped
    # ------------------------------------------------------------
    with zipfile.ZipFile(backup_zip, "r") as zf:
        names = sorted([n for n in zf.namelist() if not n.endswith("/")])

    assert set(names) == {"delete.txt", "write.txt"}

    # ------------------------------------------------------------
    # Assertions — filesystem rollback
    # Destination is replaced; only backed-up files are restored.
    # ------------------------------------------------------------
    assert (dest / "write.txt").read_text(encoding="utf-8") == "OLD_WRITE"
    assert (dest / "delete.txt").read_text(encoding="utf-8") == "OLD_DELETE"
    assert not (dest / "unrelated.txt").exists()
