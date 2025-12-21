from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List

from thn_cli.contracts.errors import SYSTEM_CONTRACT
from thn_cli.contracts.exceptions import CommandError

# ---------------------------------------------------------------------------
# Golden env inspection (STRICT, mirrors tests/golden/_runner.py)
# ---------------------------------------------------------------------------


def _update_enabled() -> bool:
    return os.getenv("THN_UPDATE_GOLDEN") == "1"


def _validate_env() -> List[str]:
    warnings: List[str] = []

    has_singular = bool(os.getenv("THN_UPDATE_GOLDEN"))
    has_plural = bool(os.getenv("THN_UPDATE_GOLDENS"))

    if has_singular and has_plural:
        warnings.append(
            "Both THN_UPDATE_GOLDEN and THN_UPDATE_GOLDENS are set. "
            "Only THN_UPDATE_GOLDEN (singular) is valid."
        )
    elif has_plural:
        warnings.append(
            "Invalid environment variable THN_UPDATE_GOLDENS detected. "
            "Did you mean THN_UPDATE_GOLDEN?"
        )

    val = os.getenv("THN_UPDATE_GOLDEN")
    if val is not None and val != "1":
        warnings.append(f"THN_UPDATE_GOLDEN is set to '{val}', but only '1' enables updates.")

    return warnings


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def inspect_golden_env() -> str:
    """
    Return a deterministic JSON report describing golden-test mode.
    """
    report: Dict[str, Any] = {
        "golden_update_enabled": _update_enabled(),
        "env": {
            "THN_UPDATE_GOLDEN": os.getenv("THN_UPDATE_GOLDEN"),
            "THN_UPDATE_GOLDENS": os.getenv("THN_UPDATE_GOLDENS"),
        },
        "warnings": _validate_env(),
    }

    return json.dumps(report, indent=4)


def run_golden_tests() -> int:
    """
    Run pytest tests/golden with the current environment.
    Exit code is propagated verbatim.
    """
    cmd = [sys.executable, "-m", "pytest", "tests/golden"]
    print(f"Running: {' '.join(cmd)}")

    try:
        return subprocess.call(cmd)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to invoke golden test suite.",
        ) from exc
