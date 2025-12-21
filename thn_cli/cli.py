# thn_cli/cli.py
"""
THN CLI Core Dispatcher (Hybrid-Standard)
=========================================

LOCKED CORE INFRASTRUCTURE
"""

from __future__ import annotations

import argparse
from typing import Optional

from thn_cli.contracts.errors import USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError


class _HelpExit(Exception):
    """Internal control-flow exception used to intercept argparse --help."""


class THNArgumentParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser enforcing THN error contracts and deterministic help.
    """

    def error(self, message: str) -> None:
        raise CommandError(
            contract=USER_CONTRACT,
            message=message,
        )

    def exit(self, status: int = 0, message: str | None = None) -> None:
        """
        Intercept argparse exits.

        For --help, ALWAYS print full help explicitly to guarantee
        deterministic output across TTY and CI environments.
        """
        if status == 0:
            # argparse help path — force full help
            self.print_help()
        elif message:
            self._print_message(message)

        raise _HelpExit(status)


def _register_command_groups(subparsers: argparse._SubParsersAction) -> None:
    from thn_cli import commands as commands_pkg

    for mod_name in getattr(commands_pkg, "__all__", []):
        mod = getattr(commands_pkg, mod_name, None)
        add = getattr(mod, "add_subparser", None)
        if callable(add):
            add(subparsers)


def build_parser() -> argparse.ArgumentParser:
    parser = THNArgumentParser(
        prog="thn",
        description="THN Master Control / THN CLI",
        formatter_class=argparse.RawTextHelpFormatter,
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
