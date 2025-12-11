"""
Environment Diagnostics
-----------------------

Performs core environment checks required by THN CLI, including:

    • Python version validation
    • OS identification
    • THN root directory presence
    • Required subsystem folder existence
    • Basic PATH / environment-variable inspection

Outputs a DiagnosticResult object ensuring Hybrid-Standard schema compliance.
"""

from __future__ import annotations

import os
import sys
import platform
from typing import Any, Dict

from .diagnostic_result import DiagnosticResult
from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _python_version_ok() -> bool:
    """Return True if Python meets THN minimum version requirement."""
    major, minor = sys.version_info[:2]
    return major >= 3 and minor >= 10   # THN requires ≥ Python 3.10


def _gather_env_details(paths: Dict[str, str]) -> Dict[str, Any]:
    """Return a dictionary of environment details for diagnostic output."""
    return {
        "python_version": platform.python_version(),
        "executable": sys.executable,
        "os": platform.system(),
        "os_release": platform.release(),
        "cwd": os.getcwd(),
        "thn_paths": paths,
        "path_entry_count": len(os.getenv("PATH", "").split(os.pathsep)),
    }


def _required_paths_missing(paths: Dict[str, str]) -> Dict[str, bool]:
    """
    Determine which required THN folders are missing.
    Returns: { path: exists_bool }
    """
    return {name: os.path.exists(path) for name, path in paths.items()}


# ---------------------------------------------------------------------------
# Main Diagnostic
# ---------------------------------------------------------------------------

def run_env_diagnostic() -> Dict[str, Any]:
    """
    Perform environment validation and return a Hybrid-Standard diagnostic dict.

    This function must NOT print — the suite and CLI handle presentation.
    """

    paths = get_thn_paths()
    details = _gather_env_details(paths)

    errors = []
    warnings = []

    # Python validation
    if not _python_version_ok():
        errors.append("Python version is below the required minimum: 3.10")

    # Required paths
    existence_map = _required_paths_missing(paths)
    missing = [name for name, exists in existence_map.items() if not exists]
    details["path_exists"] = existence_map

    if missing:
        errors.append(f"Missing required THN paths: {', '.join(missing)}")

    # OS warnings (not errors)
    os_name = platform.system().lower()
    if os_name not in ("windows", "linux", "darwin"):
        warnings.append(f"Unrecognized OS '{platform.system()}'; behavior may vary.")

    # Final result
    ok = not errors
    return DiagnosticResult(
        component="environment",
        ok=ok,
        details=details,
        errors=errors,
        warnings=warnings,
    ).as_dict()
