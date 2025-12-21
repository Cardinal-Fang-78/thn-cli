from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.presentation.snapshots import present_compare_status, present_snapshot_changes
from thn_cli.snapshots.diff_engine import diff_snapshots
from thn_cli.snapshots.snapshot_store import default_snapshot_root, read_snapshot

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _emit(obj: Dict[str, Any]) -> int:
    print(json.dumps(obj, indent=4))
    return 0


def _normalize_snapshot_id(value: str) -> str:
    v = (value or "").strip()
    return v[:-5] if v.endswith(".json") else v


def _load_snapshot(scaffold_root: Path, snap_id: str) -> Dict[str, Any]:
    snap_root = default_snapshot_root(scaffold_root.resolve())
    sid = _normalize_snapshot_id(snap_id)

    if not snap_root.exists():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"No snapshots exist for this scaffold: {snap_root}",
        )

    try:
        data = read_snapshot(snap_root, sid)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"Failed to read snapshot: {sid}",
        ) from exc

    if not data:
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Snapshot not found: {sid}",
        )

    return data


def _extract_paths(items: Any) -> List[str]:
    """
    Accept either:
      - ["a", "b"]
      - [{"path": "a"}, {"path": "b"}]

    This exists only to support legacy golden snapshots.
    """
    out: List[str] = []

    if isinstance(items, list):
        for x in items:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict) and isinstance(x.get("path"), str):
                out.append(str(x["path"]))

    return out


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


def run_snapshots_diff(args: argparse.Namespace) -> int:
    root = Path(args.path)

    if not root.exists():
        raise CommandError(USER_CONTRACT, f"Path does not exist: {root}")
    if not root.is_dir():
        raise CommandError(USER_CONTRACT, f"Path is not a directory: {root}")

    before = _load_snapshot(root, args.before)
    after = _load_snapshot(root, args.after)

    diff = diff_snapshots(before=before, after=after)

    added = _extract_paths(diff.get("added"))
    removed = _extract_paths(diff.get("removed"))

    changes = present_snapshot_changes(
        added=added,
        removed=removed,
    )

    payload: Dict[str, Any] = {
        "status": present_compare_status(has_changes=bool(changes)),
        "path": str(root.resolve()),
        "before": _normalize_snapshot_id(args.before),
        "after": _normalize_snapshot_id(args.after),
        "change_count": len(changes),
        "changes": changes,
    }

    if args.summary:
        payload["summary"] = {
            "added_count": len(added),
            "removed_count": len(removed),
        }

    return _emit(payload)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "diff",
        help="Compare two snapshots for a scaffold.",
        description="Show structural differences between two snapshots.",
    )
    p.add_argument("path", help="Scaffold directory.")
    p.add_argument("before", help="Earlier snapshot id or filename.")
    p.add_argument("after", help="Later snapshot id or filename.")
    p.add_argument(
        "--summary",
        action="store_true",
        help="Include a small added/removed summary block in the output.",
    )
    p.set_defaults(func=run_snapshots_diff)
