# thn_cli/cli_structure_verify.py
"""
THN CLI Structure Verifier (Hybrid-Standard)
===========================================

Purpose
-------
Validate that the THN CLI directory structure contains the minimum
required components for correct operation. This module can be invoked:

    • As a library (programmatic check)
    • As a CLI utility (`python -m thn_cli.cli_structure_verify`)
    • As part of future THN automated diagnostics

Hybrid-Standard Guarantees
--------------------------
• No unhandled exceptions
• Machine-readable return structure
• Clear separation between *verification* and *presentation*
• Forward-compatible contract for CI, diagnostics, and UI integration
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = r"C:\THN\core\cli\thn_cli"

REQUIRED = [
    "commands",
    "routing",
    "ui",
    "hub",
    "plugins",
    "tasks",
    "blueprints",
    "__init__.py",
    "__main__.py",
    "pathing.py",
    "command_loader.py",
]


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _walk(root: str) -> List[str]:
    """
    Recursively list all files and folders under `root`,
    returning paths relative to the root.
    """
    results: List[str] = []
    for base, dirs, files in os.walk(root):
        for d in dirs:
            rel = os.path.relpath(os.path.join(base, d), root)
            results.append(rel)
        for f in files:
            rel = os.path.relpath(os.path.join(base, f), root)
            results.append(rel)
    return results


def _resolve_presence(existing: List[str]) -> Tuple[List[str], List[str]]:
    """
    Compare REQUIRED list against the filesystem.
    Returns:
        (present, missing)
    """
    present = []
    missing = []

    for req in REQUIRED:
        if any(path.endswith(req) for path in existing):
            present.append(req)
        else:
            missing.append(req)

    return present, missing


def _compute_extras(existing: List[str]) -> List[str]:
    """
    Any file/folder not explicitly listed in REQUIRED is considered "extra".
    This does *not* mean it's invalid — only that it's not part of the
    minimal guaranteed structure.
    """
    required_names = {os.path.basename(r) for r in REQUIRED}
    extras = []

    for item in existing:
        name = os.path.basename(item)
        if name not in required_names:
            extras.append(item)

    return extras


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def verify_structure(root: str = ROOT) -> Dict[str, Any]:
    """
    Perform a Hybrid-Standard structure check.

    Returns normalized diagnostics:
        {
            "root": "<str>",
            "present": [...],
            "missing": [...],
            "extras": [...],
            "success": bool
        }
    """
    try:
        existing = _walk(root)
        present, missing = _resolve_presence(existing)
        extras = _compute_extras(existing)

        return {
            "root": root,
            "present": present,
            "missing": missing,
            "extras": extras,
            "success": len(missing) == 0,
        }

    except Exception as exc:
        # Hybrid-Standard: never raise, always return structured failure.
        return {
            "root": root,
            "present": [],
            "missing": REQUIRED,
            "extras": [],
            "success": False,
            "error": f"Verification failed: {exc}",
        }


# ---------------------------------------------------------------------------
# Script Entry Point
# ---------------------------------------------------------------------------


def _print_report(report: Dict[str, Any]) -> None:
    """
    Human-readable output for standalone execution.
    """
    print("\nTHN CLI Structure Verification\n")

    print("Required items present:")
    for item in report.get("present", []):
        print(f"  ✔ {item}")

    print("\nMissing items:")
    missing = report.get("missing", [])
    if missing:
        for item in missing:
            print(f"  ✘ {item}")
    else:
        print("  None")

    print("\nExtra files/folders:")
    for item in report.get("extras", []):
        print(f"  • {item}")

    print("\nSuccess:" if report["success"] else "\nFailure:", report["success"])
    print("\nDone.\n")


def main() -> None:
    """
    Standalone script execution.

    Supports:
        • Human-readable report
        • Optional JSON mode: set env THN_JSON=1
    """
    report = verify_structure(ROOT)

    if os.environ.get("THN_JSON") == "1":
        print(json.dumps(report, indent=2))
    else:
        _print_report(report)


if __name__ == "__main__":
    main()
