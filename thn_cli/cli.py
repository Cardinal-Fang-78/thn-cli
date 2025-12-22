# thn_cli/cli.py
"""
THN CLI Core Dispatcher (Hybrid-Standard)
=========================================

RESPONSIBILITIES
----------------
Defines the core CLI construction and dispatch pipeline for THN.
Owns argparse configuration, command registration, help behavior,
and top-level dispatch semantics.

INVARIANTS
----------
• argparse MUST NOT call sys.exit directly
• All user-facing errors MUST raise CommandError
• --help MUST exit cleanly with code 0
• Unknown or missing commands MUST raise USER_CONTRACT errors
• Dispatch MUST return a stable integer exit code
• --help output MUST be deterministic across Python versions and platforms

CONTRACT STATUS
---------------
Authoritative. This module defines the canonical CLI surface contract.
All CLI consumers (tests, CI, GUI shells) rely on its behavior.

NON-GOALS
---------
• No business logic execution
• No command-specific validation
• No dynamic command discovery beyond commands.__all__
• No environment mutation beyond argument parsing

TENET NOTES
-----------
• Follows THN Command Discovery Tenet (__all__ is canonical)
• Enforces deterministic argparse output (CI-safe)
• Avoids simulated workflows or background processes
"""

from __future__ import annotations

import argparse
from typing import Optional

from thn_cli.contracts.errors import USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError


class _HelpExit(Exception):
    """Internal control-flow exception used to intercept argparse exits."""


class THNArgumentParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser that converts argparse exits into
    THN-owned control flow and error contracts.
    """

    def error(self, message: str) -> None:
        raise CommandError(contract=USER_CONTRACT, message=message)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if message:
            self._print_message(message)
        raise _HelpExit(status)


def _register_command_groups(subparsers: argparse._SubParsersAction) -> None:
    """
    Register all CLI command groups deterministically.

    Ordering is defined *only* by thn_cli.commands.__all__.
    """
    from thn_cli import commands as commands_pkg

    # ------------------------------------------------------------------
    # CRITICAL DETERMINISM GUARANTEE
    #
    # __all__ is canonical, but import order is NOT guaranteed to be
    # stable across platforms or filesystems. We must sort explicitly
    # before registration.
    # ------------------------------------------------------------------
    names = sorted(getattr(commands_pkg, "__all__", []))

    for name in names:
        mod = getattr(commands_pkg, name, None)
        add = getattr(mod, "add_subparser", None)
        if callable(add):
            add(subparsers)

    # ------------------------------------------------------------------
    # Deterministic argparse help enforcement
    # ------------------------------------------------------------------
    # 1. Force stable ordering of subcommands
    # 2. Prevent argparse from collapsing long choice lists into "..."
    #    (behavior differs across Python builds and CI environments)
    # ------------------------------------------------------------------
    choices = sorted(subparsers.choices.keys())
    subparsers.metavar = "{" + ",".join(choices) + "}"
    subparsers._choices_actions.sort(key=lambda a: a.dest)


def build_parser() -> argparse.ArgumentParser:
    parser = THNArgumentParser(
        prog="thn",
        description="THN Master Control / THN CLI",
    )

    # Restore stable argparse headings (Python 3.12+ regression)
    parser._optionals.title = "options"

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information",
    )

    subparsers = parser.add_subparsers(dest="command")
    _register_command_groups(subparsers)

    return parser


def _resolve_version_string() -> str:
    try:
        from thn_cli import __version__  # type: ignore

        return str(__version__)
    except Exception:
        # Fallback must be stable and non-failing
        return "2.0.0"


def dispatch(
    argv: list[str],
    *,
    parser: Optional[argparse.ArgumentParser] = None,
) -> int:
    """
    Parse CLI arguments and dispatch execution.

    Returns a stable integer exit code.
    """
    if parser is None:
        parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except _HelpExit as exc:
        return exc.args[0] if exc.args else 0

    if args.version:
        print(f"THN CLI version {_resolve_version_string()}")
        return 0

    if not getattr(args, "command", None):
        raise CommandError(
            contract=USER_CONTRACT,
            message="No command specified",
        )

    func = getattr(args, "func", None)
    if callable(func):
        rc = func(args)
        return int(rc) if rc is not None else 0

    raise CommandError(
        contract=USER_CONTRACT,
        message=f"Unknown command: {args.command}",
    )
