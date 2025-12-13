"""
THN Registry CLI Commands (Hybrid-Standard)
-------------------------------------------

Provides:

    thn registry show [--json]
    thn registry reset [--json]
    thn registry validate [--json]
    thn registry recent [--limit N] [--json]

The registry subsystem stores metadata for:

    • projects
    • modules
    • blueprint runs
    • task executions
    • arbitrary system events

This command group ensures safe, deterministic, and machine-friendly
access to registry state.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from thn_cli.pathing import get_thn_paths
from thn_cli.registry import get_recent_events, load_registry, save_registry, validate_registry

# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------


def _out_json(obj: Any) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _header(title: str) -> None:
    print(f"\n{title}\n")


def _err(msg: str) -> None:
    print(f"Error: {msg}\n")


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_registry_show(args: argparse.Namespace) -> int:
    paths = get_thn_paths()
    reg = load_registry(paths)

    if args.json:
        _out_json(
            {
                "status": "OK",
                "registry": reg,
            }
        )
        return 0

    _header("THN Registry")
    _out_json(reg)
    print()
    return 0


def run_registry_reset(args: argparse.Namespace) -> int:
    """
    Resets the registry to a known-good initial state.
    """
    paths = get_thn_paths()

    new_reg = {
        "version": 1,
        "projects": {},
        "events": [],
    }
    save_registry(paths, new_reg)

    if args.json:
        _out_json(
            {
                "status": "OK",
                "message": "Registry reset complete.",
            }
        )
        return 0

    print("\nRegistry reset complete.\n")
    return 0


def run_registry_validate(args: argparse.Namespace) -> int:
    """
    Validate registry structure, required keys, value types, and schema alignment.
    """
    paths = get_thn_paths()
    reg = load_registry(paths)
    result = validate_registry(reg)

    # Ensure consistent result format
    out = {
        "status": "OK" if result.get("valid") else "ERROR",
        "valid": result.get("valid", False),
        "details": result,
    }

    if args.json:
        _out_json(out)
        return 0 if out["valid"] else 1

    _header("THN Registry Validation")
    _out_json(out)
    print()
    return 0 if out["valid"] else 1


def run_registry_recent(args: argparse.Namespace) -> int:
    """
    Display recent registry events for audit/debugging.
    """
    paths = get_thn_paths()
    reg = load_registry(paths)

    events = get_recent_events(reg, limit=args.limit)

    if args.json:
        _out_json(
            {
                "status": "OK",
                "count": len(events),
                "events": events,
            }
        )
        return 0

    _header("THN Registry - Recent Events")

    if not events:
        print("(no registry events logged yet)\n")
        return 0

    _out_json(events)
    print()
    return 0


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "registry",
        help="Inspect and modify the THN registry.",
        description="Read, validate, reset, and inspect THN system registry data.",
    )

    sub = parser.add_subparsers(dest="registry_cmd", required=True)

    # ------- show -------
    p_show = sub.add_parser("show", help="Show registry contents.")
    p_show.add_argument(
        "--json",
        action="store_true",
        help="Return output in JSON format.",
    )
    p_show.set_defaults(func=run_registry_show)

    # ------- reset -------
    p_reset = sub.add_parser("reset", help="Reset registry to base state.")
    p_reset.add_argument(
        "--json",
        action="store_true",
        help="Return output in JSON format.",
    )
    p_reset.set_defaults(func=run_registry_reset)

    # ------- validate -------
    p_validate = sub.add_parser("validate", help="Validate registry structure.")
    p_validate.add_argument(
        "--json",
        action="store_true",
        help="Return output in JSON format.",
    )
    p_validate.set_defaults(func=run_registry_validate)

    # ------- recent -------
    p_recent = sub.add_parser("recent", help="Show recent registry events.")
    p_recent.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of events to display.",
    )
    p_recent.add_argument(
        "--json",
        action="store_true",
        help="Return output in JSON format.",
    )
    p_recent.set_defaults(func=run_registry_recent)

    # Default fallback
    parser.set_defaults(func=lambda args: parser.print_help())
