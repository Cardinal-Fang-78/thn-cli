from __future__ import annotations

"""
Scaffold Drift Event Log (Diagnostic Telemetry, Hybrid-Standard)
===============================================================

RESPONSIBILITIES
----------------
Provide a lightweight, append-only event log for scaffold drift activity.

This module:
    • Maintains a per-scaffold JSON log file
    • Records chronological drift-related events
    • Preserves historical context for diagnostics and audit
    • Operates independently of enforcement or verification logic

Log file:
    <scaffold>/.thn-drift-log.json

CONTRACT STATUS
---------------
⚠️ DIAGNOSTIC WRITE-SIDE — NON-AUTHORITATIVE

The drift log:
    • Does NOT determine scaffold correctness
    • Does NOT affect drift classification
    • Does NOT gate accept/migrate/apply flows
    • Is safe to delete without affecting scaffold behavior

All entries are advisory and informational only.

DATA MODEL GUARANTEES
---------------------
    • Append-only semantics (no mutation of past events)
    • Best-effort durability (no transactional guarantees)
    • Human-readable JSON
    • Forward-compatible schema via versioning

NON-GOALS
---------
• This module is NOT a source of truth
• This module is NOT a reconciliation engine
• This module does NOT validate events
• This module does NOT enforce ordering or uniqueness

Higher-level tooling may consume this log for display or audit purposes,
but must never rely on it for correctness.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

LOG_NAME = ".thn-drift-log.json"


def _now_utc() -> str:
    """
    Return current UTC time in ISO-8601 Z format.
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_or_init_log(root: Path, blueprint: Dict[str, str]) -> Dict[str, Any]:
    """
    Load the existing drift log or initialize a new one.

    Failure modes:
        • Malformed or missing logs result in a fresh log
        • No exceptions are raised to callers
    """
    path = root / LOG_NAME
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass  # fall through to fresh init

    return {
        "schema_version": 1,
        "scaffold": {
            "path": str(root),
            "blueprint": blueprint,
        },
        "events": [],
    }


def append_event(root: Path, blueprint: Dict[str, str], event: Dict[str, Any]) -> None:
    """
    Append a drift-related event to the scaffold log.

    This function:
        • Loads or initializes the log
        • Appends the event verbatim
        • Writes the updated log atomically (best-effort)

    Event structure is intentionally unconstrained to allow evolution.
    """
    log = load_or_init_log(root, blueprint)
    log["events"].append(event)

    path = root / LOG_NAME
    path.write_text(json.dumps(log, indent=2), encoding="utf-8")
