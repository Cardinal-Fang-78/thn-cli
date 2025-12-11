"""
THN Routing Command Group (Hybrid-Standard)
------------------------------------------

Provides diagnostic and introspection commands for the Hybrid-Standard
routing subsystem.

Commands:

    thn routing show [--json]
    thn routing test [--file <zip>] [--tag <tag>] [--json]

This tooling exercises the canonical routing entrypoint:

    thn_cli.routing.integration.resolve_routing
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, Optional

from thn_cli.pathing import get_thn_paths
from thn_cli.routing.integration import resolve_routing
from thn_cli.routing.rules import load_routing_rules
from thn_cli.routing_config import load_routing_config


# ---------------------------------------------------------------------------
# Output Helpers
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

def run_routing_show(args: argparse.Namespace) -> int:
    """
    Display unified routing configuration:

        • raw rules from routing_rules.json
        • classifier configuration
        • schema validation results
    """
    paths = get_thn_paths()

    # Load unified schema + rules bundle
    config = load_routing_config(paths)

    if args.json:
        _out_json({
            "status": "OK",
            "config": config,
        })
        return 0

    _header("THN Routing Configuration (Unified)")
    _out_json(config)
    print()
    return 0


def run_routing_test(args: argparse.Namespace) -> int:
    """
    Test routing behavior using:

        • a tag (default: "test")
        • an optional ZIP payload
    """
    paths = get_thn_paths()

    tag = args.tag or "test"
    payload_path = args.file
    zip_bytes: Optional[bytes] = None

    # --------------------------------------------------------------
    # ZIP Payload Handling
    # --------------------------------------------------------------
    if payload_path:
        if not os.path.isfile(payload_path):
            err = {
                "status": "ERROR",
                "message": "Payload file not found.",
                "provided_path": payload_path,
                "cwd": os.getcwd(),
            }
            if args.json:
                _out_json(err)
                return 1

            _err("The file specified with --file does not exist.")
            print(f"Provided path : {payload_path}")
            print(f"Working dir   : {os.getcwd()}\n")
            return 1

        try:
            with open(payload_path, "rb") as f:
                zip_bytes = f.read()
        except Exception as exc:
            err = {
                "status": "ERROR",
                "message": f"Failed reading payload file: {exc}",
            }
            if args.json:
                _out_json(err)
                return 1

            _err(str(exc))
            return 1

    # --------------------------------------------------------------
    # Perform routing through the canonical integration layer
    # --------------------------------------------------------------
    try:
        result = resolve_routing(
            tag=tag,
            zip_bytes=zip_bytes,
            paths=paths,
        )
    except Exception as exc:
        err = {
            "status": "ERROR",
            "message": f"Routing engine exception: {exc}",
        }
        if args.json:
            _out_json(err)
            return 1

        _err(str(exc))
        return 1

    out = {
        "status": "OK",
        "tag": tag,
        "zip_provided": bool(zip_bytes),
        "routing": result,
    }

    # JSON or pretty output
    if args.json:
        _out_json(out)
        return 0

    _header("Routing Test Result")
    _out_json(out)
    print()
    return 0


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------

def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "routing",
        help="Routing utilities for THN.",
        description="Hybrid-Standard routing engine diagnostics.",
    )

    routing_sub = parser.add_subparsers(dest="routing_cmd", required=True)

    # ----------------------------------------------------------------------
    # thn routing show
    # ----------------------------------------------------------------------
    p_show = routing_sub.add_parser(
        "show",
        help="Show unified routing configuration (rules + classifier + schema).",
    )
    p_show.add_argument(
        "--json",
        action="store_true",
        help="Return output in JSON format.",
    )
    p_show.set_defaults(func=run_routing_show)

    # ----------------------------------------------------------------------
    # thn routing test
    # ----------------------------------------------------------------------
    p_test = routing_sub.add_parser(
        "test",
        help="Evaluate routing rules with an optional tag and ZIP payload.",
    )
    p_test.add_argument(
        "--file",
        help="Path to ZIP payload to test (optional).",
        required=False,
    )
    p_test.add_argument(
        "--tag",
        help="Routing tag to evaluate. Default: 'test'.",
        required=False,
    )
    p_test.add_argument(
        "--json",
        action="store_true",
        help="Return output in JSON format.",
    )
    p_test.set_defaults(func=run_routing_test)

    # Default help fallback
    parser.set_defaults(func=lambda args: parser.print_help())
