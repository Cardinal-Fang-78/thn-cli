# thn_cli/syncv2/txlog.py

"""
THN Sync V2 Transaction Log (Hybrid-Standard)
--------------------------------------------

Responsibilities:
    • Append per-operation Sync V2 transaction records.
    • Guarantee atomic JSONL writes.
    • Enforce Hybrid-Standard record structure.
    • Provide minimal read utilities for diagnostics.

Write Target:
    <sync_root>/logs/sync_v2_log.jsonl

Record Shape (always JSON, one per line):
    {
        "timestamp": "UTC ISO-8601 Z",
        "tx_id": "<hex-id>",
        "type": "dry-run" | "apply" | "failed" | "unknown",
        "target": "<target-name>" | null,
        "status": "OK" | "DRY_RUN" | "FAILED",
        "details": { ... arbitrary engine payload ... }
    }

Notes:
    • Never breaks on malformed incoming entries; logging is best-effort.
    • Always UTF-8, never ASCII-escaping real characters.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, List, Optional

from thn_cli.pathing import get_thn_paths

# ---------------------------------------------------------------------------
# Paths and timestamp utilities
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """
    Return a UTC timestamp in strict ISO-8601 Z format without microseconds.
    Example: "2025-12-09T12:34:56Z"
    """
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _log_path() -> str:
    """
    Compute the sync_v2_log.jsonl full path.
    Ensures the log directory exists.
    """
    paths = get_thn_paths()
    log_dir = paths.get("sync_logs") or os.path.join(paths["sync_root"], "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "sync_v2_log.jsonl")


# ---------------------------------------------------------------------------
# Record shaping
# ---------------------------------------------------------------------------


def _normalize_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw transaction dict into a Hybrid-Standard log record.
    """
    tx_id = entry.get("tx_id")
    status = entry.get("status") or "UNKNOWN"
    target = (
        entry.get("routing", {}).get("target") if isinstance(entry.get("routing"), dict) else None
    )

    # Determine transaction type
    if entry.get("dry_run"):
        tx_type = "dry-run"
    elif status == "OK":
        tx_type = "apply"
    elif status == "FAILED":
        tx_type = "failed"
    else:
        tx_type = "unknown"

    # Package details safely
    details = dict(entry)
    details.pop("timestamp", None)  # replaced by canonical timestamp

    return {
        "timestamp": _now_iso(),
        "tx_id": tx_id,
        "type": tx_type,
        "target": entry.get("target") or target,
        "status": status,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Public API — append-only logging
# ---------------------------------------------------------------------------


def log_transaction(entry: Dict[str, Any]) -> None:
    """
    Append a Hybrid-Standard transaction record to sync_v2_log.jsonl.

    Guaranteed properties:
        • Atomic append for each entry.
        • Hybrid-Standard record shape.
        • UTF-8 no-escape real JSON.
    """
    record = _normalize_entry(entry)
    path = _log_path()

    # Atomic append: open, write line, flush+close
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write("\n")
    except Exception as exc:
        # Logging must NEVER interrupt the caller.
        # Fail silently; diagnostics may warn externally if desired.
        print(f"[WARN] Failed to write Sync V2 log entry: {exc}")


# ---------------------------------------------------------------------------
# Optional read utilities (for diagnostics or future CLI commands)
# ---------------------------------------------------------------------------


def read_all_transactions(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Read back transaction records from sync_v2_log.jsonl.

    Parameters:
        limit: if provided, return only the most recent N entries.

    Returns:
        A list of parsed JSON objects (best-effort).
    """
    path = _log_path()
    if not os.path.exists(path):
        return []

    results: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    if limit is not None:
        lines = lines[-limit:]

    for line in lines:
        try:
            results.append(json.loads(line))
        except Exception:
            # Skip malformed records; logging is best-effort.
            continue

    return results
