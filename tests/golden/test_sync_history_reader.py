# tests/golden/test_sync_history_reader.py

import json
import subprocess
import sys
from pathlib import Path


def _write_jsonl(path: Path, records) -> None:
    lines = []
    for r in records:
        lines.append(json.dumps(r, ensure_ascii=False))
    path.write_text("\n".join(lines), encoding="utf-8")


def test_sync_history_reader_basic(tmp_path: Path):
    """
    Golden test for Unified History Reader (TXLOG-only, diagnostic).

    Validates:
      - Deterministic JSON shape
      - No inference or reconciliation
      - Correct integrity classification
      - Presence of diagnostic-only metadata
    """

    # Arrange: synthetic scaffold with txlog
    scaffold = tmp_path / "scaffold"
    txlog_dir = scaffold / ".thn" / "txlog"
    txlog_dir.mkdir(parents=True)

    txlog_file = txlog_dir / "sync_apply-abc123.jsonl"

    _write_jsonl(
        txlog_file,
        [
            {
                "event": "begin",
                "tx_id": "abc123",
                "op": "sync_apply",
                "target": "cli",
                "started_at": "2025-01-01T00:00:00Z",
            },
            {
                "event": "commit",
                "tx_id": "abc123",
                "op": "sync_apply",
                "target": "cli",
                "at": "2025-01-01T00:00:01Z",
                "summary": {
                    "outcome": "OK",
                    "mode": "raw-zip",
                },
            },
        ],
    )

    # Act
    code = (
        "from pathlib import Path;"
        "from thn_cli.txlog.history_reader import load_sync_history, HistoryQuery;"
        "import json;"
        f"p=Path(r'{scaffold}');"
        "res=load_sync_history(scaffold_root=p, query=HistoryQuery());"
        "print(json.dumps(res, indent=4, ensure_ascii=False))"
    )

    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0

    data = json.loads(proc.stdout)

    # Top-level contract
    assert data["status"] == "OK"
    assert data["count"] == 1
    assert data["truncated"] is False
    assert isinstance(data["history"], list)

    entry = data["history"][0]

    # Required diagnostic fields
    assert entry["tx_id"] == "abc123"
    assert entry["op"] == "sync_apply"
    assert entry["target"] == "cli"
    assert entry["started_at"] == "2025-01-01T00:00:00Z"
    assert entry["ended_at"] == "2025-01-01T00:00:01Z"
    assert entry["outcome"] == "commit"
    assert entry["integrity"] == "complete"
    assert entry["summary"] == {
        "outcome": "OK",
        "mode": "raw-zip",
    }

    # Diagnostic-only metadata (locked presence, not value)
    assert "observed_at" in entry
    assert "reason" in entry
