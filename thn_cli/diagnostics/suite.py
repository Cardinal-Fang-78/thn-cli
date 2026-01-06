"""
THN Diagnostics Suite
---------------------

Provides the orchestration layer for all diagnostic modules.

Each diagnostic module returns a dict of the form:

    {
        "ok": bool,
        "component": "name",
        "details": {...},      # optional
        "errors": [...],       # optional
        "warnings": [...],     # optional
    }

This suite collects and standardizes results into a single
Hybrid-Standard diagnostic report:

    {
        "summary": {
            "passed": <int>,
            "failed": <int>,
            "total":  <int>,
        },
        "results": [ ... ],
        "timestamp": "...",
        "version": 1
    }
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .env_diag import diagnose_env
from .hub_diag import diagnose_hub
from .paths_diag import diagnose_paths
from .plugins_diag import diagnose_plugins
from .registry_diag import diagnose_registry
from .routing_diag import diagnose_routing
from .sanity_diag import run_sanity
from .tasks_diag import diagnose_tasks
from .ui_diag import diagnose_ui

_DIAGNOSTIC_VERSION = 1


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _stamp() -> str:
    """Current timestamp in ISO8601 format (seconds resolution)."""
    return datetime.now().isoformat(timespec="seconds")


def _normalize(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure required fields exist and follow the Hybrid-Standard schema.
    """
    return {
        "ok": bool(result.get("ok", False)),
        "component": result.get("component", "unknown"),
        "details": result.get("details", {}),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        # additive metadata (non-enforcing)
        "category": result.get("category"),
    }


def _collect(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build suite summary."""
    normalized = [_normalize(r) for r in results]

    passed = sum(1 for r in normalized if r["ok"])
    failed = len(normalized) - passed

    return {
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": len(normalized),
        },
        "results": normalized,
        "timestamp": _stamp(),
        "version": _DIAGNOSTIC_VERSION,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_full_suite() -> Dict[str, Any]:
    """
    Run ALL diagnostics in dependency-safe order.

    Ordered to prevent cascade errors:
        1. env → filesystem → registry → routing → plugins → tasks → ui → hub → sanity
    """

    results: List[Dict[str, Any]] = []

    # Core system & environment
    results.append(diagnose_env())
    results.append(diagnose_paths())
    results.append(diagnose_registry())

    # Routing + rules
    results.append(diagnose_routing())

    # Plugin & task subsystems
    results.append(diagnose_plugins())
    results.append(diagnose_tasks())

    # User interface + hub reachability
    results.append(diagnose_ui())
    results.append(diagnose_hub())

    # Final comprehensive check
    results.append(run_sanity())

    return _collect(results)


# ---------------------------------------------------------------------------
# Compatibility: placeholder diagnostic suite aggregator
# ---------------------------------------------------------------------------


def run_all_diagnostics() -> dict:
    """
    Placeholder aggregator used by hub_sync and commands_diag.
    Returns a minimal success structure so imports and commands load cleanly.
    """
    return {"status": "ok", "message": "run_all_diagnostics placeholder", "results": []}
