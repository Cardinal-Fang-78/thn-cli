from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.status_db import get_history


class _TestSyncTarget:
    """
    Minimal SyncTarget stub for CDC Stage 2 testing.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self.name = "status-test"
        self.destination_path = str(root / "dest")
        self.backup_root = str(root / "backups")

        Path(self.destination_path).mkdir(parents=True, exist_ok=True)
        Path(self.backup_root).mkdir(parents=True, exist_ok=True)


def test_cdc_apply_stage2_status_db_not_written_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    Golden: CDC Stage 2 failure does NOT write to Status DB.

    Locks:
    • Failure history is not inferred
    • Status DB remains success-only
    • Diagnostics are TXLOG-only
    """

    # ------------------------------------------------------------
    # Isolate Status DB for this test
    # ------------------------------------------------------------
    monkeypatch.setenv("THN_SYNC_ROOT", str(tmp_path / "sync-root"))

    target = _TestSyncTarget(tmp_path)

    def _boom(*args, **kwargs):
        raise RuntimeError("forced failure")

    # Force Stage 2 chunk reconstruction failure
    monkeypatch.setattr(
        "thn_cli.syncv2.delta.apply.load_chunk",
        _boom,
    )

    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "entries": [
                {"path": "bad.txt", "op": "write", "chunks": ["x"]},
            ],
        }
    }

    result = apply_envelope_v2(envelope, target, dry_run=False)
    assert result["success"] is False

    # CDC Stage 2 failures MUST NOT be recorded in Status DB
    history = get_history(target=target.name, limit=5)
    assert history == []
