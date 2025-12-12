"""
THN Hub Status Module
---------------------

Provides a unified Hybrid-Standard interface for retrieving and reporting
Hub-related system status, including connectivity indicators, last sync
timestamps, and hub-side capabilities.

Used by:
    • thn hub status diagnostics
    • hub_sync workflow
    • CLI status display
    • UI diagnostic overlays
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from thn_cli.diagnostics.diagnostic_result import DiagnosticResult
from thn_cli.pathing import get_thn_paths
from thn_cli.registry import load_registry

# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _ts_now() -> str:
    """
    Return current timestamp in ISO-8601 format.
    """
    return datetime.utcnow().isoformat() + "Z"


def _safe_ts(value: Optional[str]) -> Optional[str]:
    """
    Normalize timestamp formatting; returns None if invalid.
    """
    if not value:
        return None
    try:
        # Validate parse
        return datetime.fromisoformat(value.replace("Z", "")).isoformat() + "Z"
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Status Loader
# ---------------------------------------------------------------------------


def _load_hub_status_block(paths: Dict[str, str]) -> Dict[str, Any]:
    """
    Internal helper to load hub-specific data from the registry.

    Registry format example:
        {
            "hub": {
                "connected": true,
                "last_sync": "2025-11-23T18:32:14Z",
                "capabilities": ["sync", "delta", "push"],
                "remote_version": "1.4.2"
            }
        }

    Missing keys gracefully fall back to defaults.
    """
    reg = load_registry(paths)
    hub = reg.get("hub", {})

    return {
        "connected": bool(hub.get("connected", False)),
        "last_sync": _safe_ts(hub.get("last_sync")),
        "capabilities": hub.get("capabilities", []),
        "remote_version": hub.get("remote_version"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_hub_status() -> Dict[str, Any]:
    """
    Return the Hybrid-Standard Hub status block wrapped inside
    a DiagnosticResult instance.

    Provides:
        • connection indicator
        • last sync timestamp
        • server-reported capabilities
        • remote version info
        • timestamped response metadata
    """
    paths = get_thn_paths()
    raw = _load_hub_status_block(paths)

    details = {
        "connected": raw["connected"],
        "last_sync": raw["last_sync"],
        "capabilities": list(raw["capabilities"]),
        "remote_version": raw["remote_version"],
        "timestamp": _ts_now(),
    }

    ok = raw["connected"]

    warnings = []
    if not raw["connected"]:
        warnings.append("Hub is not connected.")
    if raw["last_sync"] is None:
        warnings.append("Last sync timestamp unavailable or invalid.")

    return DiagnosticResult(
        component="hub_status",
        ok=ok,
        warnings=warnings,
        errors=[],
        details=details,
    ).as_dict()
