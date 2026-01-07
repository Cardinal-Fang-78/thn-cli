# thn_cli/diagnostics/suite.py
"""
THN Diagnostics Suite
---------------------

Provides the authoritative orchestration layer for THN diagnostics.

Each diagnostic module returns a dict of the form:

    {
        "ok": bool,
        "component": "name",
        "category": "environment|filesystem|registry|routing|plugins|tasks|ui|hub|sanity|unknown",  # optional
        "details": {...},      # optional
        "errors": [...],       # optional
        "warnings": [...],     # optional
    }

This suite is responsible ONLY for:
    • Executing diagnostics in a safe, deterministic order
    • Normalizing results via DiagnosticResult
    • Aggregating outputs without interpretation

The suite does NOT:
    • Interpret correctness
    • Infer system health
    • Enforce policy
    • Compute summaries
    • Add timestamps or versions

Notes
-----
- "ok" reflects diagnostic execution success only
- Category is diagnostic-only metadata
- No inference or aggregation semantics are applied here
- All schema guarantees are enforced by DiagnosticResult
"""

from __future__ import annotations

from typing import List

from thn_cli.diagnostics.diagnostic_result import DiagnosticResult

from .env_diag import diagnose_env
from .hub_diag import diagnose_hub
from .paths_diag import diagnose_paths
from .plugins_diag import diagnose_plugins
from .registry_diag import diagnose_registry
from .routing_diag import diagnose_routing
from .sanity_diag import run_sanity
from .tasks_diag import diagnose_tasks
from .ui_diag import diagnose_ui

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_full_suite() -> dict:
    """
    Run ALL diagnostics in dependency-safe order.

    Ordered to prevent cascade errors:
        1. env → filesystem → registry → routing → plugins → tasks → ui → hub → sanity

    Semantics:
    - ok = True  → all diagnostics executed successfully
    - ok = False → at least one diagnostic failed to execute

    This does NOT indicate system correctness.
    """

    diagnostics: List[DiagnosticResult] = []

    try:
        diagnostics.append(DiagnosticResult.from_raw(diagnose_env()))
        diagnostics.append(DiagnosticResult.from_raw(diagnose_paths()))
        diagnostics.append(DiagnosticResult.from_raw(diagnose_registry()))
        diagnostics.append(DiagnosticResult.from_raw(diagnose_routing()))
        diagnostics.append(DiagnosticResult.from_raw(diagnose_plugins()))
        diagnostics.append(DiagnosticResult.from_raw(diagnose_tasks()))
        diagnostics.append(DiagnosticResult.from_raw(diagnose_ui()))
        diagnostics.append(DiagnosticResult.from_raw(diagnose_hub()))
        diagnostics.append(DiagnosticResult.from_raw(run_sanity()))
    except Exception:
        return {
            "ok": False,
            "diagnostics": [],
            "errors": ["Diagnostic suite execution failed"],
            "warnings": [],
        }

    errors = []
    warnings = []

    for d in diagnostics:
        errors.extend(d.errors)
        warnings.extend(d.warnings)

    return {
        "ok": True,
        "diagnostics": [d.as_dict() for d in diagnostics],
        "errors": errors,
        "warnings": warnings,
    }
