# thn_cli/commands_diag.py

"""
THN Diagnostic Command Group (Hybrid-Standard)
==============================================

Commands:

    thn diag env      [--json]
    thn diag routing  [--json]
    thn diag registry [--json]
    thn diag plugins  [--json]
    thn diag tasks    [--json]
    thn diag ui       [--json]
    thn diag hub      [--json]
    thn diag sanity   [--json]

Each diagnostic returns structured, automation-safe JSON.
All errors & exceptions emit Hybrid-Standard envelopes:
    { "status": "ERROR", "message": "...", ... }
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from thn_cli.diagnostics.env_diag import diagnose_env
from thn_cli.diagnostics.hub_diag import diagnose_hub
from thn_cli.diagnostics.plugins_diag import diagnose_plugins
from thn_cli.diagnostics.registry_diag import diagnose_registry
from thn_cli.diagnostics.routing_diag import diagnose_routing
from thn_cli.diagnostics.sanity_diag import run_sanity
from thn_cli.diagnostics.tasks_diag import diagnose_tasks
from thn_cli.diagnostics.ui_diag import diagnose_ui

# ---------------------------------------------------------------------------
# Hybrid-Standard output helpers
# ---------------------------------------------------------------------------


def _emit_json(obj: Dict[str, Any]) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _ok(json_mode: bool, **payload) -> int:
    out = {"status": "OK"}
    out.update(payload)
    if json_mode:
        _emit_json(out)
    else:
        print(json.dumps(out, indent=4))
        print()
    return 0


def _err(msg: str, json_mode: bool, **extra) -> int:
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
# Diagnostic Wrappers
# ---------------------------------------------------------------------------


def _run_diag(func, json_mode: bool, label: str) -> int:
    """
    Shared wrapper that safely executes a diagnostic function and
    returns a Hybrid-Standard result envelope.
    """
    try:
        result = func()
    except Exception as exc:
        return _err(f"{label} diagnostic failed.", json_mode, error=str(exc))

    return _ok(json_mode, diagnostic=result)


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
    """
    Register:

        thn diag ...
    """

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

    # Individual subsystems
    _attach(
        "env",
        "Check the THN environment.",
        "Validate OS environment, paths, variables, and prerequisites.",
        run_diag_env,
    )

    _attach(
        "routing",
        "Check routing system.",
        "Validate routing rules, classifications, and configs.",
        run_diag_routing,
    )

    _attach(
        "registry",
        "Check registry structure.",
        "Verify registry.json integrity & versioning.",
        run_diag_registry,
    )

    _attach(
        "plugins",
        "Check plugin system.",
        "Validate plugin registry, modules, and loader readiness.",
        run_diag_plugins,
    )

    _attach(
        "tasks",
        "Check task subsystem.",
        "Inspect task registry, scheduler state, and consistency.",
        run_diag_tasks,
    )

    _attach(
        "ui",
        "Check UI subsystem.",
        "Validate UI launcher and UI API health.",
        run_diag_ui,
    )

    _attach(
        "hub",
        "Check THN Hub connectivity.",
        "Diagnose Hub/Nexus integration readiness.",
        run_diag_hub,
    )

    _attach(
        "sanity",
        "Run full system validation.",
        "Perform comprehensive multi-subsystem THN sanity tests.",
        run_diag_sanity,
    )

    # Fallback help
    parser.set_defaults(func=lambda args: parser.print_help())
