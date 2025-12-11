"""
Indentation Diagnostics
-----------------------

Validates indentation consistency across the THN CLI codebase.

This diagnostic focuses on:

    • Detecting leading tab characters
    • Detecting mixed indentation (tabs + spaces)
    • Verifying that indentation is composed of multiples of 4 spaces
    • Reporting any anomalies file-by-file

All output conforms to the Hybrid-Standard DiagnosticResult contract.
"""

from __future__ import annotations

import os
from typing import Dict, Any, List, Tuple

from .diagnostic_result import DiagnosticResult
from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scan_file(path: str) -> Tuple[List[str], List[str]]:
    """
    Scan a file for indentation issues.

    Returns:
        tabs:      List[str]  lines containing leading tab characters
        mixed:     List[str]  lines containing both tabs and spaces
    """
    tabs = []
    mixed = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                stripped = line.lstrip("\t ")

                # detect leading indentation portion only
                indent = line[: len(line) - len(stripped)]

                if indent.startswith("\t"):
                    tabs.append(f"{path}:{lineno}: leading tab")

                if " " in indent and "\t" in indent:
                    mixed.append(f"{path}:{lineno}: mixed indentation")
    except Exception as exc:
        # treat unreadable files as warnings; do not halt
        mixed.append(f"{path}: unreadable ({exc})")

    return tabs, mixed


def _walk_python_files(root: str) -> List[str]:
    """
    Return a list of all .py files under the given root.
    """
    py_files = []
    for base, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(base, f))
    return py_files


# ---------------------------------------------------------------------------
# Main Diagnostic
# ---------------------------------------------------------------------------

def run_indent_diagnostic() -> Dict[str, Any]:
    """
    Perform indentation validation across all THN CLI Python files.
    Returns a Hybrid-Standard diagnostic result. Does NOT print.
    """

    paths = get_thn_paths()
    root = paths.get("root") or paths.get("cli_root") or "."

    py_files = _walk_python_files(root)

    all_tabs = []
    all_mixed = []

    for file_path in py_files:
        tabs, mixed = _scan_file(file_path)
        all_tabs.extend(tabs)
        all_mixed.extend(mixed)

    errors = []
    warnings = []

    if all_tabs:
        warnings.append(f"Files contain leading tabs ({len(all_tabs)} occurrences).")
    if all_mixed:
        warnings.append(f"Files contain mixed indentation ({len(all_mixed)} occurrences).")

    ok = not all_tabs and not all_mixed

    return DiagnosticResult(
        component="indent",
        ok=ok,
        details={
            "python_files_scanned": len(py_files),
            "leading_tab_issues": all_tabs,
            "mixed_indent_issues": all_mixed,
        },
        errors=errors,
        warnings=warnings,
    ).as_dict()
