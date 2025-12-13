"""
THN CLI Entry Point (Hybrid-Standard)

Responsibilities:
    • Construct the argument parser
    • Register all command modules
    • Dispatch execution
    • Enforce CLI exit and error contracts
    • Provide a stable entrypoint for tests and tooling
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from typing import List, Optional

from thn_cli import THN_CLI_NAME, THN_CLI_VERSION
from thn_cli.command_loader import load_commands
from thn_cli.contracts.errors import INTERNAL_ERROR, USER_ERROR, format_user_error, suggest

# ---------------------------------------------------------------------------
# Debug Helpers
# ---------------------------------------------------------------------------


def _debug_enabled() -> bool:
    return os.environ.get("THN_CLI_DEBUG", "").strip() not in ("", "0", "false", "False")


# ---------------------------------------------------------------------------
# Custom ArgumentParser
#   - Never calls sys.exit()
#   - Converts argparse errors into ValueError we can handle centrally
# ---------------------------------------------------------------------------


class THNArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


# ---------------------------------------------------------------------------
# Parser Construction
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = THNArgumentParser(
        prog="thn",
        description=THN_CLI_NAME,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {THN_CLI_VERSION}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    load_commands(subparsers)

    # Store valid top-level commands for suggestion logic
    parser.set_defaults(_thn_valid_commands=sorted(subparsers.choices.keys()))

    return parser


# ---------------------------------------------------------------------------
# Main Entrypoint
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    """
    CLI execution entrypoint.

    Returns an integer exit code instead of raising SystemExit,
    to support unit testing and programmatic use.
    """
    parser = build_parser()

    try:
        args = parser.parse_args(argv)

    # --help / --version
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 0

    # Argument / user errors
    except ValueError as exc:
        bad_token = None
        if argv:
            first = argv[0]
            if isinstance(first, str) and first and not first.startswith("-"):
                bad_token = first

        candidates = getattr(parser, "_defaults", {}).get("_thn_valid_commands", [])

        suggestions = suggest(bad_token or "", candidates) if bad_token else []

        sys.stderr.write(
            format_user_error(
                message=f"argument command: {exc}",
                suggestions=suggestions,
                footer_lines=[
                    "Run `thn --help` to see available commands.",
                    "Run `thn docs` for full documentation.",
                ],
            )
        )

        if _debug_enabled():
            sys.stderr.write("\nTraceback (most recent call last):\n")
            traceback.print_stack(file=sys.stderr)

        return USER_ERROR.code

    # Dispatch command
    try:
        if hasattr(args, "func"):
            result = args.func(args)
            return int(result) if isinstance(result, int) else 0

        # Defensive fallback
        sys.stderr.write(
            format_user_error(
                "No command specified.",
                footer_lines=["Run `thn --help` to see available commands."],
            )
        )
        return USER_ERROR.code

    # Internal / unexpected errors
    except Exception:
        if _debug_enabled():
            traceback.print_exc()

        sys.stderr.write(
            f"ERROR [{INTERNAL_ERROR.code}: {INTERNAL_ERROR.kind}]: "
            "An unexpected internal error occurred.\n"
        )
        return INTERNAL_ERROR.code


# ---------------------------------------------------------------------------
# Script Invocation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
