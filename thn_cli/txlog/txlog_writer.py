from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def default_txlog_dir(scaffold_root: Path) -> Path:
    # Keep TXLOG under the scaffold so it is portable and audit-friendly.
    return scaffold_root / ".thn" / "txlog"


@dataclass(frozen=True)
class TxContext:
    tx_id: str
    started_at: str
    log_path: str


class TxLogWriter:
    """
    Minimal JSONL TXLOG writer.

    Each line is a single JSON object. This is append-only and crash-resilient.
    Future phases can add:
      - rollback journaling
      - staged apply
      - reconciliation / resume
    """

    def __init__(self, *, file_path: Path, tx_id: str, op: str, target: str) -> None:
        self._path = file_path
        self._tx_id = tx_id
        self._op = op
        self._target = target
        self._opened = False
        self._fh = None  # type: ignore[assignment]

    @property
    def path(self) -> Path:
        return self._path

    @property
    def tx_id(self) -> str:
        return self._tx_id

    def open(self) -> None:
        if self._opened:
            return
        _atomic_mkdir(self._path.parent)
        # newline-delimited JSON, UTF-8
        self._fh = self._path.open("a", encoding="utf-8", newline="\n")
        self._opened = True

    def close(self) -> None:
        if not self._opened:
            return
        try:
            self._fh.flush()
        finally:
            self._fh.close()
        self._opened = False

    def _write_line(self, payload: Dict[str, Any]) -> None:
        if not self._opened:
            self.open()
        payload = dict(payload)
        payload.setdefault("at", _utc_now_iso())
        payload.setdefault("tx_id", self._tx_id)
        payload.setdefault("op", self._op)
        payload.setdefault("target", self._target)
        self._fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._fh.flush()

    def begin(self, *, meta: Optional[Dict[str, Any]] = None) -> TxContext:
        started_at = _utc_now_iso()
        self._write_line(
            {
                "event": "begin",
                "started_at": started_at,
                "meta": meta or {},
            }
        )
        return TxContext(tx_id=self._tx_id, started_at=started_at, log_path=str(self._path))

    def action(self, *, action: Dict[str, Any]) -> None:
        self._write_line(
            {
                "event": "action",
                "action": action,
            }
        )

    def commit(self, *, summary: Optional[Dict[str, Any]] = None) -> None:
        self._write_line(
            {
                "event": "commit",
                "summary": summary or {},
            }
        )

    def abort(self, *, reason: str, error: Optional[str] = None) -> None:
        self._write_line(
            {
                "event": "abort",
                "reason": reason,
                "error": error or "",
            }
        )


def start_txlog(
    *,
    scaffold_root: Path,
    op: str,
    target: Path,
    txlog_dir: Optional[Path] = None,
) -> TxLogWriter:
    tx_id = uuid.uuid4().hex
    base = txlog_dir or default_txlog_dir(scaffold_root)
    # recovery-<txid>.jsonl
    path = base / f"{op}-{tx_id}.jsonl"
    return TxLogWriter(file_path=path, tx_id=tx_id, op=op, target=str(target))
