"""
Hub Diagnostics
---------------

Performs connectivity and configuration checks for the THN Hub / Nexus layer.

This diagnostic verifies:

    • Hub subsystem availability
    • Hub status structure shape
    • Connectivity indicators (online / offline)
    • Error reporting returned by the hub_status API

All output conforms to the Hybrid-Standard DiagnosticResult contract.
"""

from __future__ import annotations

from typing import Any, Dict

from thn_cli.hub.hub_status import get_hub_status

from .diagnostic_result import DiagnosticResult

# ---------------------------------------------------------------------------
# Main Diagnostic
# ---------------------------------------------------------------------------


def diagnose_hub() -> Dict[str, Any]:
    """
    Execute Hub subsystem checks and return a Hybrid-Standard diagnostic dict.
    Must NOT print. CLI and suite handle presentation.
    """
    errors = []
    warnings = []

    try:
        status = get_hub_status() or {}
    except Exception as exc:
        return DiagnosticResult(
            component="hub",
            ok=False,
            details={"exception": str(exc)},
            errors=[f"Hub status retrieval failed: {exc}"],
            warnings=[],
        ).as_dict()

    expected_keys = {"online", "version", "message"}
    missing = [k for k in expected_keys if k not in status]
    if missing:
        warnings.append(f"Hub status missing expected fields: {', '.join(missing)}")

    online = bool(status.get("online", False))
    message = status.get("message", "")

    if not online:
        warnings.append("Hub reports offline or unreachable.")
        if message:
            warnings.append(f"Hub message: {message}")

    ok = online

    return DiagnosticResult(
        component="hub",
        ok=ok,
        details=status,
        warnings=warnings,
        errors=errors,
    ).as_dict()
