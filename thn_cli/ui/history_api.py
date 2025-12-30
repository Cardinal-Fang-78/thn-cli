# thn_cli/ui/history_api.py
"""
THN GUI API – Unified Sync History (Read-Only)
---------------------------------------------

AUTHORITATIVE BOUNDARY
----------------------
This module defines the *only* supported GUI-facing API for unified
sync history.

It is explicitly:
    - Read-only
    - Non-authoritative
    - Non-enforcing
    - Policy-agnostic

The CLI and core engines remain the sole authoritative executors.
GUI consumers MUST NOT infer strictness, validation, or enforcement
semantics from this API.

RESPONSIBILITIES
----------------
• Provide a stable, JSON-only interface for unified sync history
• Delegate all logic to authoritative read models
• Perform minimal, deterministic input normalization
• Preserve payload shape exactly as returned by the core reader

NON-GOALS
---------
• No mutation
• No formatting
• No filtering beyond delegated query parameters
• No strict-mode evaluation
• No inference or reconciliation
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
    # --- GUI-only forward extension point (unused by design) ---
    _gui_context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    GUI-facing unified history read.

    Contract:
        • JSON-safe return value only
        • Read-only
        • Deterministic
        • No side effects

    Parameters beyond those defined here MUST NOT be inferred
    or assumed by consumers.
    """

    # --- deterministic input normalization ---
    root_path = Path(scaffold_root).expanduser().resolve() if scaffold_root else None

    query = HistoryQuery(
        limit=int(limit),
        target=str(target) if target is not None else None,
        tx_id=str(tx_id) if tx_id is not None else None,
    )

    # --- delegation to authoritative read model ---
    return read_unified_history(
        scaffold_root=root_path,
        txlog_query=query,
    )
