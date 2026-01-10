from __future__ import annotations

import json
import os
from typing import Any, Dict

from thn_cli.contracts.dev.goldens import inspect_golden_env
from thn_cli.diagnostics.diagnostic_result import DiagnosticCategory, DiagnosticResult

# ---------------------------------------------------------------------------
# Dev diagnostics (read-only, deterministic)
# ---------------------------------------------------------------------------


def _resolve_debug_flags() -> Dict[str, Any]:
    """
    Resolve debug / trace flags according to canonical THN rules.
    Mirrors thn_cli.__main__._debug_enabled without side effects.
    """
    env = {
        "THN_CLI_DEBUG": os.getenv("THN_CLI_DEBUG"),
        "THN_CLI_TRACE": os.getenv("THN_CLI_TRACE"),
        "THN_TRACE": os.getenv("THN_TRACE"),
    }

    enabled = env["THN_CLI_DEBUG"] == "1" or env["THN_CLI_TRACE"] == "1" or env["THN_TRACE"] == "1"

    source = None
    for key in ("THN_CLI_DEBUG", "THN_CLI_TRACE", "THN_TRACE"):
        if env[key] == "1":
            source = key
            break

    warnings = []
    if source and sum(v == "1" for v in env.values()) > 1:
        warnings.append("Multiple debug/trace flags are set. " f"'{source}' is taking precedence.")

    return {
        "enabled": enabled,
        "source": source,
        "env": env,
        "warnings": warnings,
    }


def _resolve_verbose_flag() -> Dict[str, Any]:
    val = os.getenv("THN_CLI_VERBOSE")
    return {
        "enabled": bool(val),
        "env": {"THN_CLI_VERBOSE": val},
    }


def diagnose_dev() -> DiagnosticResult:
    """
    Return a deterministic developer diagnostics result.

    This diagnostic is observational only:
    - No mutation
    - No validation
    - No enforcement
    """
    debug = _resolve_debug_flags()
    verbose = _resolve_verbose_flag()
    golden = json.loads(inspect_golden_env())

    warnings = []
    warnings.extend(debug.get("warnings", []))
    warnings.extend(golden.get("warnings", []))

    return DiagnosticResult(
        component="dev_diag",
        ok=True,
        category=DiagnosticCategory.ENVIRONMENT,
        details={
            "execution_status": "diagnostic_completed",
            "debug": debug,
            "verbose": verbose,
            "golden": golden,
        },
        warnings=warnings,
        errors=[],
    )
