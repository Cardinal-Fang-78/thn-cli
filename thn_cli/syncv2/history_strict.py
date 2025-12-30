# thn_cli/syncv2/history_strict.py
"""
THN Sync V2 – Unified History Strict Diagnostics (Read-Only)
============================================================

RESPONSIBILITIES
----------------
Provides strict, read-only diagnostics over the unified sync history payload.

This module:
    - Evaluates invariants and structural expectations
    - Emits diagnostic annotations only
    - NEVER mutates history data
    - NEVER raises to enforce policy
    - NEVER alters exit codes

Strict mode is explicitly opt-in and diagnostic-only.

INVARIANTS
----------
• Input payload MUST remain unchanged
• Output diagnostics MUST be deterministic
• Ordering MUST be stable
• No side effects
• No filesystem writes

CONTRACT STATUS
---------------
Read-only diagnostic layer.
Safe for CLI use and future GUI consumption.

NON-GOALS
---------
• No enforcement
• No filtering
• No mutation
• No recovery
• No policy decisions
"""

from __future__ import annotations

from typing import Any, Dict, List


def evaluate_strict_diagnostics(history: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate strict diagnostics for a unified history payload.

    Returns a diagnostic block only. Caller is responsible for attaching it.
    """

    violations: List[Dict[str, Any]] = []

    entries = history.get("entries", [])
    if not isinstance(entries, list):
        violations.append(
            {
                "code": "HISTORY_ENTRIES_INVALID",
                "severity": "error",
                "message": "Unified history entries field is missing or invalid",
                "tx_id": None,
            }
        )
        return _finalize(violations)

    for entry in entries:
        tx_id = entry.get("tx_id")

        if not tx_id:
            violations.append(
                {
                    "code": "TX_ID_MISSING",
                    "severity": "warning",
                    "message": "History entry missing tx_id",
                    "tx_id": None,
                }
            )

        if entry.get("integrity") == "partial":
            violations.append(
                {
                    "code": "TXLOG_INCOMPLETE",
                    "severity": "warning",
                    "message": "Transaction record is incomplete",
                    "tx_id": tx_id,
                }
            )

        if "timestamp" not in entry:
            violations.append(
                {
                    "code": "TIMESTAMP_MISSING",
                    "severity": "warning",
                    "message": "History entry missing timestamp",
                    "tx_id": tx_id,
                }
            )

    return _finalize(violations)


def _finalize(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Finalize strict diagnostics block with deterministic ordering.
    """

    status = "ok"
    if any(v["severity"] == "error" for v in violations):
        status = "error"
    elif violations:
        status = "warning"

    # Deterministic ordering
    violations_sorted = sorted(
        violations,
        key=lambda v: (
            v["severity"],
            v["code"],
            str(v.get("tx_id") or ""),
        ),
    )

    return {
        "status": status,
        "violations": violations_sorted,
    }
