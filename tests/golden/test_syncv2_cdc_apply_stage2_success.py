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


def test_cdc_apply_stage2_write_and_delete_success(monkeypatch, tmp_path: Path):
    """
    Golden: Stage 2 CDC apply (write + delete)

    Verifies:
    • Writes occur via chunk reconstruction
    • Deletes remove declared paths
    • Unrelated files are untouched
    """

    target = _TestSyncTarget(tmp_path)
    dest = Path(target.destination_path)

    # Initial state
    (dest / "old.txt").write_text("OLD", encoding="utf-8")
    (dest / "keep.txt").write_text("KEEP", encoding="utf-8")

    # Chunk loader stub
    def _load_chunk(_target: str, chunk_id: str) -> bytes:
        return f"DATA:{chunk_id}".encode("utf-8")

    monkeypatch.setattr(
        "thn_cli.syncv2.delta.apply.load_chunk",
        _load_chunk,
    )

    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "entries": [
                {"path": "new.txt", "op": "write", "chunks": ["c1", "c2"]},
                {"path": "old.txt", "op": "delete"},
            ],
        }
    }

    result = apply_envelope_v2(envelope, target, dry_run=False)

    # ------------------------------------------------------------
    # Assertions — successful Stage 2 apply semantics
    # ------------------------------------------------------------
    assert result["success"] is True
    assert "errors" not in result
    assert result["applied_count"] == 1

    # Written file
    assert (dest / "new.txt").read_text(encoding="utf-8") == "DATA:c1DATA:c2"

    # Deleted file
    assert not (dest / "old.txt").exists()

    # Unrelated file preserved
    assert (dest / "keep.txt").read_text(encoding="utf-8") == "KEEP"
