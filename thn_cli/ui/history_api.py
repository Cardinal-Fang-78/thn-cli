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
• Apply presentation-only ordering & pagination
• Preserve payload shape exactly as returned by the core reader

NON-GOALS
---------
• No mutation of authoritative data
• No formatting
• No filtering beyond delegated query parameters
• No strict-mode evaluation
• No inference or reconciliation
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from thn_cli.syncv2.history_read import read_unified_history
from thn_cli.txlog.history_reader import HistoryQuery


def _parse_observed_at(value: Any) -> Optional[datetime]:
    """
    Best-effort parser for observed_at.
    Accepts ISO-8601 strings; returns None if unavailable or invalid.
    """
    if not value or not isinstance(value, str):
        return None
    try:
        # Accepts 'YYYY-MM-DDTHH:MM:SS(.ffffff)(Z|±HH:MM)'
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _stable_order_entries(
    entries: Iterable[Dict[str, Any]],
    *,
    order: str,
) -> List[Dict[str, Any]]:
    """
    Presentation-only, stable ordering.

    Ordering key:
        1) observed_at (preferred; parsed)
        2) original position (stable fallback)

    order:
        - "desc": newest -> oldest (default)
        - "asc":  oldest -> newest
    """
    indexed: List[Tuple[int, Dict[str, Any]]] = list(enumerate(entries))

    def sort_key(item: Tuple[int, Dict[str, Any]]):
        idx, entry = item
        ts = _parse_observed_at(entry.get("observed_at"))
        # None timestamps sort last for desc, first for asc via sentinel
        if ts is None:
            return (0, idx) if order == "desc" else (1, idx)
        # Use epoch seconds for total ordering
        return (1, ts.timestamp(), idx) if order == "desc" else (0, ts.timestamp(), idx)

    # Python sort is stable; include idx to guarantee stability
    reverse = False  # handled in key to keep stability explicit
    ordered = sorted(indexed, key=sort_key, reverse=reverse)

    # For desc, newer first: keys are constructed accordingly
    return [entry for _, entry in ordered]


def _paginate(
    entries: List[Dict[str, Any]],
    *,
    offset: int,
    limit: int,
) -> List[Dict[str, Any]]:
    if offset < 0:
        offset = 0
    if limit <= 0:
        return []
    return entries[offset : offset + limit]


def get_unified_history(
    *,
    scaffold_root: Optional[str] = None,
    limit: int = 50,
    target: Optional[str] = None,
    tx_id: Optional[str] = None,
    # --- Presentation-only controls ---
    order: str = "desc",  # "desc" (default) | "asc"
    offset: int = 0,
    # --- GUI-only forward extension point (unused by design) ---
    _gui_context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    GUI-facing unified history read.

    Contract:
        • JSON-safe return value only
        • Read-only
        • Deterministic for identical inputs
        • No side effects

    Ordering & pagination are presentation-only and MUST NOT
    be inferred as authoritative semantics.
    """

    # --- deterministic input normalization ---
    root_path = Path(scaffold_root).expanduser().resolve() if scaffold_root else None

    normalized_order = order.lower().strip()
    if normalized_order not in {"asc", "desc"}:
        normalized_order = "desc"

    query = HistoryQuery(
        limit=int(limit),
        target=str(target) if target is not None else None,
        tx_id=str(tx_id) if tx_id is not None else None,
    )

    # --- delegation to authoritative read model ---
    result = read_unified_history(
        scaffold_root=root_path,
        txlog_query=query,
    )

    # --- presentation-only ordering & pagination ---
    history = result.get("history")
    if isinstance(history, dict) and isinstance(history.get("entries"), list):
        entries = history.get("entries", [])
        ordered = _stable_order_entries(entries, order=normalized_order)
        paged = _paginate(ordered, offset=int(offset), limit=int(limit))

        # Preserve shape; do not mutate original list in-place
        history["entries"] = paged
        history["count"] = len(paged)

        # Optional presentation notes (non-authoritative)
        notes = history.get("notes")
        if isinstance(notes, list):
            notes.append(
                f"presentation: order={normalized_order}, offset={int(offset)}, limit={int(limit)}"
            )

    return result
