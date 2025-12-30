"""
THN Sync Status (Compatibility Alias)
-------------------------------------

Command:
    thn sync-status

This command exists for backward compatibility.

Behavior:
    - Delegates directly to `thn sync status`
    - Enforces JSON-only, diagnostic-only semantics
    - No independent logic or policy
"""

from __future__ import annotations

import argparse

from thn_cli.commands.commands_sync_status import run_sync_status


def run_sync_status_alias(args: argparse.Namespace) -> int:
    """
    Compatibility wrapper for legacy `thn sync-status`.

    Forces --json semantics and delegates to the canonical implementation.
    """
    args.json = True
    return run_sync_status(args)


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "sync-status",
        help="Read Sync V2 Status DB (diagnostic, read-only). [compatibility alias]",
    )

    # Accept --json for backwards compatibility, but enforce it regardless.
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output (enforced by alias).",
    )

    parser.set_defaults(func=run_sync_status_alias)
