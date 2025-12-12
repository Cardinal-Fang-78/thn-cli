"""
UI Diagnostic
-------------

Evaluates the THN UI subsystem:

    • UI availability
    • launcher behavior
    • API status response
    • missing configuration
    • runtime failures

Produces a Hybrid-Standard DiagnosticResult structure consistent with
all other diagnostics.
"""

from __future__ import annotations

from typing import Any, Dict, List

from thn_cli.ui.ui_api import get_ui_status
from thn_cli.ui.ui_launcher import launch_ui

from .diagnostic_result import DiagnosticResult

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_status_payload(status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the structure returned by get_ui_status().

    Expected structure:
        {
            "ready": bool,
            "details": {...},
            "warnings": [...optional...]
        }
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(status, dict):
        return {
            "ok": False,
            "errors": ["UI status payload is not a dictionary."],
            "warnings": [],
        }

    if "ready" not in status:
        errors.append("Missing required field 'ready'.")
    elif not isinstance(status["ready"], bool):
        errors.append("'ready' must be a boolean.")

    # Optional metadata
    if "warnings" in status and not isinstance(status["warnings"], list):
        warnings.append("UI status 'warnings' field is not a list.")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _test_launcher() -> Dict[str, Any]:
    """
    Run launch_ui() in 'test-only' mode (launcher itself should handle dry-run).

    Returns structure:
        {
            "ok": bool,
            "result": {...},
            "errors": [...]
        }
    """
    errors: List[str] = []

    try:
        res = launch_ui()
    except Exception as exc:
        return {
            "ok": False,
            "result": None,
            "errors": [f"Exception during UI launcher execution: {exc}"],
        }

    if not isinstance(res, dict):
        errors.append("UI launcher returned unsupported payload (expected dict).")
        return {
            "ok": False,
            "result": res,
            "errors": errors,
        }

    # Check minimal expected fields
    if "status" not in res:
        errors.append("UI launcher result missing required field 'status'.")

    return {
        "ok": not errors,
        "result": res,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Public Diagnostic
# ---------------------------------------------------------------------------


def diagnose_ui() -> Dict[str, Any]:
    """
    Hybrid-standard UI diagnostic.

    Produces a DiagnosticResult with:

        • status validation
        • launcher verification
        • collected errors and warnings
        • raw detail fields for UI panels
    """
    # Gather status from API
    try:
        ui_status = get_ui_status()
    except Exception as exc:
        return DiagnosticResult(
            component="ui",
            ok=False,
            errors=[f"Exception during get_ui_status(): {exc}"],
            details={"exception": str(exc)},
        ).as_dict()

    status_check = _validate_status_payload(ui_status)

    # Launcher dry-run test
    launcher_check = _test_launcher()

    errors: List[str] = []
    warnings: List[str] = []

    # Aggregate validation errors
    if not status_check["ok"]:
        errors.extend(status_check["errors"])
    if status_check["warnings"]:
        warnings.extend(status_check["warnings"])

    if not launcher_check["ok"]:
        errors.extend(launcher_check["errors"])

    # UI readiness hint
    if isinstance(ui_status, dict) and ui_status.get("ready") is False:
        warnings.append("UI reports not ready; launch may be partial or unavailable.")

    ok = not errors

    details = {
        "ui_status_raw": ui_status,
        "ui_status_validation": status_check,
        "launcher_result": launcher_check,
    }

    return DiagnosticResult(
        component="ui",
        ok=ok,
        details=details,
        warnings=warnings,
        errors=errors,
    ).as_dict()
