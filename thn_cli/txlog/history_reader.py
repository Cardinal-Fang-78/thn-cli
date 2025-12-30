# thn_cli/txlog/history_reader.py
"""
THN TXLOG History Reader (Read-Only Diagnostics)
------------------------------------------------

Responsibilities:
    - Read scaffold-local TXLOG JSONL files:
        <scaffold_root>/.thn/txlog/*.jsonl
    - Aggregate per-transaction summaries (tx_id).
    - Provide stable JSON output for CLI diagnostics.
    - Provide a simple human-readable rendering.

Non-goals:
    - No mutation, repair, replay, or policy effects.
    - No assumptions about completeness or ordering of txlog lines.
    - No joins or reconciliation with Status DB.
    - No inference beyond parsing explicit TXLOG events.

Contract alignment notes:
    - tx_id is treated as opaque. Missing/unkeyed records use tx_id="unknown".
    - Integrity is diagnostic-only:
        * complete: begin + (commit or abort) observed
        * partial:  begin observed, missing terminal event
        * unknown:  malformed/unparseable records only
    - For unknown/partial transactions, we do not invent identity or ordering.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class HistoryQuery:
    limit: int = 50
    target: Optional[str] = None
    tx_id: Optional[str] = None


def _parse_iso_loose(value: str) -> Optional[datetime]:
    """
    Best-effort parse for ISO timestamps used in txlog.

    Supports:
      - ...Z
      - ...+00:00 (or any offset)
      - naive ISO

    Returns None if parsing fails.
    """
    if not value or not isinstance(value, str):
        return None
    v = value.strip()
    if not v:
        return None
    try:
        if v.endswith("Z"):
            return datetime.fromisoformat(v[:-1] + "+00:00")
        return datetime.fromisoformat(v)
    except Exception:
        return None


def _txlog_dir(scaffold_root: Path) -> Path:
    return scaffold_root / ".thn" / "txlog"


def find_scaffold_root(start: Path, max_depth: int = 10) -> Optional[Path]:
    """
    Search upward from 'start' for a directory containing ".thn/txlog".
    Returns the scaffold root path if found, otherwise None.
    """
    try:
        cur = start.resolve()
    except Exception:
        cur = start

    for _ in range(max_depth + 1):
        if _txlog_dir(cur).is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def _iter_txlog_files(tx_dir: Path) -> List[Path]:
    if not tx_dir.is_dir():
        return []
    files = sorted(tx_dir.glob("*.jsonl"))
    return [p for p in files if p.is_file()]


def _read_jsonl_lines(path: Path) -> List[Dict[str, Any]]:
    """
    Read JSONL records from a single txlog file.

    Malformed JSON lines are preserved as diagnostic records with:
        event="malformed", tx_id="unknown"
    """
    out: List[Dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return out

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
            else:
                out.append(
                    {
                        "event": "malformed",
                        "raw": line,
                        "tx_id": "unknown",
                    }
                )
        except Exception:
            out.append(
                {
                    "event": "malformed",
                    "raw": line,
                    "tx_id": "unknown",
                }
            )
    return out


def _first_nonempty_str(*vals: Any) -> str:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _aggregate_transactions(
    records: List[Dict[str, Any]],
    *,
    observed_at: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate txlog records into per-tx summaries.

    This is diagnostic-only aggregation:
        - No inference beyond explicit begin/commit/abort events.
        - No reconstruction of missing identity.
        - Malformed lines are bucketed under tx_id="unknown".
    """
    txs: Dict[str, Dict[str, Any]] = {}

    for r in records:
        if not isinstance(r, dict):
            continue

        tx_id = r.get("tx_id") if isinstance(r.get("tx_id"), str) else ""
        if not tx_id:
            tx_id = "unknown"

        tx = txs.get(tx_id)
        if tx is None:
            tx = {
                "tx_id": tx_id,
                "op": _first_nonempty_str(r.get("op")),
                "target": _first_nonempty_str(r.get("target")),
                "started_at": "",
                "ended_at": "",
                "outcome": "unknown",  # commit|abort|unknown
                "integrity": "partial",  # complete|partial|unknown
                "summary": {},
                # Diagnostic-only fields to support sorting/inspection without inventing identity.
                "observed_at": observed_at,
                "reason": "",
            }
            txs[tx_id] = tx

        # Fill op/target if missing.
        if not tx.get("op"):
            tx["op"] = _first_nonempty_str(r.get("op"))
        if not tx.get("target"):
            tx["target"] = _first_nonempty_str(r.get("target"))

        event = _first_nonempty_str(r.get("event"))
        if event == "malformed":
            # Do not overwrite a known tx with malformed content; just mark diagnostics.
            if tx.get("tx_id") == "unknown" and not tx.get("reason"):
                tx["reason"] = "malformed_jsonl_line"
            tx["integrity"] = "unknown"
            continue

        # TXLOG contract uses "started_at" on begin, and "at" on commit/abort.
        at = _first_nonempty_str(r.get("at"))
        if event == "begin":
            started_at = _first_nonempty_str(r.get("started_at"), at)
            if started_at and not tx.get("started_at"):
                tx["started_at"] = started_at
        elif event == "commit":
            tx["outcome"] = "commit"
            if at:
                tx["ended_at"] = at
            summary = r.get("summary")
            if isinstance(summary, dict):
                tx["summary"] = summary
        elif event == "abort":
            tx["outcome"] = "abort"
            if at:
                tx["ended_at"] = at
            tx["summary"] = {
                "reason": _first_nonempty_str(r.get("reason")),
                "error": _first_nonempty_str(r.get("error")),
            }
        else:
            # Unknown events are ignored (diagnostic reader is tolerant).
            if tx.get("tx_id") == "unknown" and not tx.get("reason"):
                tx["reason"] = "unknown_event_type"

        # Integrity rule: begin + terminal event => complete.
        if tx.get("started_at") and tx.get("outcome") in ("commit", "abort"):
            tx["integrity"] = "complete"
        else:
            # Keep "unknown" if already marked so; otherwise partial.
            if tx.get("integrity") != "unknown":
                tx["integrity"] = "partial"

    return txs


def _sort_key(tx: Dict[str, Any]) -> Tuple[int, float]:
    """
    Sort most-recent-first using ended_at then started_at.
    If parsing fails, use (0, 0.0).
    """
    ended = tx.get("ended_at") if isinstance(tx.get("ended_at"), str) else ""
    started = tx.get("started_at") if isinstance(tx.get("started_at"), str) else ""
    dt = _parse_iso_loose(ended) or _parse_iso_loose(started)
    if dt is None:
        return (0, 0.0)
    return (1, dt.timestamp())


def load_sync_history(*, scaffold_root: Path, query: HistoryQuery) -> Dict[str, Any]:
    tx_dir = _txlog_dir(scaffold_root)
    observed_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    files = _iter_txlog_files(tx_dir)
    if not files:
        return {
            "status": "OK",
            "scaffold_root": str(scaffold_root.resolve()),
            "txlog_dir": str(tx_dir),
            "history": [],
            "count": 0,
            "truncated": False,
            "notes": ["No txlog files found."],
        }

    all_records: List[Dict[str, Any]] = []
    for p in files:
        all_records.extend(_read_jsonl_lines(p))

    txs = _aggregate_transactions(all_records, observed_at=observed_at)
    items = list(txs.values())

    # Filters (string-based only, no inference)
    if query.tx_id:
        items = [t for t in items if str(t.get("tx_id", "")) == query.tx_id]
    if query.target:
        items = [t for t in items if str(t.get("target", "")) == query.target]

    # Sort most recent first
    items.sort(key=_sort_key, reverse=True)

    limit = int(query.limit) if query.limit is not None else 50
    if limit <= 0:
        limit = 50

    truncated = len(items) > limit
    items_out = items[:limit]

    return {
        "status": "OK",
        "scaffold_root": str(scaffold_root.resolve()),
        "txlog_dir": str(tx_dir),
        "history": items_out,
        "count": len(items_out),
        "truncated": truncated,
    }


def render_history_text(result: Dict[str, Any]) -> str:
    """
    Human-readable rendering for interactive use.

    Minor clarity improvements are allowed as long as JSON output remains stable.
    """
    lines: List[str] = []
    status = result.get("status", "OK")
    lines.append(f"THN Sync History ({status})")
    lines.append(f"Scaffold: {result.get('scaffold_root', '')}")
    lines.append(f"TXLOG:    {result.get('txlog_dir', '')}")

    count = int(result.get("count", 0) or 0)
    truncated = bool(result.get("truncated", False))
    lines.append(f"Count:    {count}" + (" (truncated)" if truncated else ""))
    lines.append("")

    history = result.get("history")
    if not isinstance(history, list) or not history:
        notes = result.get("notes")
        if isinstance(notes, list) and notes:
            for n in notes:
                if isinstance(n, str) and n.strip():
                    lines.append(f"- {n.strip()}")
        else:
            lines.append("- No history entries found.")
        return "\n".join(lines)

    for tx in history:
        if not isinstance(tx, dict):
            continue

        tx_id = str(tx.get("tx_id", ""))
        op = str(tx.get("op", ""))
        target = str(tx.get("target", ""))
        started_at = str(tx.get("started_at", ""))
        ended_at = str(tx.get("ended_at", ""))
        outcome = str(tx.get("outcome", "unknown"))
        integrity = str(tx.get("integrity", "partial"))

        lines.append(f"tx_id:     {tx_id}")
        if op:
            lines.append(f"op:        {op}")
        if target:
            lines.append(f"target:    {target}")
        if started_at:
            lines.append(f"started:   {started_at}")
        if ended_at:
            lines.append(f"ended:     {ended_at}")
        lines.append(f"outcome:   {outcome}")
        lines.append(f"integrity: {integrity}")

        reason = tx.get("reason")
        if isinstance(reason, str) and reason.strip():
            lines.append(f"reason:    {reason.strip()}")

        summary = tx.get("summary")
        if isinstance(summary, dict) and summary:
            lines.append("summary:")
            for k in sorted(summary.keys()):
                v = summary.get(k)
                if isinstance(v, (dict, list)):
                    try:
                        v_str = json.dumps(v, ensure_ascii=False)
                    except Exception:
                        v_str = str(v)
                else:
                    v_str = str(v)
                lines.append(f"  - {k}: {v_str}")

        lines.append("")
    return "\n".join(lines).rstrip()
