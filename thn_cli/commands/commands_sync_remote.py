# thn_cli/commands_sync_remote.py
"""
THN Sync Remote Command (Hybrid-Standard)
-----------------------------------------

Modernized workflow for:

    thn sync-remote web  --input <path> --url <url> [--dry-run | --apply] [--json]
    thn sync-remote cli  --input <path> --url <url> [--dry-run | --apply] [--json]
    thn sync-remote docs --input <path> --url <url> [--dry-run | --apply] [--json]

Pipeline:
    1. Build test envelope (local ZIP → Sync V2 envelope)
    2. Inspect envelope locally
    3. Compute routing + execution plan locally
    4. Perform CDC-delta negotiation with remote
    5. Upload missing chunks
    6. Instruct remote to apply or dry-run

This file replaces legacy implementations and provides full hybrid support.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from thn_cli.syncv2.envelope import inspect_envelope, load_envelope_from_file
from thn_cli.syncv2.executor import execute_envelope_plan
from thn_cli.syncv2.make_test import make_test_envelope
from thn_cli.syncv2.remote_client import (negotiate_remote_cdc,
                                          remote_apply_envelope,
                                          upload_missing_chunk)

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
# Remote Sync Core
# ---------------------------------------------------------------------------


def _run_remote(
    *,
    args: argparse.Namespace,
    target_name: str,
) -> int:
    """
    Shared hybrid-standard remote sync implementation.

    Steps:
        • Build envelope
        • Inspect locally
        • Generate execution plan
        • Negotiate CDC-delta with remote
        • Upload missing chunks
        • Trigger remote apply/dry-run
    """

    input_path = args.input
    remote_url = args.url
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
        dry = True

    # ------------------------------------------------------------------
    # Step 1 — Build test envelope
    # ------------------------------------------------------------------
    try:
        env_info = make_test_envelope(input_path)
        env_zip = env_info.get("envelope_zip")
        if not env_zip:
            raise RuntimeError("Envelope generator returned no 'envelope_zip'.")
    except Exception as exc:
        if json_mode:
            _err_json("Failed to create remote envelope.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ------------------------------------------------------------------
    # Step 2 — Load envelope
    # ------------------------------------------------------------------
    try:
        env = load_envelope_from_file(env_zip)
    except Exception as exc:
        if json_mode:
            _err_json("Failed to load envelope.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ------------------------------------------------------------------
    # Step 3 — Local inspection
    # ------------------------------------------------------------------
    try:
        inspection = inspect_envelope(env)
    except Exception as exc:
        if json_mode:
            _err_json("Failed to inspect envelope.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ------------------------------------------------------------------
    # Step 4 — Local routing + execution plan
    # ------------------------------------------------------------------
    try:
        plan = execute_envelope_plan(
            env, tag=f"sync_remote_{target_name}", dry_run=True
        )
    except Exception as exc:
        if json_mode:
            _err_json("Failed to compute remote sync plan.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    # ------------------------------------------------------------------
    # Step 5 — CDC-delta negotiation
    # ------------------------------------------------------------------
    try:
        negotiation = negotiate_remote_cdc(
            env=env,
            target_name=target_name,
            url=remote_url,
        )
    except Exception as exc:
        if json_mode:
            _err_json("CDC negotiation failed.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    missing_chunks = negotiation.get("missing", [])
    uploaded_chunks: Dict[str, str] = {}

    # Upload missing chunks
    for cid in missing_chunks:
        try:
            local_bytes = negotiation["load_chunk"](cid)
            result = upload_missing_chunk(
                url=remote_url,
                target=target_name,
                chunk_id=cid,
                data=local_bytes,
            )
            uploaded_chunks[cid] = result
        except Exception as exc:
            if json_mode:
                _err_json("Chunk upload failed.", chunk_id=cid, error=str(exc))
            else:
                _err_text(f"Chunk upload failed for {cid}: {exc}")
            return 1

    # ------------------------------------------------------------------
    # DRY-RUN STOP BEFORE APPLY
    # ------------------------------------------------------------------
    if dry:
        result = {
            "status": "DRY_RUN",
            "input": input_path,
            "remote_url": remote_url,
            "target": target_name,
            "inspection": inspection,
            "plan": plan,
            "cdc_negotiation": negotiation,
            "chunks_uploaded": uploaded_chunks,
        }
        if json_mode:
            _out_json(result)
            return 0

        # Text
        print("\n==========================================")
        print(f"   THN SYNC REMOTE ({target_name}) — DRY RUN")
        print("==========================================\n")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        print()
        return 0

    # ------------------------------------------------------------------
    # Step 6 — Remote apply
    # ------------------------------------------------------------------
    try:
        remote_apply = remote_apply_envelope(
            envelope_zip=env_zip,
            url=remote_url,
            target_name=target_name,
        )
    except Exception as exc:
        if json_mode:
            _err_json("Remote apply failed.", error=str(exc))
        else:
            _err_text(str(exc))
        return 1

    final = {
        "status": "OK",
        "input": input_path,
        "remote_url": remote_url,
        "target": target_name,
        "inspection": inspection,
        "plan": plan,
        "cdc_negotiation": negotiation,
        "chunks_uploaded": uploaded_chunks,
        "remote_apply": remote_apply,
    }

    if json_mode:
        _out_json(final)
        return 0

    print("\n==========================================")
    print(f"      THN SYNC REMOTE ({target_name}) — APPLY")
    print("==========================================\n")
    print(json.dumps(final, indent=4, ensure_ascii=False))
    print("\nTHN Sync Remote workflow complete.\n")

    return 0


# ---------------------------------------------------------------------------
# Entrypoints
# ---------------------------------------------------------------------------


def run_sync_remote_web(args: argparse.Namespace) -> int:
    return _run_remote(args=args, target_name="web")


def run_sync_remote_cli(args: argparse.Namespace) -> int:
    return _run_remote(args=args, target_name="cli")


def run_sync_remote_docs(args: argparse.Namespace) -> int:
    return _run_remote(args=args, target_name="docs")


# ---------------------------------------------------------------------------
# Subparser Registration
# ---------------------------------------------------------------------------


def add_subparser(root_subparsers: argparse._SubParsersAction) -> None:
    parser = root_subparsers.add_parser(
        "sync-remote",
        help="Push Sync V2 envelopes to a remote THN Sync server.",
        description=(
            "Build envelope → inspect → route → negotiate CDC-delta → "
            "upload missing chunks → remote apply."
        ),
    )

    remote = parser.add_subparsers(
        title="sync-remote targets",
        dest="sync_remote_target",
        required=True,
    )

    def attach(name: str, handler):
        p = remote.add_parser(
            name,
            help=f"Remote sync for {name} target.",
        )
        p.add_argument(
            "--input",
            "--in",
            "-i",
            required=True,
            help="Folder or file to sync (zipped automatically).",
        )
        p.add_argument(
            "--url",
            "-u",
            required=True,
            help="Remote Sync server endpoint (e.g. http://host:8765).",
        )
        p.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate on remote without applying changes.",
        )
        p.add_argument(
            "--apply",
            action="store_true",
            help="Perform a live remote apply.",
        )
        p.add_argument(
            "--json",
            action="store_true",
            help="Emit structured JSON output.",
        )
        p.set_defaults(func=handler)

    attach("web", run_sync_remote_web)
    attach("cli", run_sync_remote_cli)
    attach("docs", run_sync_remote_docs)
