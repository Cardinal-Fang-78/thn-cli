"""
THN Master Control / THN CLI Entrypoint (Unified Hybrid-Standard)
=================================================================

This file is the authoritative and *only* root entrypoint for the
THN CLI. It merges:

    • Stability + predictability of the original THN CLI dispatcher
    • Clean structured flow of the improved dispatcher
    • Hybrid-Standard guarantees for command loading & execution
    • Optional verbose debugging via THN_CLI_VERBOSE=1

Responsibilities:
    • Build the global Hybrid-Standard parser
    • Dynamically load all commands from thn_cli.commands
    • Safely dispatch each command's handler with controlled errors
    • Provide consistent exit codes for all subsystems
"""

from __future__ import annotations

import argparse
import sys
import os
from typing import List, Optional, Callable, Any

from .command_loader import load_commands


# ---------------------------------------------------------------------------
# Verbose diagnostic mode
# ---------------------------------------------------------------------------

_VERBOSE = bool(os.environ.get("THN_CLI_VERBOSE", "").strip())


def _log(msg: str) -> None:
    """Internal debug logger (only prints when verbose mode enabled)."""
    if _VERBOSE:
        print(f"[thn-cli:debug] {msg}")


# ---------------------------------------------------------------------------
# Parser Construction
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """
    Construct the root THN CLI parser using Hybrid-Standard conventions.

    The parser loads *all* command groups dynamically from:

        thn_cli.commands.*

    Subcommands are attached to this parser via each command module’s
    add_subparser() function.
    """

    parser = argparse.ArgumentParser(
        prog="thn",
        description="THN Master Control / THN CLI",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        title="Available commands",
        dest="command",
    )

    _log("Loading command modules...")
    load_commands(subparsers)
    _log("Command modules loaded successfully.")

    # Default action: show help when no command provided
    parser.set_defaults(func=lambda _args: parser.print_help())

    return parser


# ---------------------------------------------------------------------------
# Safe Invocation Wrapper
# ---------------------------------------------------------------------------

def _safe_invoke(func: Callable[[Any], Any], args: argparse.Namespace) -> int:
    """
    Execute a command handler inside a protective wrapper.

    Guarantees:
        • No exception escapes to the top level.
        • Runtime errors produce exit code 1.
        • Verbose mode prints full traceback.
        • Handler return values:
              - int      → used as exit code
              - None     → treated as success (0)
              - object   → treated as success (0)
    """
    try:
        _log(f"Dispatching handler: {func.__name__}")
        result = func(args)

        if isinstance(result, int):
            return result

        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)

        if _VERBOSE:
            import traceback
            traceback.print_exc()

        return 1


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """
    Primary entrypoint for the THN CLI.

    Parameters:
        argv: Optional list of arguments (used for testing).
              If None → sys.argv[1:].

    Returns:
        Integer exit code (0 = success, nonzero = failure)
    """
    if argv is None:
        argv = sys.argv[1:]

    _log(f"argv = {argv}")

    try:
        parser = build_parser()
    except Exception as exc:
        print("Failed to initialize THN CLI parser.", file=sys.stderr)
        if _VERBOSE:
            import traceback
            traceback.print_exc()
        return 1

    args = parser.parse_args(argv)
    func = getattr(args, "func", None)

    if func is None:
        _log("No command given; showing help.")
        parser.print_help()
        return 1

    return _safe_invoke(func, args)


# ---------------------------------------------------------------------------
# Module Execution Guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Protect against accidental re-entry during nested tooling/IDE invocations
    if os.environ.get("THN_CLI_REENTRANT") == "1":
        print("Warning: THN CLI re-entered; aborting nested launch.", file=sys.stderr)
        sys.exit(1)

    sys.exit(main())
