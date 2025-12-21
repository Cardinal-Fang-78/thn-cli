# thn_cli/commands/commands_snapshots.py
"""
THN Snapshots Command Group (Hybrid-Standard)
=============================================

RESPONSIBILITIES
----------------
Defines the authoritative CLI entrypoints for **immutable scaffold snapshots**.

This module:
    • Owns `thn snapshots list`
    • Owns `thn snapshots show`
    • Registers snapshot diff subcommands
    • Validates scaffold paths and snapshot identifiers
    • Loads snapshot metadata and contents
    • Emits structured, deterministic JSON output

SUPPORTED COMMANDS
------------------
    thn snapshots list <path>
    thn snapshots show <path> <snapshot_id>
    thn snapshots diff ...

INVARIANTS
----------
    • Target path MUST exist and be a directory
    • Target path MUST reside under THN root
    • Snapshot storage is immutable and read-only
    • Snapshot IDs are normalized ('.json' suffix optional)
    • Absence of snapshots is a valid, non-error state
    • All failures MUST raise CommandError

NON-GOALS
---------
    • Snapshot creation or mutation
    • Snapshot garbage collection
    • Snapshot rollback or replay
    • Enforcement of snapshot retention policy

Those responsibilities belong to:
    • snapshot writers (post-make, accept, migrate, etc.)
    • recovery / replay tooling
    • future GUI orchestration layers

CONTRACT STATUS
---------------
LOCKED CLI OUTPUT SURFACE

The JSON structures emitted by:
    • run_snapshots_list()
    • run_snapshots_show()

are externally visible and relied upon by:
    • Automation
    • CI
    • Golden tests
    • GUI consumers

Any changes to:
    • output keys
    • nesting structure
    • semantic meaning

MUST be accompanied by updated golden tests or a versioned CLI change.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from thn_cli.commands.commands_snapshots_diff import add_subparser as add_diff_subparser
from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.snapshots.snapshot_store import default_snapshot_root, list_snapshots, read_snapshot

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _emit(obj: Dict[str, Any]) -> int:
    """
    Emit structured JSON output.

    CONTRACT
    --------
    Output must remain deterministic and stable.
    """
    print(json.dumps(obj, indent=4))
    return 0


def _ensure_under_thn_root(target_path: Path) -> None:
    paths = get_thn_paths()
    thn_root = paths.get("root", "")
    if isinstance(thn_root, str) and thn_root.strip():
        try:
            target_path.resolve().relative_to(Path(thn_root).resolve())
        except Exception:
            raise CommandError(
                contract=USER_CONTRACT,
                message=f"Target is not under THN root: {target_path} (root={thn_root})",
            )


def _normalize_snapshot_id(val: str) -> str:
    """
    Normalize snapshot identifier.

    Accepts either:
        • bare snapshot ID
        • snapshot ID with '.json' suffix
    """
    v = (val or "").strip()
    if v.endswith(".json"):
        v = v[:-5]
    return v


def _snapshot_root(scaffold_root: Path) -> Path:
    """
    Resolve the snapshot root for a scaffold.

    Canonical location:
        <scaffold_root>/.thn/snapshots
    """
    return default_snapshot_root(scaffold_root.resolve())


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_snapshots_list(args: argparse.Namespace) -> int:
    root = Path(args.path)

    if not root.exists():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path does not exist: {root}",
        )
    if not root.is_dir():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path is not a directory: {root}",
        )

    _ensure_under_thn_root(root)

    snap_root = _snapshot_root(root)
    if not snap_root.exists():
        return _emit(
            {
                "status": {
                    "code": "no_snapshots",
                    "message": "No snapshots exist for this scaffold",
                },
                "path": str(root.resolve()),
                "snapshots_root": str(snap_root),
                "count": 0,
                "snapshots": [],
            }
        )

    snaps: List[str] = list_snapshots(snap_root)

    return _emit(
        {
            "status": {
                "code": "snapshots_available" if snaps else "no_snapshots",
                "message": (
                    "Snapshots are available for this scaffold"
                    if snaps
                    else "No snapshots exist for this scaffold"
                ),
            },
            "path": str(root.resolve()),
            "snapshots_root": str(snap_root),
            "count": len(snaps),
            "snapshots": snaps,
        }
    )


def run_snapshots_show(args: argparse.Namespace) -> int:
    root = Path(args.path)

    if not root.exists():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path does not exist: {root}",
        )
    if not root.is_dir():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path is not a directory: {root}",
        )

    _ensure_under_thn_root(root)

    snap_root = _snapshot_root(root)
    snap_id = _normalize_snapshot_id(args.id)

    try:
        data: Optional[Dict[str, Any]] = (
            read_snapshot(snap_root, snap_id) if snap_root.exists() else None
        )
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"Failed to read snapshot JSON: {snap_id}",
        ) from exc

    if not data:
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Snapshot not found: {snap_id}",
        )

    return _emit(
        {
            "status": {
                "code": "snapshot_loaded",
                "message": "Snapshot loaded successfully",
            },
            "path": str(root.resolve()),
            "snapshots_root": str(snap_root),
            "snapshot_id": snap_id,
            "snapshot": data,
        }
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "snapshots",
        help="Snapshot history utilities.",
        description="View and compare immutable scaffold snapshots.",
    )

    sub = parser.add_subparsers(dest="snap_cmd", required=True)

    # --- snapshots list ---
    p_list = sub.add_parser(
        "list",
        help="List snapshots for a scaffold.",
    )
    p_list.add_argument("path", help="Scaffold directory.")
    p_list.set_defaults(func=run_snapshots_list)

    # --- snapshots show ---
    p_show = sub.add_parser(
        "show",
        help="Show the contents of a snapshot.",
    )
    p_show.add_argument("path", help="Scaffold directory.")
    p_show.add_argument("id", help="Snapshot id or filename.")
    p_show.set_defaults(func=run_snapshots_show)

    # --- snapshots diff ---
    add_diff_subparser(sub)

    parser.set_defaults(func=lambda a: parser.print_help())
