from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget
from thn_cli.txlog.history_reader import HistoryQuery, find_scaffold_root, load_sync_history


class _TestSyncTarget(SyncTarget):
    """
    Minimal SyncTarget stub for CDC Stage 2 TXLOG observability tests.
    """

    def __init__(self, root: Path):
        self._root = root
        self._dest = root / "dest"
        self._dest.mkdir(parents=True, exist_ok=True)
        self._backup_root = root / "backups"

        # Explicit scaffold marker
        (root / ".thn" / "txlog").mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "test"

    @property
    def destination_path(self) -> str:
        return str(self._dest)

    @property
    def backup_root(self) -> str:
        return str(self._backup_root)


def test_cdc_apply_stage2_txlog_emission(tmp_path: Path) -> None:
    """
    Golden: CDC Stage 2 emits a complete TXLOG transaction.

    Locks:
    • begin + commit observed
    • correct op and target
    • diagnostic-only observability (no inference)
    """

    target = _TestSyncTarget(tmp_path)
    dest = Path(target.destination_path)

    # Initial destination state
    (dest / "keep.txt").write_text("KEEP", encoding="utf-8")

    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            # CRITICAL: binds TXLOG scaffold deterministically
            "source": str(tmp_path),
            "entries": [
                {"path": "new.txt", "op": "write", "chunks": []},
            ],
        }
    }

    result = apply_envelope_v2(envelope, target, dry_run=False)
    assert result["success"] is True

    # ------------------------------------------------------------
    # Load TXLOG history
    # ------------------------------------------------------------
    scaffold_root = find_scaffold_root(tmp_path)
    assert scaffold_root == tmp_path

    history = load_sync_history(
        scaffold_root=scaffold_root,
        query=HistoryQuery(limit=10),
    )

    assert history["status"] == "OK"
    assert history["count"] >= 1

    tx = history["history"][0]

    # ------------------------------------------------------------
    # TXLOG contract assertions (diagnostic-only)
    # ------------------------------------------------------------
    assert tx["op"] == "sync_apply"
    assert tx["target"] == str(dest)
    assert tx["outcome"] == "commit"
    assert tx["integrity"] == "complete"

    # Guardrail: no inferred execution data
    assert "files" not in tx
    assert "applied_count" not in tx
