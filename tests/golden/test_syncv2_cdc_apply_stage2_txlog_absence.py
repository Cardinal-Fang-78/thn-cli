from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget
from thn_cli.txlog.history_reader import HistoryQuery, find_scaffold_root, load_sync_history


class _TestSyncTarget(SyncTarget):
    def __init__(self, root: Path):
        self._root = root
        self._dest = root / "dest"
        self._dest.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "test"

    @property
    def destination_path(self) -> str:
        return str(self._dest)

    @property
    def backup_root(self) -> str:
        # backup_root is irrelevant here; no backup expected
        return str(self._root / "backups")


def test_cdc_apply_stage2_does_not_emit_txlog_without_scaffold(tmp_path: Path) -> None:
    """
    Golden: CDC Stage 2 does NOT emit TXLOG when no scaffold exists.

    Locks:
    • TXLOG emission is scaffold-scoped
    • No implicit .thn creation
    • Observability remains best-effort and non-inferential
    """

    target = _TestSyncTarget(tmp_path)

    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "entries": [
                {"path": "new.txt", "op": "write", "chunks": []},
            ],
        }
    }

    result = apply_envelope_v2(envelope, target, dry_run=False)
    assert result["success"] is True

    # No scaffold should be discoverable
    scaffold_root = find_scaffold_root(tmp_path)
    assert scaffold_root is None

    # Therefore no TXLOG history can exist
    history = load_sync_history(
        scaffold_root=tmp_path,
        query=HistoryQuery(limit=10),
    )

    assert history["count"] == 0
