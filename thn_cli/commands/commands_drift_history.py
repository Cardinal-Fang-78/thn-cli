from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.scaffolds.drift_history import build_drift_history


def _emit(obj: Dict[str, Any]) -> int:
    print(json.dumps(obj, indent=4))
    return 0


def run_drift_history(args: argparse.Namespace) -> int:
    root = Path(args.path)

    if not root.exists():
        raise CommandError(USER_CONTRACT, f"Path does not exist: {root}")
    if not root.is_dir():
        raise CommandError(USER_CONTRACT, f"Path is not a directory: {root}")

    paths = get_thn_paths()
    thn_root = paths.get("root", "")
    if isinstance(thn_root, str) and thn_root.strip():
        try:
            root.resolve().relative_to(Path(thn_root).resolve())
        except Exception:
            raise CommandError(
                USER_CONTRACT,
                f"Target is not under THN root: {root} (root={thn_root})",
            )

    try:
        history = build_drift_history(root)
    except Exception as exc:
        raise CommandError(
            SYSTEM_CONTRACT,
            "Failed to build drift history.",
        ) from exc

    return _emit(
        {
            "status": "OK",
            "path": str(root.resolve()),
            "count": len(history),
            "history": history,
        }
    )


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "history",
        help="Show drift history timeline for a scaffold.",
        description="View accepted drift and migration history in chronological order.",
    )
    p.add_argument("path", help="Scaffold directory.")
    p.set_defaults(func=run_drift_history)
