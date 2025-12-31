# thn_cli/commands/commands_sync.py
"""
C:\\thn\\core\\cli\\thn_cli\\commands\\commands_sync.py
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.syncv2.delta.inspectors import check_payload_completeness
from thn_cli.syncv2.engine import apply_envelope_v2, validate_envelope
from thn_cli.syncv2.envelope import inspect_envelope, load_envelope_from_file
from thn_cli.syncv2.history_read import read_unified_history
from thn_cli.syncv2.history_strict import evaluate_strict_diagnostics
from thn_cli.syncv2.make_test import make_test_envelope
from thn_cli.syncv2.manifest import summarize_cdc_files, summarize_manifest
from thn_cli.syncv2.targets.cli import CLISyncTarget
from thn_cli.txlog.history_reader import (
    HistoryQuery,
    find_scaffold_root,
    load_sync_history,
    render_history_text,
)

from .commands_sync_cli import add_subparser as add_cli_subparser
from .commands_sync_docs import add_subparser as add_docs_subparser
from .commands_sync_status import add_subparser as add_status_subparser
from .commands_sync_web import add_subparser as add_web_subparser


def _out_json(obj: Any) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Destination Resolution (LOCKED)
# ---------------------------------------------------------------------------


def _default_apply_dest_root() -> Path:
    env_base = os.environ.get("PYTEST_TMPDIR")
    if env_base:
        base = Path(env_base).expanduser()
        base.mkdir(parents=True, exist_ok=True)
        return base / "thn-sync-apply"

    return Path(tempfile.gettempdir()) / "thn-sync-apply"


def _resolve_apply_destination(dest_arg: Optional[str]) -> Dict[str, Any]:
    if dest_arg:
        dest = Path(dest_arg).expanduser()
        return {"destination": str(dest), "mode": "explicit"}

    dest = _default_apply_dest_root()
    dest.mkdir(parents=True, exist_ok=True)
    return {"destination": str(dest), "mode": "temporary"}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_sync_inspect(args: argparse.Namespace) -> int:
    path = args.zip

    if not os.path.isfile(path):
        raise CommandError(
            contract=USER_CONTRACT,
            message="Envelope file not found.",
            extra_suggestions=[f"Provided path: {path}"],
        )

    try:
        env = load_envelope_from_file(path)
        env_info = inspect_envelope(env)

        manifest = env.get("manifest", {}) or {}
        summary = summarize_manifest(manifest)
        cdc_files = summarize_cdc_files(manifest, max_items=200)

        validation = validate_envelope(env)

        envelope_block: Dict[str, Any] = {
            "source_path": env_info.get("source_path"),
            "work_dir": env_info.get("work_dir"),
            "payload_zip": env_info.get("payload_zip"),
            "has_payload": env_info.get("has_payload"),
        }

        validation_block: Dict[str, Any] = {
            "valid": bool(validation.get("valid", True)),
            "errors": list(validation.get("errors", [])),
            "payload_sha256": validation.get("hash"),
        }

        # Legacy / locked inspect surface (what goldens and consumers expect)
        inspect_block: Dict[str, Any] = {
            "envelope": envelope_block,
            "manifest": manifest,
            "manifest_summary": summary,
            "validation": validation_block,
        }

        if cdc_files.get("present"):
            inspect_block["cdc_files"] = cdc_files
            inspect_block["cdc_diagnostics"] = {
                "payload_completeness": check_payload_completeness(
                    manifest=manifest,
                    payload_zip=env_info.get("payload_zip"),
                )
            }

        # Additive forward-safe overlay (do not remove or rename legacy fields)
        diagnostics_overlay: Dict[str, Any] = {
            "validation": validation_block,
        }
        if "cdc_files" in inspect_block:
            diagnostics_overlay["cdc_files"] = inspect_block["cdc_files"]
        if "cdc_diagnostics" in inspect_block:
            diagnostics_overlay["cdc_diagnostics"] = inspect_block["cdc_diagnostics"]

        inspect_block["structure"] = {
            "envelope": envelope_block,
            "manifest": manifest,
            "manifest_summary": summary,
        }
        inspect_block["diagnostics"] = diagnostics_overlay

    except CommandError:
        raise
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to inspect envelope.",
            extra_suggestions=[str(exc)],
        ) from exc

    if args.json:
        _out_json(
            {
                "scope": "diagnostic",
                "status": "OK",
                "inspect": inspect_block,
            }
        )
        return 0

    print(json.dumps(inspect_block, indent=4, ensure_ascii=False))
    print()
    return 0


def run_sync_apply(args: argparse.Namespace) -> int:
    path = args.zip
    dry = bool(args.dry_run)

    if not os.path.isfile(path):
        raise CommandError(
            contract=USER_CONTRACT,
            message="Envelope file not found.",
            extra_suggestions=[f"Provided path: {path}"],
        )

    destination = None
    try:
        env = load_envelope_from_file(path)

        dest_info = _resolve_apply_destination(args.dest)
        destination = dest_info["destination"]
        backup_root = str(Path(destination) / "_backups")

        target = CLISyncTarget(destination, backup_root=backup_root)

        result = apply_envelope_v2(
            env,
            target=target,
            dry_run=dry,
        )

    except CommandError:
        raise
    except Exception as exc:
        extra = [str(exc)]
        if destination:
            extra.append(f"Destination: {destination}")
        extra.append(
            "If this is a permissions error, pass an explicit writable destination via --dest."
        )
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Sync apply failed.",
            extra_suggestions=extra,
        ) from exc

    if args.json:
        _out_json(result)
        return 0

    print(json.dumps(result, indent=4, ensure_ascii=False))
    print()
    return 0


def run_sync_history(args: argparse.Namespace) -> int:
    limit = int(args.limit) if args.limit is not None else 50
    if limit <= 0:
        limit = 50

    scaffold_arg = args.scaffold
    if scaffold_arg:
        scaffold_root = Path(scaffold_arg).expanduser()
    else:
        found = find_scaffold_root(Path.cwd())
        scaffold_root = found if found is not None else Path.cwd()

    if args.unified:
        if not args.json:
            raise CommandError(
                contract=USER_CONTRACT,
                message="Unified history requires --json.",
            )

        query = HistoryQuery(
            limit=limit,
            target=str(args.target) if args.target else None,
            tx_id=str(args.tx_id) if args.tx_id else None,
        )

        history = read_unified_history(
            scaffold_root=scaffold_root,
            txlog_query=query,
        )

        if args.strict:
            history = dict(history)
            history["strict"] = evaluate_strict_diagnostics(history)

        _out_json(history)
        return 0

    # ------------------------------------------------------------------
    # TXLOG-only (existing behavior, unchanged)
    # ------------------------------------------------------------------

    query = HistoryQuery(
        limit=limit,
        target=str(args.target) if args.target else None,
        tx_id=str(args.tx_id) if args.tx_id else None,
    )

    try:
        result = load_sync_history(scaffold_root=scaffold_root, query=query)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to read sync history.",
            extra_suggestions=[str(exc)],
        ) from exc

    if args.json:
        _out_json(result)
        return 0

    print(render_history_text(result))
    print()
    return 0


def run_sync_make_test(args: argparse.Namespace) -> int:
    in_path = args.in_path

    if not os.path.isdir(in_path):
        raise CommandError(
            contract=USER_CONTRACT,
            message="Input folder does not exist.",
            extra_suggestions=[f"Provided path: {in_path}"],
        )

    try:
        result = make_test_envelope(in_path)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to generate test envelope.",
            extra_suggestions=[str(exc)],
        ) from exc

    if args.json:
        _out_json({"status": "OK", "result": result})
        return 0

    print(json.dumps(result, indent=4, ensure_ascii=False))
    print()
    return 0


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "sync",
        help="Sync V2 envelope utilities.",
    )

    sync_sub = parser.add_subparsers(dest="sync_command", required=True)

    p_inspect = sync_sub.add_parser("inspect")
    p_inspect.add_argument("zip")
    p_inspect.add_argument("--json", action="store_true")
    p_inspect.set_defaults(func=run_sync_inspect)

    p_apply = sync_sub.add_parser("apply")
    p_apply.add_argument("zip")
    p_apply.add_argument("--dest", help="Explicit destination directory")
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.add_argument("--json", action="store_true")
    p_apply.set_defaults(func=run_sync_apply)

    p_history = sync_sub.add_parser(
        "history",
        help="Show Sync V2 transaction history (read-only).",
    )
    p_history.add_argument(
        "--scaffold",
        help="Scaffold root to read .thn/txlog from. If omitted, search upward from CWD.",
    )
    p_history.add_argument("--limit", type=int, default=50)
    p_history.add_argument("--target")
    p_history.add_argument("--tx-id", dest="tx_id")
    p_history.add_argument("--json", action="store_true")
    p_history.add_argument(
        "--unified",
        action="store_true",
        help="Emit unified status + txlog history (JSON-only).",
    )
    p_history.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict diagnostic evaluation (read-only).",
    )
    p_history.set_defaults(func=run_sync_history)

    p_test = sync_sub.add_parser("make-test")
    p_test.add_argument("--in", dest="in_path", required=True)
    p_test.add_argument("--json", action="store_true")
    p_test.set_defaults(func=run_sync_make_test)

    add_web_subparser(sync_sub)
    add_cli_subparser(sync_sub)
    add_docs_subparser(sync_sub)
    add_status_subparser(sync_sub)

    parser.set_defaults(func=lambda args: parser.print_help())
