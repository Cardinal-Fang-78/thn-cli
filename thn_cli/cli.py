# thn_cli/cli.py
"""
THN CLI Core Dispatcher (Hybrid-Standard)
=========================================

RESPONSIBILITIES
----------------
Defines the core CLI construction and dispatch pipeline for THN.

This module is responsible for:
    • Constructing the top-level argparse parser
    • Registering command groups dynamically
    • Enforcing THN-specific error semantics
    • Dispatching parsed arguments to command handlers
    • Normalizing argparse behavior for golden tests and CI

This file is the *spinal cord* of the CLI:
    all commands flow through it.

INVARIANTS
----------
    • argparse MUST NOT call sys.exit directly
    • All user-facing errors MUST raise CommandError
    • --help MUST exit cleanly with code 0
    • Unknown or missing commands MUST raise USER_CONTRACT errors
    • Dispatch MUST return a stable integer exit code

NON-GOALS
---------
    • Business logic execution
    • Filesystem mutation
    • Output formatting beyond version/help
    • Command-specific argument parsing

CONTRACT STATUS
---------------
LOCKED CORE INFRASTRUCTURE

Changes here affect:
    • All CLI invocations
    • Golden tests
    • Subprocess-driven tools
    • GUI / automation consumers

Modify only with extreme care.
"""

from __future__ import annotations

import argparse
from typing import Optional

from thn_cli.contracts.errors import USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError


class _HelpExit(Exception):
    """
    Internal control-flow exception used to intercept argparse --help.

    This allows THN to:
        • Avoid sys.exit()
        • Preserve exit code semantics
        • Keep help output deterministic for golden tests
    """


class THNArgumentParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser enforcing THN error contracts.
    """

    def error(self, message: str) -> None:
        """
        Override argparse default error handling.

        All parse errors are surfaced as USER_CONTRACT violations.
        """
        raise CommandError(
            contract=USER_CONTRACT,
            message=message,
        )

    def exit(self, status: int = 0, message: str | None = None) -> None:
        """
        Override argparse exit behavior.

        argparse calls this for --help and some internal flows.
        We intercept it to prevent sys.exit().
        """
        if message:
            self._print_message(message)
        raise _HelpExit(status)


def _register_command_groups(subparsers: argparse._SubParsersAction) -> None:
    """
    Dynamically register all CLI command groups.

    Command modules are discovered from:
        thn_cli.commands.__all__

    Each module may expose:
        add_subparser(subparsers)
    """
    from thn_cli import commands as commands_pkg

    for mod_name in getattr(commands_pkg, "__all__", []):
        mod = getattr(commands_pkg, mod_name, None)
        add = getattr(mod, "add_subparser", None)
        if callable(add):
            add(subparsers)


def build_parser() -> argparse.ArgumentParser:
    """
    Construct the top-level THN CLI parser.

    This includes:
        • Global flags
        • Command group registration
    """
    parser = THNArgumentParser(
        prog="thn",
        description="THN Master Control / THN CLI",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information",
    )

    subparsers = parser.add_subparsers(dest="command")
    _register_command_groups(subparsers)

    return parser


def _resolve_version_string() -> str:
    """
    Resolve the CLI version string.

    Falls back to a safe default if version metadata is unavailable.
    """
    try:
        from thn_cli import __version__  # type: ignore

        return str(__version__)
    except Exception:
        return "2.0.0"


def dispatch(
    argv: list[str],
    *,
    parser: Optional[argparse.ArgumentParser] = None,
) -> int:
    """
    Dispatch CLI execution.

    Responsibilities:
        • Parse argv
        • Handle --help and --version
        • Route execution to command handlers
        • Return a stable integer exit code
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
