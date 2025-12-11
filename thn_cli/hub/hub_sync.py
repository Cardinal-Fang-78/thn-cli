"""
THN Hub Sync Module
-------------------

Provides a Hybrid-Standard interface for performing Hub-related sync
operations. This includes:

    • local → hub push handshake simulation
    • hub → local pull simulation (future)
    • registry updates for sync metadata
    • consistent DiagnosticResult wrapping

This module intentionally implements *no network calls* yet.
Instead, it provides stable, testable sync semantics that higher-level
remote negotiation layers can extend.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Any, Optional

from thn_cli.diagnostics.diagnostic_result import DiagnosticResult
from thn_cli.registry import load_registry, save_registry
from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _sleep_min(delay: float) -> None:
    """
    Minimal artificial delay to simulate negotiation.
    Ensures consistent testing without real network operations.
    """
    time.sleep(max(0.05, delay))


def _update_registry_after_sync(paths: Dict[str, str], *, success: bool) -> None:
    """
    Update registry hub metadata after sync attempt.
    """
    reg = load_registry(paths)
    hub = reg.setdefault("hub", {})

    hub["last_sync"] = _ts_now()
    hub["connected"] = success

    save_registry(paths, reg)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def perform_hub_sync() -> Dict[str, Any]:
    """
    Perform a Hybrid-Standard mock Hub sync operation.

    Returns:
        DiagnosticResult.as_dict(), containing:
            • ok / warnings / errors
            • timestamps
            • simulated negotiation stages
            • summary block
            • registry-updated status
    """

    paths = get_thn_paths()

    # --------------------------------------------------------
    # Stage 1: handshake
    # --------------------------------------------------------
    _sleep_min(0.10)
    handshake_ok = True   # placeholder for future real logic

    warnings = []
    errors = []

    if not handshake_ok:
        errors.append("Hub handshake failed.")
        overall_ok = False
    else:
        overall_ok = True

    # --------------------------------------------------------
    # Stage 2: simulated metadata exchange
    # --------------------------------------------------------
    _sleep_min(0.10)
    remote_version = "1.0.0-mock"
    capabilities = ["sync", "status", "mock-endpoint"]

    # --------------------------------------------------------
    # Stage 3: registry update
    # --------------------------------------------------------
    _update_registry_after_sync(paths, success=overall_ok)

    # --------------------------------------------------------
    # Build result details
    # --------------------------------------------------------
    details = {
        "timestamp": _ts_now(),
        "handshake": {
            "performed": True,
            "ok": handshake_ok,
        },
        "exchange": {
            "remote_version": remote_version,
            "capabilities": capabilities,
        },
        "summary": {
            "sync_completed": overall_ok,
            "registry_updated": True,
        },
    }

    return DiagnosticResult(
        component="hub_sync",
        ok=overall_ok,
        warnings=warnings,
        errors=errors,
        details=details,
    ).as_dict()
