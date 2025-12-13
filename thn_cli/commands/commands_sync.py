"""
THN Sync V2 Command Group (Hybrid-Standard)
------------------------------------------

Provides safe, structured Sync V2 operations:

    thn sync inspect <zip> [--json]
    thn sync apply <zip> [--dry-run] [--json]
    thn sync make-test --in <folder> [--json]

Also registers the legacy:
    thn sync web
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.envelope import inspect_envelope, load_envelope_from_file
from thn_cli.syncv2.executor import execute_envelope_plan
from thn_cli.syncv2.make_test import make_test_envelope

# Legacy Sync Web subcommand
from .commands_sync_web import add_subparser as add_web_subparser

# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------


def _out_json(obj: Any) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _err_json(message: str, **fields: Any) -> None:
    obj = {"status": "ERROR", "message": message}
    obj.update(fields)
    _out_json(obj)


def _err_text(message: str) -> None:
    print(f"Error: {message}\n")


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_sync_inspect(args: argparse.Namespace) -> int:
    """
    Performs a non-destructive inspection of a Sync V2 envelope.
    Shows manifest, file count, and structural metadata.
    """
    path = args.zip

    if not os.path.isfile(path):
        if args.json:
            _err_json("Envelope file not found.", provided_path=path)
        else:
            _err_text(f"Envelope file not found: {path}")
        return 1

    try:
        env = load_envelope_from_file(path)
        info = inspect_envelope(env)
    except Exception as exc:
        if args.json:
            _err_json("Failed to inspect envelope.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    if args.json:
        _out_json({"status": "OK", "inspect": info})
        return 0

    print("\nTHN Sync Inspect\n")
    print(json.dumps(info, indent=4, ensure_ascii=False))
    print()
    return 0


def run_sync_apply(args: argparse.Namespace) -> int:
    """
    Applies a Sync V2 envelope:

        1. Build execution plan (routing + resolve)
        2. Apply via authoritative apply_envelope_v2
    """
    path = args.zip
    dry = bool(args.dry_run)

    if not os.path.isfile(path):
        if args.json:
            _err_json("Envelope file not found.", provided_path=path)
        else:
            _err_text(f"Envelope file not found: {path}")
        return 1

    try:
        env = load_envelope_from_file(path)

        # Build plan (routing → file movements)
        plan = execute_envelope_plan(env, tag="sync_apply", dry_run=dry)

        # If dry-run: skip apply, return plan only
        if dry:
            if args.json:
                _out_json({"status": "DRY_RUN", "plan": plan})
                return 0

            print("\nTHN Sync Apply (DRY-RUN)\n")
            print(json.dumps(plan, indent=4, ensure_ascii=False))
            print()
            return 0

        # Apply envelope to destinations
        result = apply_envelope_v2(env)

    except Exception as exc:
        if args.json:
            _err_json("Sync apply failed.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # Success output
    if args.json:
        _out_json({"status": "OK", "plan": plan, "apply": result})
        return 0

    print("\nTHN Sync Apply\n")
    print("Execution Plan:\n")
    print(json.dumps(plan, indent=4, ensure_ascii=False))
    print("\nApply Result:\n")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    print()
    return 0


def run_sync_make_test(args: argparse.Namespace) -> int:
    """
    Creates a test envelope from a folder and returns the object structure.
    Useful for diagnostics + Sync V2 dev.
    """
    in_path = args.in_path

    if not os.path.isdir(in_path):
        if args.json:
            _err_json("Input folder does not exist.", provided_path=in_path)
        else:
            _err_text(f"Input folder does not exist: {in_path}")
        return 1

    try:
        result = make_test_envelope(in_path)
    except Exception as exc:
        if args.json:
            _err_json("Failed to generate test envelope.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    if args.json:
        _out_json({"status": "OK", "result": result})
        return 0

    print("\nTHN Sync Make-Test\n")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    print()
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "sync",
        help="Sync V2 envelope utilities.",
        description="Inspect, apply, or generate THN Sync V2 envelopes.",
    )

    sync_sub = parser.add_subparsers(dest="sync_command", required=True)

    # ----------------------------------------------------------------------
    # thn sync inspect <zip>
    # ----------------------------------------------------------------------
    p_inspect = sync_sub.add_parser("inspect", help="Inspect a Sync V2 envelope.")
    p_inspect.add_argument("zip", help="Path to the envelope ZIP.")
    p_inspect.add_argument("--json", action="store_true", help="Structured JSON output.")
    p_inspect.set_defaults(func=run_sync_inspect)

    # ----------------------------------------------------------------------
    # thn sync apply <zip> [--dry-run]
    # ----------------------------------------------------------------------
    p_apply = sync_sub.add_parser("apply", help="Apply a Sync V2 envelope.")
    p_apply.add_argument("zip", help="Path to the envelope ZIP.")
    p_apply.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate apply without moving files.",
    )
    p_apply.add_argument("--json", action="store_true", help="Structured JSON output.")
    p_apply.set_defaults(func=run_sync_apply)

    # ----------------------------------------------------------------------
    # thn sync make-test --in <folder>
    # ----------------------------------------------------------------------
    p_test = sync_sub.add_parser(
        "make-test",
        help="Generate + inspect + apply a test envelope from an input directory.",
    )
    p_test.add_argument(
        "--in",
        dest="in_path",
        required=True,
        help="Folder to package into a test envelope.",
    )
    p_test.add_argument("--json", action="store_true", help="Structured JSON output.")
    p_test.set_defaults(func=run_sync_make_test)

    # ----------------------------------------------------------------------
    # Legacy Sync Web integration (unchanged but now isolated)
    # ----------------------------------------------------------------------
    add_web_subparser(sync_sub)

    # Default help
    parser.set_defaults(func=lambda args: parser.print_help())
