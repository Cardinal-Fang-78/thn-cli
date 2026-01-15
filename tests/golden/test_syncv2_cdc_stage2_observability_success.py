# tests/golden/test_syncv2_cdc_apply_stage2_observability_success.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.base import SyncTarget


class _TestSyncTarget(SyncTarget):
    """
    Minimal SyncTarget stub for CDC Stage 2 observability tests.
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


def test_cdc_apply_stage2_observability_success(monkeypatch, tmp_path: Path) -> None:
    """
    Golden: CDC Stage 2 apply forwards observability fields verbatim.

    Locks:
    • written_files
    • written_bytes
    • deleted_files
    • No inference or recomputation at engine level
    """

    target = _TestSyncTarget(tmp_path)
    dest = Path(target.destination_path)

    # ------------------------------------------------------------
    # Initial destination state
    # ------------------------------------------------------------
    (dest / "delete.txt").write_text("OLD", encoding="utf-8")
    (dest / "keep.txt").write_text("KEEP", encoding="utf-8")

    # ------------------------------------------------------------
    # Stub chunk loader (deterministic bytes)
    # ------------------------------------------------------------
    def _load_chunk(_target: str, chunk_id: str) -> bytes:
        return f"DATA:{chunk_id}".encode("utf-8")

    monkeypatch.setattr(
        "thn_cli.syncv2.delta.apply.load_chunk",
        _load_chunk,
    )

    # ------------------------------------------------------------
    # CDC Stage 2 envelope
    # ------------------------------------------------------------
    envelope: Dict[str, Any] = {
        "manifest": {
            "version": 2,
            "mode": "cdc-delta",
            "entries": [
                {"path": "write.txt", "op": "write", "chunks": ["c1", "c2"]},
                {"path": "delete.txt", "op": "delete"},
            ],
        }
    }

    # ------------------------------------------------------------
    # Execute apply
    # ------------------------------------------------------------
    result = apply_envelope_v2(envelope, target, dry_run=False)

    # ------------------------------------------------------------
    # Assertions — engine result shape
    # ------------------------------------------------------------
    assert result["success"] is True
    assert result["operation"] == "apply"
    assert result["applied_count"] == 1

    # Observability (forwarded, not inferred)
    assert result["written_files"] == 1
    assert result["written_bytes"] == len(b"DATA:c1DATA:c2")
    assert result["deleted_files"] == 1

    # Errors must not be present on success
    assert "errors" not in result

    # ------------------------------------------------------------
    # Assertions — filesystem effects
    # ------------------------------------------------------------
    assert (dest / "write.txt").read_text(encoding="utf-8") == "DATA:c1DATA:c2"
    assert not (dest / "delete.txt").exists()
    assert (dest / "keep.txt").read_text(encoding="utf-8") == "KEEP"
