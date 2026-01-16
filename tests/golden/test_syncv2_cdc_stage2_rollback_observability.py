from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget


class _TestSyncTarget(SyncTarget):
    def __init__(self, root: Path):
        self._root = root
        self._dest = root / "dest"
        self._dest.mkdir(parents=True, exist_ok=True)

        # Ensure scaffold TXLOG discovery works (engine searches upward for ".thn")
        (root / ".thn" / "txlog").mkdir(parents=True, exist_ok=True)

        self._backup = root / "backups"
        self._backup.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "rollback-test"

    @property
    def destination_path(self) -> str:
        return str(self._dest)

    @property
    def backup_root(self) -> str:
        return str(self._backup)


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        obj = json.loads(line)
        if isinstance(obj, dict):
            out.append(obj)
    return out


def test_cdc_stage2_rollback_observability_and_restore(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """
    Golden: CDC Stage 2 rollback is explicit and restores prior state.

    Locks:
    - Stage 2 failure triggers rollback restore when a path-scoped backup exists
    - TXLOG includes an explicit rollback action before terminal abort
    - Rollback is best-effort observability only (no inference required)
    """

    target = _TestSyncTarget(tmp_path)
    dest = Path(target.destination_path)

    # Existing file that will be deleted during Stage 2 then must be restored by rollback
    (dest / "old.txt").write_text("OLD", encoding="utf-8")

    # Force chunk reconstruction failure during the write entry
    def _boom(_target: str, _chunk_id: str) -> bytes:
        raise RuntimeError("forced failure")

    monkeypatch.setattr("thn_cli.syncv2.delta.apply.load_chunk", _boom)

    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            # Note: ordering matters: delete happens, then write fails -> rollback needed
            "entries": [
                {"path": "old.txt", "op": "delete"},
                {"path": "bad.txt", "op": "write", "chunks": ["x"]},
            ],
        }
    }

    result = apply_envelope_v2(envelope, target, dry_run=False)
    assert result["success"] is False
    assert result["mode"] == "cdc-delta"
    assert result["backup_created"] is True
    assert result["backup_zip"]
    assert result["restored_previous_state"] is True

    # Destination must be restored: old.txt must exist with original content
    assert (dest / "old.txt").read_text(encoding="utf-8") == "OLD"
    # The failed write must not exist (atomic write guarantee)
    assert not (dest / "bad.txt").exists()

    # ------------------------------------------------------------
    # TXLOG assertions (read raw JSONL, do not depend on history aggregation)
    # ------------------------------------------------------------
    txlog_dir = tmp_path / ".thn" / "txlog"
    txlog_files = sorted(txlog_dir.glob("sync_apply-*.jsonl"))
    assert txlog_files, "Expected a sync_apply TXLOG file"

    records = _read_jsonl(txlog_files[-1])

    events = [r.get("event") for r in records]
    assert "begin" in events
    assert "abort" in events
    assert "action" in events

    # Rollback action must be explicit and include backup_zip
    rollback = next(
        r
        for r in records
        if r.get("event") == "action"
        and isinstance(r.get("action"), dict)
        and r["action"].get("type") == "rollback"
    )
    action = rollback["action"]
    assert action.get("stage") == 2
    assert action.get("mode") == "cdc-delta"
    assert action.get("restored") is True
    assert action.get("backup_zip") == result["backup_zip"]

    # Terminal must be abort (not commit)
    assert "commit" not in events
