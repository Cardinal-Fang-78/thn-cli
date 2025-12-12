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


def run_hub_diagnostic() -> Dict[str, Any]:
    """
    Execute Hub subsystem checks and return a Hybrid-Standard diagnostic dict.
    Must NOT print. CLI and suite handle presentation.
    """

    errors = []
    warnings = []

    try:
        status = get_hub_status() or {}
    except Exception as exc:
        # Hard failure → cannot proceed
        return DiagnosticResult(
            component="hub",
            ok=False,
            details={"exception": str(exc)},
            errors=[f"Hub status retrieval failed: {exc}"],
            warnings=[],
        ).as_dict()

    # Expected schema (minimal)
    expected_keys = {"online", "version", "message"}

    missing = [k for k in expected_keys if k not in status]
    if missing:
        warnings.append(f"Hub status missing expected fields: {', '.join(missing)}")

    # Evaluate online/offline
    online = bool(status.get("online", False))
    message = status.get("message", "")

    if not online:
        warnings.append("Hub reports offline or unreachable.")
        if message:
            warnings.append(f"Hub message: {message}")

    # Determine pass/fail
    ok = online and not errors  # warnings do not make it fail

    return DiagnosticResult(
        component="hub",
        ok=ok,
        details=status,
        errors=errors,
        warnings=warnings,
    ).as_dict()


# ---------------------------------------------------------------------------
# Compatibility stub required until full hub diagnostics are implemented
# ---------------------------------------------------------------------------


def diagnose_hub() -> dict:
    """
    Placeholder hub diagnostic.
    Exists solely so imports succeed during test collection.
    """
    return {
        "status": "not_implemented",
        "message": "diagnose_hub placeholder",
    }
