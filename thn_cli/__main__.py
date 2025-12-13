"""
THN CLI Entry Point (Hybrid-Standard)

Responsibilities:
    • Construct the argument parser
    • Register all command modules
    • Dispatch execution
    • Provide a stable entrypoint for tests and tooling
"""

from __future__ import annotations

import argparse
import sys

from thn_cli import THN_CLI_NAME, THN_CLI_VERSION
from thn_cli.command_loader import load_commands


def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the root CLI argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="thn",
        description=THN_CLI_NAME,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {THN_CLI_VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    load_commands(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    CLI execution entrypoint.

    Returns an integer exit code instead of raising SystemExit,
    to support unit testing and programmatic use.
    """
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse uses SystemExit for --help / --version
        return int(exc.code) if isinstance(exc.code, int) else 0

    if hasattr(args, "func"):
        result = args.func(args)
        return int(result) if isinstance(result, int) else 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
