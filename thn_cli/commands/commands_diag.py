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
    thn diag all

Diagnostics are:
    • Read-only
    • Non-authoritative (except suite aggregation)
    • Structurally normalized via DiagnosticResult
    • Governed by the diagnostics taxonomy

All errors are raised as CommandError and rendered centrally.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable, Dict

from thn_cli.contracts.errors import SYSTEM_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.diagnostics.diagnostic_result import DiagnosticResult
from thn_cli.diagnostics.env_diag import diagnose_env
from thn_cli.diagnostics.hub_diag import diagnose_hub
from thn_cli.diagnostics.plugins_diag import diagnose_plugins
from thn_cli.diagnostics.registry_diag import diagnose_registry
from thn_cli.diagnostics.routing_diag import diagnose_routing
from thn_cli.diagnostics.sanity_diag import run_sanity
from thn_cli.diagnostics.suite import run_full_suite
from thn_cli.diagnostics.tasks_diag import diagnose_tasks
from thn_cli.diagnostics.ui_diag import diagnose_ui

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize any single diagnostic dict into a Hybrid-Standard shape.
    """
    return DiagnosticResult.from_raw(raw).as_dict()


def _emit_single(result: Dict[str, Any], json_mode: bool) -> int:
    """
    Emit a SINGLE diagnostic result.

    CLI wrapping is permitted here because the result is non-authoritative.
    """
    envelope = {
        "ok": bool(result.get("ok", False)),
        "diagnostics": [result],
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }
    print(json.dumps(envelope, indent=4))
    return 0


def _run_single(
    func: Callable[[], Dict[str, Any]],
    json_mode: bool,
    label: str,
) -> int:
    """
    Execute a single diagnostic function with normalization and error isolation.
    """
    try:
        raw = func()
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"{label} diagnostic failed.",
        ) from exc

    return _emit_single(_normalize(raw), json_mode)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_diag_env(args: argparse.Namespace) -> int:
    return _run_single(diagnose_env, bool(args.json), "Environment")


def run_diag_routing(args: argparse.Namespace) -> int:
    return _run_single(diagnose_routing, bool(args.json), "Routing")


def run_diag_registry(args: argparse.Namespace) -> int:
    return _run_single(diagnose_registry, bool(args.json), "Registry")


def run_diag_plugins(args: argparse.Namespace) -> int:
    return _run_single(diagnose_plugins, bool(args.json), "Plugins")


def run_diag_tasks(args: argparse.Namespace) -> int:
    return _run_single(diagnose_tasks, bool(args.json), "Tasks")


def run_diag_ui(args: argparse.Namespace) -> int:
    return _run_single(diagnose_ui, bool(args.json), "UI")


def run_diag_hub(args: argparse.Namespace) -> int:
    return _run_single(diagnose_hub, bool(args.json), "Hub")


def run_diag_sanity(args: argparse.Namespace) -> int:
    return _run_single(run_sanity, bool(args.json), "Sanity")


def run_diag_all(args: argparse.Namespace) -> int:
    """
    Run the full diagnostic suite.

    This is the ONLY authoritative aggregation path.
    No CLI-level wrapping or reinterpretation is permitted.
    """
    try:
        result = run_full_suite()
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Diagnostic suite failed.",
        ) from exc

    print(json.dumps(result, indent=4))
    return 0


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
        "sanity", "Run core sanity checks.", "Run comprehensive sanity checks.", run_diag_sanity
    )
    _attach("all", "Run all diagnostics.", "Run full diagnostic suite.", run_diag_all)

    parser.set_defaults(func=lambda args: parser.print_help())
