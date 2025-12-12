"""
THN CLI Entrypoint (Hybrid-Standard)

Responsibilities:
    • Parse global CLI arguments
    • Provide --help and --version
    • Initialize command routing
    • Delegate execution to subcommands

Guarantees:
    • No side effects on import
    • No filesystem writes
    • Deterministic startup behavior
"""

from __future__ import annotations

import argparse
import sys

from thn_cli import THN_CLI_NAME, __version__
from thn_cli.command_loader import load_commands


def _print_version_and_exit() -> None:
    """
    Print CLI version and exit immediately.
    No side effects, no command loading.
    """
    print(__version__)
    sys.exit(0)


def main(argv: list[str] | None = None) -> None:
    """
    CLI entrypoint.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Handle --version early (before argparse consumes subcommands)
    if "--version" in argv:
        _print_version_and_exit()

    parser = argparse.ArgumentParser(
        prog="thn",
        description=THN_CLI_NAME,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="{new,blueprint,dev,diag,hub,init,keys,list,make,plugins,registry,routing,sync,cli,delta,docs,sync-remote,sync-status,web,tasks,ui}",
    )

    # Load all command modules
    load_commands(subparsers)

    args = parser.parse_args(argv)

    # No command provided → show help
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    # Dispatch command
    args.func(args)


if __name__ == "__main__":
    main()
