# thn_cli/commands/commands_diag.py

"""
THN Diagnostic Command Group (Hybrid-Standard)
==============================================

Commands:

    thn diag env
    thn diag routing
    thn diag registry
    thn diag plugins
    thn diag tasks
    thn diag ui
    thn diag hub
    thn diag sanity

Diagnostics return structured results.
All errors are raised as CommandError and rendered centrally.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from thn_cli.contracts.errors import SYSTEM_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.diagnostics.env_diag import diagnose_env
from thn_cli.diagnostics.hub_diag import diagnose_hub
from thn_cli.diagnostics.plugins_diag import diagnose_plugins
from thn_cli.diagnostics.registry_diag import diagnose_registry
from thn_cli.diagnostics.routing_diag import diagnose_routing
from thn_cli.diagnostics.sanity_diag import run_sanity
from thn_cli.diagnostics.tasks_diag import diagnose_tasks
from thn_cli.diagnostics.ui_diag import diagnose_ui

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _emit_result(result: Dict[str, Any], json_mode: bool) -> int:
    if json_mode:
        print(json.dumps({"status": "OK", "diagnostic": result}, indent=4))
    else:
        print(json.dumps(result, indent=4))
        print()
    return 0


def _run_diag(func, json_mode: bool, label: str) -> int:
    try:
        result = func()
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"{label} diagnostic failed.",
        ) from exc

    return _emit_result(result, json_mode)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_diag_env(args: argparse.Namespace) -> int:
    return _run_diag(diagnose_env, bool(args.json), "Environment")


def run_diag_routing(args: argparse.Namespace) -> int:
    return _run_diag(diagnose_routing, bool(args.json), "Routing")


def run_diag_registry(args: argparse.Namespace) -> int:
    return _run_diag(diagnose_registry, bool(args.json), "Registry")


def run_diag_plugins(args: argparse.Namespace) -> int:
    return _run_diag(diagnose_plugins, bool(args.json), "Plugins")


def run_diag_tasks(args: argparse.Namespace) -> int:
    return _run_diag(diagnose_tasks, bool(args.json), "Tasks")


def run_diag_ui(args: argparse.Namespace) -> int:
    return _run_diag(diagnose_ui, bool(args.json), "UI")


def run_diag_hub(args: argparse.Namespace) -> int:
    return _run_diag(diagnose_hub, bool(args.json), "Hub")


def run_diag_sanity(args: argparse.Namespace) -> int:
    return _run_diag(run_sanity, bool(args.json), "Sanity")


# ---------------------------------------------------------------------------
# Command Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "diag",
        help="Diagnostic utilities.",
        description="Diagnostic utilities.",
    )

    sub = parser.add_subparsers(dest="diag_cmd", required=True)

    def _attach(name: str, help_text: str, desc: str, func) -> None:
        p = sub.add_parser(name, help=help_text, description=desc)
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=func)

    _attach(
        "env", "Check the THN environment.", "Validate OS and runtime environment.", run_diag_env
    )
    _attach(
        "routing", "Check routing system.", "Validate routing rules and configs.", run_diag_routing
    )
    _attach(
        "registry", "Check registry structure.", "Verify registry integrity.", run_diag_registry
    )
    _attach(
        "plugins", "Check plugin system.", "Validate plugin loader and registry.", run_diag_plugins
    )
    _attach(
        "tasks", "Check task subsystem.", "Inspect task registry and scheduler.", run_diag_tasks
    )
    _attach("ui", "Check UI subsystem.", "Validate UI launcher and APIs.", run_diag_ui)
    _attach("hub", "Check THN Hub connectivity.", "Diagnose Hub/Nexus readiness.", run_diag_hub)
    _attach(
        "sanity", "Run full system validation.", "Run comprehensive sanity checks.", run_diag_sanity
    )

    parser.set_defaults(func=lambda args: parser.print_help())
