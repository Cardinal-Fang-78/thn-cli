# thn_cli/syncv2/history_read.py
"""
THN Sync V2 – Unified History Read Model (Read-Only)
---------------------------------------------------

Responsibilities:
    - Provide a composite, read-only view over:
        • Status DB (authoritative terminal state)
        • TXLOG (per-operation lineage)
    - Make authority explicit.
    - Make absence explicit.
    - Provide a single, stable JSON-serializable shape for:
        • CLI consumption
        • GUI consumption
        • Future strict modes

Non-goals:
    - No reconciliation between status and txlog
    - No inference or reconstruction
    - No ordering guarantees across sources
    - No mutation, repair, or policy effects
    - No execution semantics

Contract:
    - Shape is locked via golden test.
    - Values may be stubbed, but meaning must never be implied.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from thn_cli.syncv2.status_read import read_status_db
from thn_cli.txlog.history_reader import HistoryQuery, find_scaffold_root, load_sync_history


def read_unified_history(
    *,
    scaffold_root: Optional[Path] = None,
    txlog_query: Optional[HistoryQuery] = None,
) -> Dict[str, Any]:
    """
    Read-only composite history view.

    This function performs NO inference and NO reconciliation.
    It simply aggregates independent read surfaces into a single container.
    """

    # ------------------------------------------------------------------
    # Status DB read (authoritative terminal state)
    # ------------------------------------------------------------------

    try:
        status_result = read_status_db()
        status_block = {
            "authority": "status_db",
            "contract": "live",
            "present": bool(status_result.get("present")),
            "record": status_result.get("record"),
            "notes": [],
        }
    except Exception as exc:
        # Best-effort, non-throwing diagnostic behavior
        status_block = {
            "authority": "status_db",
            "contract": "diagnostic_stub",
            "present": False,
            "record": None,
            "notes": [f"Status DB read failed: {exc}"],
        }

    # ------------------------------------------------------------------
    # TXLOG read (per-operation lineage)
    # ------------------------------------------------------------------

    if scaffold_root is None:
        found = find_scaffold_root(Path.cwd())
        scaffold_root = found if found is not None else Path.cwd()

    query = txlog_query or HistoryQuery()

    try:
        txlog_result = load_sync_history(
            scaffold_root=scaffold_root,
            query=query,
        )

        history_block = {
            "authority": "txlog",
            "contract": "diagnostic_read_only",
            "count": int(txlog_result.get("count", 0) or 0),
            "truncated": bool(txlog_result.get("truncated", False)),
            "entries": list(txlog_result.get("history", [])),
            "notes": (
                list(txlog_result.get("notes", []))
                if isinstance(txlog_result.get("notes"), list)
                else []
            ),
        }
    except Exception as exc:
        history_block = {
            "authority": "txlog",
            "contract": "diagnostic_read_only",
            "count": 0,
            "truncated": False,
            "entries": [],
            "notes": [f"TXLOG read failed: {exc}"],
        }

    # ------------------------------------------------------------------
    # Composite container (shape locked)
    # ------------------------------------------------------------------

    return {
        "schema_version": 1,
        "status": status_block,
        "history": history_block,
        "notes": [],
    }
