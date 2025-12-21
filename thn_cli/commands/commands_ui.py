# thn_cli/commands/commands_ui.py
"""
THN UI Command Group (Hybrid-Standard)
=====================================

RESPONSIBILITIES
----------------
Defines CLI entrypoints for interacting with the THN UI subsystem.

This module:
    • Owns `thn ui status`
    • Owns `thn ui launch`
    • Bridges CLI → UI runtime APIs
    • Emits structured, automation-safe output
    • Handles UI launch failures deterministically

SUPPORTED COMMANDS
------------------
    thn ui status [--json]
    thn ui launch [--json]

INVARIANTS
----------
    • UI commands MUST NOT crash the CLI
    • All failures MUST be caught and surfaced cleanly
    • --json mode MUST emit machine-readable JSON
    • Non-JSON mode MUST remain human-readable
    • UI lifecycle ownership remains external to the CLI

NON-GOALS
---------
    • UI configuration management
    • UI state persistence
    • UI runtime supervision
    • UI shutdown or lifecycle enforcement

Those responsibilities belong to:
    • thn_cli.ui subsystem modules
    • the UI application itself
    • future GUI orchestration layers

CONTRACT STATUS
---------------
LOCKED CLI OUTPUT SURFACE

The output shapes emitted by:
    • run_ui_status()
    • run_ui_launch()

are externally visible and relied upon by:
    • Automation
    • CI
    • Golden tests
    • GUI consumers

Any changes to:
    • output keys
    • semantic meaning
    • error signaling

MUST be accompanied by updated golden tests or a versioned CLI change.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from thn_cli.ui.ui_api import get_ui_status
from thn_cli.ui.ui_launcher import launch_ui

# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------


def _emit_json(obj: Dict[str, Any]) -> None:
    """
    Emit structured JSON output.

    CONTRACT
    --------
    Output must remain deterministic and UTF-8 safe.
    """
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _ok(json_mode: bool, **payload) -> int:
    """
    Emit a successful result envelope.
    """
    out = {"status": "OK"}
    out.update(payload)
    if json_mode:
        _emit_json(out)
    else:
        print(json.dumps(out, indent=4))
        print()
    return 0


def _err(msg: str, json_mode: bool, **extra) -> int:
    """
    Emit an error result envelope without raising.
    """
    out = {"status": "ERROR", "message": msg}
    out.update(extra)
    if json_mode:
        _emit_json(out)
    else:
        print(f"\nError: {msg}")
        if extra:
            print(json.dumps(extra, indent=4))
        print()
    return 1


# ---------------------------------------------------------------------------
# Command Implementations
# ---------------------------------------------------------------------------


def run_ui_status(args: argparse.Namespace) -> int:
    """
    Display the current UI subsystem status.
    """
    json_mode = bool(args.json)

    try:
        status = get_ui_status()
    except Exception as exc:
        return _err(
            "Failed to retrieve UI status.",
            json_mode,
            error=str(exc),
        )

    return _ok(json_mode, ui_status=status)


def run_ui_launch(args: argparse.Namespace) -> int:
    """
    Attempt to launch the THN UI application.
    """
    json_mode = bool(args.json)

    try:
        result = launch_ui()
    except Exception as exc:
        return _err(
            "UI launch failed.",
            json_mode,
            error=str(exc),
        )

    return _ok(json_mode, ui_launch=result)


# ---------------------------------------------------------------------------
# Subparser Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the `thn ui` command group.
    """
    parser = subparsers.add_parser(
        "ui",
        help="THN UI subsystem commands.",
        description="Inspect and launch THN UI features.",
    )

    sub = parser.add_subparsers(
        dest="ui_command",
        required=True,
    )

    # ui status ----------------------------------------------------
    p_status = sub.add_parser(
        "status",
        help="Show UI subsystem status.",
    )
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=run_ui_status)

    # ui launch ----------------------------------------------------
    p_launch = sub.add_parser(
        "launch",
        help="Launch the THN UI application.",
    )
    p_launch.add_argument("--json", action="store_true")
    p_launch.set_defaults(func=run_ui_launch)

    # default -------------------------------------------------------
    parser.set_defaults(func=lambda args: parser.print_help())
