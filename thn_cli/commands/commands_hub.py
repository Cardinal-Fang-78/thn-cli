# thn_cli/commands_hub.py

"""
THN Hub / Nexus Command Group (Hybrid-Standard)
===============================================

Commands:

    thn hub status [--json]
    thn hub sync   [--json]

Provides status reporting and placeholder sync actions for the
future THN Hub / Nexus integration layer.

Hybrid-Standard guarantees:
    • Structured OK/ERROR envelopes
    • Automation-safe JSON mode
    • No uncaught exceptions
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from thn_cli.hub.hub_status import get_hub_status
from thn_cli.hub.hub_sync import perform_hub_sync

# ---------------------------------------------------------------------------
# Output Helpers
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
# Command Handlers
# ---------------------------------------------------------------------------


def run_hub_status(args: argparse.Namespace) -> int:
    """Return the current Hub / Nexus subsystem status."""
    json_mode = bool(args.json)

    try:
        status = get_hub_status()
    except Exception as exc:
        return _err("Failed to retrieve Hub status.", json_mode, error=str(exc))

    return _ok(json_mode, hub_status=status)


def run_hub_sync(args: argparse.Namespace) -> int:
    """
    Perform a Hub sync operation (placeholder).
    Future versions will handshake with the Hub/Nexus network.
    """
    json_mode = bool(args.json)

    try:
        result = perform_hub_sync()
    except Exception as exc:
        return _err("Hub sync operation failed.", json_mode, error=str(exc))

    return _ok(json_mode, hub_sync=result)


# ---------------------------------------------------------------------------
# Command Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register all 'thn hub ...' commands."""

    parser = subparsers.add_parser(
        "hub",
        help="THN Hub / Nexus integration commands.",
        description="Inspect or interact with the THN Hub (future expansion).",
    )

    sub = parser.add_subparsers(
        dest="hub_command",
        required=True,
    )

    # ----------------------------------------------------------------------
    # thn hub status
    # ----------------------------------------------------------------------
    p_status = sub.add_parser(
        "status",
        help="Show THN Hub subsystem status.",
        description="Returns connection state, config details, and Hub diagnostics.",
    )
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=run_hub_status)

    # ----------------------------------------------------------------------
    # thn hub sync
    # ----------------------------------------------------------------------
    p_sync = sub.add_parser(
        "sync",
        help="Perform THN Hub sync (placeholder).",
        description="Triggers an outbound sync to the THN Hub (scaffolding).",
    )
    p_sync.add_argument("--json", action="store_true")
    p_sync.set_defaults(func=run_hub_sync)

    # Default: show help
    parser.set_defaults(func=lambda args: parser.print_help())
