# thn_cli/commands/commands_sync_status.py

"""
THN Sync Status (Read-Only Diagnostic)
-------------------------------------

Command:
    thn sync status

This command:
    • Exposes the Status DB read surface (diagnostic-only)
    • Does NOT mutate state
    • Does NOT infer or reconstruct history
    • Does NOT reconcile with TXLOG
    • Does NOT gate execution or policy
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from thn_cli.contracts.errors import USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.syncv2.status_read import read_status_db_stub


def _jprint(obj: Any) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def run_sync_status(args: argparse.Namespace) -> int:
    """
    Execute `thn sync status`.

    This surface is diagnostic-only and JSON-only by contract.
    """

    if not args.json:
        raise CommandError(
            contract=USER_CONTRACT,
            message="Status DB read surface is diagnostic-only. Use --json.",
        )

    result: Dict[str, Any] = read_status_db_stub()
    _jprint(result)
    return 0


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "status",
        help="Read Sync V2 Status DB (diagnostic, read-only).",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output",
    )

    parser.set_defaults(func=run_sync_status)
