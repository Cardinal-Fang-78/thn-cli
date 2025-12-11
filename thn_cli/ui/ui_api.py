# thn_cli/ui/ui_api.py
"""
THN UI API Layer (Hybrid-Standard)
=================================

Purpose
-------
Provides a stable forward-compatible interface between the THN CLI and
the future THN UI subsystem. This module does *not* implement any UI
logic; instead it defines the contracts and information flows that the
real UI will eventually support.

Long-term UI capabilities will include:
    • Window/process discovery
    • Panel state reporting
    • User-session metadata
    • IPC endpoints for UI-driven CLI operations
    • Health/diagnostic summaries
    • Tenant-aware UI state for THN Hub or local-only mode

Current Scope (Stub)
--------------------
The present implementation is intentionally minimal:

    get_ui_status()
        Returns a deterministic, safe placeholder structure describing
        the absence of an active UI layer.

This makes the CLI safe to use on systems *without* the UI installed
and forms a predictable base for future expansion.
"""

from __future__ import annotations

import platform
import datetime
from typing import Dict, Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_ui_status() -> Dict[str, Any]:
    """
    Return a normalized placeholder UI status object.

    This function is used by:
        • thn ui status          (future)
        • diagnostics/ui_diag.py (already hybrid-standardized)
        • THN CLI dashboard      (future)

    The returned structure is stable and forward-compatible.

    Returns:
        {
            "ui_available": bool,
            "ui_running": bool,
            "message": str,
            "platform": str,
            "timestamp": str (ISO8601),
        }
    """

    return {
        # UI subsystem is not implemented yet → guaranteed value
        "ui_available": False,
        "ui_running": False,

        # Structured explanation for both CLI + UI tooling
        "message": "THN UI subsystem not yet implemented.",

        # Platform hint: helpful for future UI routing and diagnostics
        "platform": platform.system(),

        # Precise, testable timestamp (UTC preferred in future versions)
        "timestamp": datetime.datetime.now().isoformat(),
    }
