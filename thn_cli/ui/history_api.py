# thn_cli/ui/history_api.py
"""
THN GUI API – Unified Sync History (Read-Only)
---------------------------------------------

Responsibilities:
    - Provide a GUI-facing, read-only API for unified sync history.
    - Return the exact unified history payload produced by the core read model.
    - Perform no inference, mutation, or reconciliation.

Non-goals:
    - No rendering
    - No formatting
    - No policy enforcement
    - No strict-mode evaluation
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from thn_cli.syncv2.history_read import read_unified_history
from thn_cli.txlog.history_reader import HistoryQuery


def get_unified_history(
    *,
    scaffold_root: Optional[str] = None,
    limit: int = 50,
    target: Optional[str] = None,
    tx_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    GUI-facing unified history read.

    This function is JSON-only and read-only by contract.
    """

    root_path = Path(scaffold_root).expanduser() if scaffold_root else None

    query = HistoryQuery(
        limit=int(limit),
        target=str(target) if target else None,
        tx_id=str(tx_id) if tx_id else None,
    )

    return read_unified_history(
        scaffold_root=root_path,
        txlog_query=query,
    )
