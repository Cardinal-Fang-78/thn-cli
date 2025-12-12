"""
THN Sync CLI Command (Hybrid-Standard)
--------------------------------------

Modernized CLI asset sync workflow using the Sync V2 routing + executor engine:

    thn sync cli --input <folder-or-file> [--dry-run | --apply] [--json]

Pipeline:

    1. Package input into a test envelope (make_test_envelope)
    2. Load envelope
    3. Inspect envelope (manifest summary)
    4. Compute SyncV2 execution plan (routing + file moves)
    5. Apply via authoritative apply_envelope_v2 (optional)
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

# ---------------------------------------------------------------------------
# Output Utilities
# ---------------------------------------------------------------------------


def _out_json(obj: Any) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _err_json(msg: str, **fields: Any) -> None:
    obj = {"status": "ERROR", "message": msg}
    obj.update(fields)
    _out_json(obj)


def _err_text(msg: str) -> None:
    print(f"Error: {msg}\n")


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


def run_sync_cli(args: argparse.Namespace) -> int:
    input_path = args.input
    json_mode = bool(args.json)

    # Validate input
    if not os.path.exists(input_path):
        if json_mode:
            _err_json("Input path does not exist.", provided_path=input_path)
        else:
            _err_text(f"Input path does not exist: {input_path}")
        return 1

    dry = bool(args.dry_run)
    explicit_apply = bool(args.apply)

    if not dry and not explicit_apply:
        dry = True  # default behavior

    # ----------------------------------------------------------------------
    # Step 1 — Build envelope from input
    # ----------------------------------------------------------------------
    try:
        env_info = make_test_envelope(input_path)
        env_zip = env_info.get("envelope_zip")
        if not env_zip:
            raise RuntimeError("Envelope generator failed: no 'envelope_zip' returned.")
    except Exception as exc:
        if json_mode:
            _err_json("Failed to create test envelope.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ----------------------------------------------------------------------
    # Step 2 — Load envelope
    # ----------------------------------------------------------------------
    try:
        env = load_envelope_from_file(env_zip)
    except Exception as exc:
        if json_mode:
            _err_json("Failed to load envelope.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ----------------------------------------------------------------------
    # Step 3 — Inspect envelope
    # ----------------------------------------------------------------------
    try:
        inspection = inspect_envelope(env)
    except Exception as exc:
        if json_mode:
            _err_json("Failed to inspect envelope.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ----------------------------------------------------------------------
    # Step 4 — Build execution plan (routing + file resolution)
    # ----------------------------------------------------------------------
    try:
        plan = execute_envelope_plan(env, tag="sync_cli", dry_run=True)
    except Exception as exc:
        if json_mode:
            _err_json("Failed to compute execution plan.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ----------------------------------------------------------------------
    # If dry-run → return here
    # ----------------------------------------------------------------------
    if dry:
        if json_mode:
            _out_json(
                {
                    "status": "DRY_RUN",
                    "input": input_path,
                    "inspection": inspection,
                    "plan": plan,
                }
            )
            return 0

        print("\n==========================================")
        print("     THN SYNC CLI via SYNC V2 (DRY RUN)")
        print("==========================================\n")

        print("Envelope Inspection:\n")
        print(json.dumps(inspection, indent=4, ensure_ascii=False))
        print("\nExecution Plan:\n")
        print(json.dumps(plan, indent=4, ensure_ascii=False))
        print()
        return 0

    # ----------------------------------------------------------------------
    # Step 5 — Apply envelope using the authoritative engine
    # ----------------------------------------------------------------------
    try:
        apply_result = apply_envelope_v2(env)
    except Exception as exc:
        if json_mode:
            _err_json("Sync CLI apply failed.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ----------------------------------------------------------------------
    # Success Output
    # ----------------------------------------------------------------------
    if json_mode:
        _out_json(
            {
                "status": "OK",
                "input": input_path,
                "inspection": inspection,
                "plan": plan,
                "apply": apply_result,
            }
        )
        return 0

    print("\n==========================================")
    print("       THN SYNC CLI via SYNC V2 (APPLY)")
    print("==========================================\n")

    print("Envelope Inspection:\n")
    print(json.dumps(inspection, indent=4, ensure_ascii=False))

    print("\nExecution Plan:\n")
    print(json.dumps(plan, indent=4, ensure_ascii=False))

    print("\nApply Result:\n")
    print(json.dumps(apply_result, indent=4, ensure_ascii=False))

    print("\nTHN Sync CLI workflow complete.\n")
    return 0


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------


def add_subparser(sync_subparsers: argparse._SubParsersAction) -> None:
    """
    Register:

        thn sync cli --input <folder-or-file> [--dry-run | --apply] [--json]
    """
    parser = sync_subparsers.add_parser(
        "cli",
        help="Sync CLI tool assets via Sync V2 routing and executor.",
        description=(
            "Package input into an envelope, inspect, route, compute the plan, "
            "and apply via Sync V2. Defaults to DRY RUN unless --apply is used."
        ),
    )

    parser.add_argument(
        "--input",
        "--in",
        "-i",
        dest="input",
        required=True,
        help="Folder or file to package into a test envelope.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate apply without modifying files.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform a live apply (write files).",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON output.",
    )

    parser.set_defaults(func=run_sync_cli)
