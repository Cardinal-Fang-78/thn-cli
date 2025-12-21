# thn_cli/commands_sync_status.py

"""
THN Sync Status (Hybrid-Standard)
---------------------------------

Provides:

    thn sync-status history   [--target <name>] [--limit N] [--json]
    thn sync-status last      [--target <name>] [--json]
    thn sync-status show      <id> [--json]
    thn sync-status rollback  <id> [--json]

Hybrid-Standard upgrades:

    • Unified text/JSON output layer
    • Normalized error formatting
    • Rollback now returns structured status
    • Safer rollback preflight validation
    • Same output conventions as remote/cli/docs/web sync
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional

from thn_cli.syncv2 import status_db
from thn_cli.syncv2.utils.fs_ops import restore_backup_zip

# ---------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------


def _jprint(obj: Any) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _err_json(msg: str, **fields: Any) -> int:
    obj = {"status": "ERROR", "message": msg}
    obj.update(fields)
    _jprint(obj)
    return 1


def _err_text(msg: str) -> int:
    print(f"Error: {msg}\n")
    return 1


def _hdr(label: str) -> None:
    print()
    print("==========================================")
    print(f"   {label}")
    print("==========================================")
    print()


def _row_to_text(row: Dict[str, Any]) -> None:
    print(
        f"[{row['id']}] {row['ts']}  "
        f"target={row['target']}  mode={row['mode']}  "
        f"op={row['operation']}  success={bool(row['success'])}  "
        f"dry_run={bool(row['dry_run'])}"
    )
    print(f"    destination : {row.get('destination')}")
    print(f"    file_count  : {row.get('file_count')}")
    print(f"    total_size  : {row.get('total_size')}")
    print(f"    manifest    : {row.get('manifest_hash')}")
    print(f"    backup_zip  : {row.get('backup_zip')}")
    print(f"    envelope    : {row.get('envelope_path')}")
    print(f"    source_root : {row.get('source_root')}")
    notes = row.get("notes")
    if notes:
        print(f"    notes       : {notes}")
    print()


# ---------------------------------------------------------------------
# history
# ---------------------------------------------------------------------


def run_history(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)
    target = args.target
    limit = args.limit

    entries = status_db.get_history(target=target, limit=limit)

    if json_mode:
        return (
            _err_json("No history entries found.")
            if not entries
            else (
                _jprint(
                    {
                        "status": "OK",
                        "count": len(entries),
                        "entries": entries,
                    }
                )
                or 0
            )
        )

    _hdr("THN Sync Status : History")

    if not entries:
        print("No history entries found.")
        return 0

    for row in entries:
        _row_to_text(row)

    return 0


# ---------------------------------------------------------------------
# last
# ---------------------------------------------------------------------


def run_last(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)
    target = args.target

    row = status_db.get_last(target=target)

    if json_mode:
        return (
            _err_json("No entries found.")
            if row is None
            else (_jprint({"status": "OK", "entry": row}) or 0)
        )

    _hdr("THN Sync Status : Last Entry")

    if row is None:
        print("No entries found.")
        return 0

    _row_to_text(row)
    return 0


# ---------------------------------------------------------------------
# show
# ---------------------------------------------------------------------


def run_show(args: argparse.Namespace) -> int:
    entry_id = int(args.id)
    json_mode = bool(args.json)

    row = status_db.get_entry_by_id(entry_id)

    if json_mode:
        return (
            _err_json(f"No entry found with id {entry_id}")
            if row is None
            else (_jprint({"status": "OK", "entry": row}) or 0)
        )

    _hdr(f"THN Sync Status : Show Entry {entry_id}")

    if row is None:
        print(f"No entry found with id {entry_id}.")
        return 0

    _row_to_text(row)
    return 0


# ---------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------


def run_rollback(args: argparse.Namespace) -> int:
    entry_id = int(args.id)
    json_mode = bool(args.json)

    row = status_db.get_entry_by_id(entry_id)
    if row is None:
        return (
            _err_json(f"No entry found with id {entry_id}")
            if json_mode
            else _err_text(f"No entry found with id {entry_id}")
        )

    backup_zip = row.get("backup_zip")
    destination = row.get("destination")
    target = row.get("target") or "unknown"

    # Preflight validations
    if not backup_zip:
        msg = "Entry has no backup ZIP; rollback impossible."
        return _err_json(msg) if json_mode else _err_text(msg)
    if not destination:
        msg = "Entry has no destination path; rollback impossible."
        return _err_json(msg) if json_mode else _err_text(msg)

    # JSON-only mode: do not print headers
    if not json_mode:
        _hdr(f"THN Sync Status : Rollback from Entry {entry_id}")
        print("Restoring backup:")
        print(f"  backup_zip  : {backup_zip}")
        print(f"  destination : {destination}\n")

    # Perform rollback
    try:
        restore_backup_zip(backup_zip, destination)
    except Exception as exc:
        return (
            _err_json("Rollback failed", error=str(exc))
            if json_mode
            else (_err_text(f"Rollback failed: {exc}"))
        )

    # Record new history entry for rollback
    new_id = status_db.record_apply(
        target=target,
        mode="rollback",
        operation="rollback",
        dry_run=False,
        success=True,
        manifest_hash=row.get("manifest_hash"),
        envelope_path=None,
        source_root=row.get("source_root"),
        file_count=row.get("file_count"),
        total_size=row.get("total_size"),
        backup_zip=backup_zip,
        destination=destination,
        notes={"rolled_back_from_id": entry_id},
    )

    result = {
        "status": "OK",
        "rolled_back_from": entry_id,
        "new_history_entry": new_id,
        "backup_zip": backup_zip,
        "destination": destination,
        "target": target,
    }

    if json_mode:
        _jprint(result)
        return 0

    print("Rollback completed successfully.\n")
    print("New rollback entry recorded:")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    print()

    return 0


# ---------------------------------------------------------------------
# Sync status root
# ---------------------------------------------------------------------


def run_sync_status_root(_args: argparse.Namespace) -> int:
    raise ValueError(
        "Missing sync-status subcommand. " "Run `thn sync-status --help` to see available options."
    )


# ---------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------


def add_subparser(root_subparsers: argparse._SubParsersAction) -> None:
    parser = root_subparsers.add_parser(
        "sync-status",
        help="View and manage THN Sync V2 history.",
        description="History, inspection, and rollback utilities for Sync V2.",
    )

    parser.set_defaults(func=run_sync_status_root)

    sub = parser.add_subparsers(
        title="sync-status commands",
        dest="sync_status_command",
        required=True,
    )

    # history
    p_hist = sub.add_parser("history", help="List recent sync operations.")
    p_hist.add_argument("--target", help="Filter by target (web, cli, docs).")
    p_hist.add_argument("--limit", type=int, default=50)
    p_hist.add_argument("--json", action="store_true")
    p_hist.set_defaults(func=run_history)

    # last
    p_last = sub.add_parser("last", help="Show most recent sync operation.")
    p_last.add_argument("--target")
    p_last.add_argument("--json", action="store_true")
    p_last.set_defaults(func=run_last)

    # show
    p_show = sub.add_parser("show", help="Show a specific history entry.")
    p_show.add_argument("id")
    p_show.add_argument("--json", action="store_true")
    p_show.set_defaults(func=run_show)

    # rollback
    p_rb = sub.add_parser("rollback", help="Rollback using entry's backup ZIP.")
    p_rb.add_argument("id")
    p_rb.add_argument("--json", action="store_true")
    p_rb.set_defaults(func=run_rollback)
