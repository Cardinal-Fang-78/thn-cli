"""
THN Sync V2 Status DB Read Surface
---------------------------------

Responsibilities:
    - Reserve the Status DB read interface
    - Provide a stable, read-only diagnostic entry point

Non-goals:
    - No joins with TXLOG
    - No inference or reconstruction
    - No execution coupling
"""

from __future__ import annotations

from typing import Any, Dict

from thn_cli.syncv2 import status_db


def read_status_db_stub() -> Dict[str, Any]:
    """
    Read-only diagnostic stub for Status DB access.

    This function intentionally does not read from the database yet.
    It exists to lock naming, intent, and call shape.
    """
    return {
        "status": "not_implemented",
        "scope": "diagnostic",
        "authority": "status_db",
        "message": "Status DB read surface stub placeholder",
    }


def read_status_db() -> Dict[str, Any]:
    """
    Real Status DB read surface (NOT YET EXPOSED VIA CLI).

    Best-effort, non-throwing, read-only.
    """
    try:
        record = status_db.load_latest_status()
    except Exception:
        return {
            "present": False,
            "record": None,
        }

    if not record:
        return {
            "present": False,
            "record": None,
        }

    return {
        "present": True,
        "record": record,
    }
