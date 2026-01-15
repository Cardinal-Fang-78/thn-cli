# tests/golden/test_syncv2_cdc_apply_stage2_observability_failure.py

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget


class _TestSyncTarget(SyncTarget):
    """
    Minimal SyncTarget stub for CDC Stage 2 observability failure tests.
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


def test_cdc_apply_stage2_observability_failure_with_rollback(monkeypatch, tmp_path: Path) -> None:
    """
    Golden: CDC Stage 2 failure propagates observability and restores state.

    Locks:
    • Path-scoped backup creation
    • Rollback on apply failure
    • Observability fields forwarded when present
    • No inferred metrics
    """

    target = _TestSyncTarget(tmp_path)
    dest = Path(target.destination_path)

    # ------------------------------------------------------------
    # Initial destination state
    # ------------------------------------------------------------
    (dest / "write.txt").write_text("OLD_WRITE", encoding="utf-8")
    (dest / "delete.txt").write_text("OLD_DELETE", encoding="utf-8")
    (dest / "keep.txt").write_text("KEEP", encoding="utf-8")

    # ------------------------------------------------------------
    # Force CDC apply failure AFTER backup
    # (engine-level symbol patch)
    # ------------------------------------------------------------
    def _boom(*args, **kwargs):
        return {
            "success": False,
            "error": "forced CDC failure",
            "written_files": 1,
            "written_bytes": 123,
            "deleted_files": 1,
            "errors": ["forced failure"],
        }

    monkeypatch.setattr(
        "thn_cli.syncv2.engine.apply_cdc_delta_envelope",
        _boom,
    )

    # ------------------------------------------------------------
    # CDC Stage 2 envelope
    # ------------------------------------------------------------
    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "entries": [
                {"path": "write.txt", "op": "write", "chunks": ["c1"]},
                {"path": "delete.txt", "op": "delete"},
            ],
        }
    }

    # ------------------------------------------------------------
    # Execute apply
    # ------------------------------------------------------------
    result = apply_envelope_v2(envelope, target, dry_run=False)

    # ------------------------------------------------------------
    # Assertions — engine failure result
    # ------------------------------------------------------------
    assert result["success"] is False
    assert result["backup_created"] is True
    assert result["restored_previous_state"] is True
    assert "error" in result

    # Observability forwarded verbatim (no recompute)
    assert result["written_files"] == 1
    assert result["written_bytes"] == 123
    assert result["deleted_files"] == 1
    assert "errors" in result

    # ------------------------------------------------------------
    # Assertions — backup contents are path-scoped
    # ------------------------------------------------------------
    backup_zip = Path(result["backup_zip"])
    assert backup_zip.exists()

    with zipfile.ZipFile(backup_zip, "r") as zf:
        names = sorted([n for n in zf.namelist() if not n.endswith("/")])

    assert set(names) == {"delete.txt", "write.txt"}

    # ------------------------------------------------------------
    # Assertions — filesystem rollback
    # ------------------------------------------------------------
    assert (dest / "write.txt").read_text(encoding="utf-8") == "OLD_WRITE"
    assert (dest / "delete.txt").read_text(encoding="utf-8") == "OLD_DELETE"
    assert not (dest / "keep.txt").exists()
