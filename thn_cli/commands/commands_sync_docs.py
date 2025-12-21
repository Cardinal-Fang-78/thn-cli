"""
THN Sync Docs Command (Hybrid-Standard)
---------------------------------------

Modernized documentation-sync workflow using the Sync V2 routing
+ executor pipeline:

    thn sync docs --input <folder-or-file> [--dry-run | --apply] [--json]

Pipeline:
    1. Make a test envelope from input (folder/file)
    2. Load envelope into memory
    3. Inspect envelope (manifest)
    4. Build execution plan (routing + file movements)
    5. Apply via authoritative apply_envelope_v2 (optional)
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.envelope import inspect_envelope, load_envelope_from_file
from thn_cli.syncv2.executor import execute_envelope_plan
from thn_cli.syncv2.make_test import make_test_envelope
from thn_cli.syncv2.targets.docs import DocsSyncTarget

# ---------------------------------------------------------------------------
# Output helpers
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
# Handler
# ---------------------------------------------------------------------------


def run_sync_docs(args: argparse.Namespace) -> int:
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

    # Default to dry-run unless --apply is explicitly set
    if not dry and not explicit_apply:
        dry = True

    # ----------------------------------------------------------------------
    # Step 1 — Create envelope
    # ----------------------------------------------------------------------
    try:
        env_info = make_test_envelope(input_path)
        env_zip = env_info.get("envelope_zip")
        if not env_zip:
            raise RuntimeError("Envelope generator returned no 'envelope_zip'.")
    except Exception as exc:
        if json_mode:
            _err_json("Failed to create documentation envelope.", error=str(exc))
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
    # Step 3 — Inspect envelope (presentation-only)
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
    # Step 4 — Compute routing + execution plan (planning-only)
    # ----------------------------------------------------------------------
    try:
        plan = execute_envelope_plan(env, tag="sync_docs", dry_run=True)
    except Exception as exc:
        if json_mode:
            _err_json("Failed to compute documentation sync plan.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ----------------------------------------------------------------------
    # DRY-RUN — stop here
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
        print("       THN SYNC DOCS via SYNC V2 (DRY RUN)")
        print("==========================================\n")

        print("Envelope Inspection:\n")
        print(json.dumps(inspection, indent=4, ensure_ascii=False))

        print("\nExecution Plan:\n")
        print(json.dumps(plan, indent=4, ensure_ascii=False))
        print()
        return 0

    # ----------------------------------------------------------------------
    # APPLY — authoritative engine path
    # ----------------------------------------------------------------------
    try:
        target = DocsSyncTarget()
        apply_result = apply_envelope_v2(
            env,
            target=target,
            dry_run=False,
        )
    except Exception as exc:
        if json_mode:
            _err_json("Documentation sync apply failed.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ----------------------------------------------------------------------
    # Success output
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
    print("        THN SYNC DOCS via SYNC V2 (APPLY)")
    print("==========================================\n")

    print("Envelope Inspection:\n")
    print(json.dumps(inspection, indent=4, ensure_ascii=False))

    print("\nExecution Plan:\n")
    print(json.dumps(plan, indent=4, ensure_ascii=False))

    print("\nApply Result:\n")
    print(json.dumps(apply_result, indent=4, ensure_ascii=False))

    print("\nTHN Sync Docs workflow complete.\n")
    return 0


# ---------------------------------------------------------------------------
# Subparser Registration
# ---------------------------------------------------------------------------


def add_subparser(sync_subparsers: argparse._SubParsersAction) -> None:
    """
    Registers:

        thn sync docs --input <folder-or-file> [--dry-run | --apply] [--json]
    """
    parser = sync_subparsers.add_parser(
        "docs",
        help="Sync documentation assets through Sync V2 routing and executor.",
        description=(
            "Package documentation input, build an envelope, inspect, route, "
            "generate a plan, and apply (or dry-run) via the Sync V2 engine."
        ),
    )

    parser.add_argument(
        "--input",
        "--in",
        "-i",
        dest="input",
        required=True,
        help="Folder or file to package into a Sync V2 envelope.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate apply without modifying any files.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform a live apply (write files).",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of text output.",
    )

    parser.set_defaults(func=run_sync_docs)
