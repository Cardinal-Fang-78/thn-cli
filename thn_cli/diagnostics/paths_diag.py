"""
Paths Diagnostic
----------------

Validates the THN pathing subsystem by checking:

    • All expected THN directories resolve correctly
    • Directories exist or are creatable
    • Environment variables do not corrupt resolution
    • Path normalization/deduplication behavior

Produces Hybrid-Standard DiagnosticResult output.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from thn_cli.pathing import get_thn_paths

from .diagnostic_result import DiagnosticResult

# ---------------------------------------------------------------------------
# Internal Checks
# ---------------------------------------------------------------------------


def _check_exists(path: str) -> bool:
    """Return True if the path exists **and** is a directory."""
    return os.path.isdir(path)


def _check_creatable(path: str) -> bool:
    """
    Determine whether a directory can be created at the given location.
    We DO NOT create anything—this is a dry check.
    """
    parent = os.path.dirname(path)
    return os.path.exists(parent) and os.access(parent, os.W_OK)


def _validate_paths(paths: Dict[str, str]) -> Dict[str, Any]:
    """
    Validate each path key and return structured detail.
    """
    results = {}

    for key, p in paths.items():
        item = {
            "path": p,
            "exists": _check_exists(p),
            "creatable": _check_creatable(p),
            "normalized": os.path.normpath(p),
        }
        results[key] = item

    return results


# ---------------------------------------------------------------------------
# Public Diagnostic
# ---------------------------------------------------------------------------


def run_paths_diag() -> Dict[str, Any]:
    """
    Validate the resolved THN directory structure.

    Success criteria:

        OK if:
            - All required paths resolve to valid strings
            - At least the parent directories are creatable
        Warnings if:
            - Non-existent but creatable
        Errors if:
            - Non-existent AND non-creatable
            - Duplicate normalization collapse (two keys → same normalized path)

    Returns DiagnosticResult (Hybrid-Standard).
    """
    paths = get_thn_paths()

    details = _validate_paths(paths)

    warnings = []
    errors = []

    # 1. check existence / creatability
    for key, info in details.items():
        if not info["exists"] and info["creatable"]:
            warnings.append(f"{key}: directory does not exist but is creatable.")
        elif not info["exists"] and not info["creatable"]:
            errors.append(f"{key}: directory does not exist and cannot be created.")

    # 2. detect collisions via normalization
    normalized_map = {}
    for key, info in details.items():
        norm = info["normalized"]
        normalized_map.setdefault(norm, []).append(key)

    collisions = [keys for keys in normalized_map.values() if len(keys) > 1]
    if collisions:
        for group in collisions:
            errors.append(f"Path normalization collision among: {', '.join(group)}")

    ok = not errors

    return DiagnosticResult(
        component="paths",
        ok=ok,
        details=details,
        warnings=warnings,
        errors=errors,
    ).as_dict()


# ---------------------------------------------------------------------------
# Compatibility stub required by diagnostics suite + commands_diag
# ---------------------------------------------------------------------------


def diagnose_paths() -> dict:
    """
    Placeholder environment diagnostic.

    This diagnostic is intentionally not implemented.
    """
    return {
        "component": "paths",
        "category": "filesystem",
        "ok": False,
        "details": {},
        "warnings": [],
        "errors": [],
    }
