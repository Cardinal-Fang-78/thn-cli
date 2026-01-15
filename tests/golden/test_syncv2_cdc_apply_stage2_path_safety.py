from pathlib import Path
from typing import Any, Dict

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget


class _TestSyncTarget(SyncTarget):
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


def test_cdc_apply_stage2_rejects_path_traversal(monkeypatch, tmp_path: Path):
    """
    Golden: Stage 2 path traversal is rejected.

    Verifies:
    • Apply fails before mutation
    • No files are written
    • No unrelated paths are touched
    """

    target = _TestSyncTarget(tmp_path)
    dest = Path(target.destination_path)

    (dest / "safe.txt").write_text("SAFE", encoding="utf-8")

    monkeypatch.setattr(
        "thn_cli.syncv2.delta.apply.load_chunk",
        lambda *_: b"DATA",
    )

    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "entries": [
                {"path": "../escape.txt", "op": "write", "chunks": ["c1"]},
            ],
        }
    }

    result = apply_envelope_v2(envelope, target, dry_run=False)

    assert result["success"] is False
    assert not (dest / "escape.txt").exists()
    assert (dest / "safe.txt").read_text(encoding="utf-8") == "SAFE"
