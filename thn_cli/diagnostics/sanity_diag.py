"""
sanity_diag.py  (Hybrid-Standard)
--------------------------------

Master, system-wide THN CLI diagnostic.

Runs every major subsystem diagnostic:

    • env_diag
    • paths_diag
    • registry_diag
    • plugins_diag
    • routing_diag
    • tasks_diag
    • ui_diag
    • indent_diag / indent_extended
    • syncv2 sanity: envelope validation, state DB checks

Produces a single structured Hybrid-Standard report.

Zero mutations. Zero writes.
"""

from __future__ import annotations

import traceback
from typing import Dict, Any

from thn_cli.diagnostics.env_diag import diagnose_environment
from thn_cli.diagnostics.paths_diag import diagnose_paths
from thn_cli.diagnostics.registry_diag import diagnose_registry
from thn_cli.diagnostics.plugins_diag import diagnose_plugins
from thn_cli.diagnostics.routing_diag import diagnose_routing
from thn_cli.diagnostics.tasks_diag import diagnose_tasks
from thn_cli.diagnostics.ui_diag import diagnose_ui
from thn_cli.diagnostics.indent_diag import diagnose_indent
from thn_cli.diagnostics.indent_extended import diagnose_indent_extended

# SyncV2 diagnostics
from thn_cli.syncv2.state import load_state_safe
from thn_cli.syncv2.status_db import test_status_db_read


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_run(name: str, func) -> Dict[str, Any]:
    """
    Run a diagnostic component safely.
    Never raises. Always returns { ok, error, result }.
    """
    try:
        result = func()
        return {"ok": True, "error": None, "result": result}
    except Exception as exc:
        return {
            "ok": False,
            "error": traceback.format_exc(),
            "result": None,
        }


def _syncv2_sanity() -> Dict[str, Any]:
    """
    Read-only SyncV2 health assessment:
        • state file loadability
        • status DB readability
    """
    try:
        state_info = load_state_safe()
    except Exception:
        state_info = {"ok": False, "error": traceback.format_exc()}

    try:
        status_info = test_status_db_read()
    except Exception:
        status_info = {"ok": False, "error": traceback.format_exc()}

    return {
        "state": state_info,
        "status_db": status_info,
    }


# ---------------------------------------------------------------------------
# Master Diagnostic
# ---------------------------------------------------------------------------

def diagnose_sanity() -> Dict[str, Any]:
    """
    Perform the master system-wide diagnostic.
    """

    env_info     = _safe_run("environment", diagnose_environment)
    paths_info   = _safe_run("paths", diagnose_paths)
    registry_info = _safe_run("registry", diagnose_registry)
    plugins_info  = _safe_run("plugins", diagnose_plugins)
    routing_info  = _safe_run("routing", diagnose_routing)
    tasks_info    = _safe_run("tasks", diagnose_tasks)
    ui_info       = _safe_run("ui", diagnose_ui)
    indent_info   = _safe_run("indent", diagnose_indent)
    indent_ext    = _safe_run("indent_extended", diagnose_indent_extended)

    syncv2_info   = _safe_run("syncv2_sanity", _syncv2_sanity)

    # Composite validity
    valid = (
        env_info["ok"]
        and paths_info["ok"]
        and registry_info["ok"]
        and plugins_info["ok"]
        and routing_info["ok"]
        and tasks_info["ok"]
        and ui_info["ok"]
        and indent_info["ok"]
        and indent_ext["ok"]
        and syncv2_info["ok"]
    )

    summary = "THN CLI subsystem appears healthy." if valid else "Issues detected in THN CLI."

    return {
        "summary": summary,
        "valid": valid,

        "environment": env_info,
        "paths": paths_info,
        "registry": registry_info,
        "plugins": plugins_info,
        "routing": routing_info,
        "tasks": tasks_info,
        "ui": ui_info,
        "indent": indent_info,
        "indent_extended": indent_ext,
        "syncv2": syncv2_info,

        "hybrid_standard": True,
    }
