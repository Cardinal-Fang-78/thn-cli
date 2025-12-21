from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.presentation.drift import present_diff, present_notes, present_status
from thn_cli.scaffolds.drift_explain import explain_scaffold_drift

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _emit(obj: Dict[str, Any]) -> int:
    print(json.dumps(obj, indent=4))
    return 0


def _ensure_under_thn_root(path: Path) -> None:
    paths = get_thn_paths()
    thn_root = paths.get("root", "")
    if isinstance(thn_root, str) and thn_root.strip():
        try:
            path.resolve().relative_to(Path(thn_root).resolve())
        except Exception:
            raise CommandError(
                contract=USER_CONTRACT,
                message=f"Target is not under THN root: {path} (root={thn_root})",
            )


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


def run_drift_explain(args: argparse.Namespace) -> int:
    target_path = Path(args.path)

    if not target_path.exists():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path does not exist: {target_path}",
        )

    if not target_path.is_dir():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path is not a directory: {target_path}",
        )

    _ensure_under_thn_root(target_path)

    try:
        result = explain_scaffold_drift(target_path)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to explain scaffold drift.",
        ) from exc

    diff = result.get("diff", [])
    notes = result.get("notes", [])

    status_code = "clean" if not diff else "drifted"

    return _emit(
        {
            "status": present_status(status_code),
            "path": result.get("path"),
            "blueprint": result.get("blueprint", {}),
            "diff": present_diff(diff),
            "notes": present_notes(notes),
        }
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "explain",
        help="Explain scaffold drift decisions.",
        description="Explain drift classification and diff results for a scaffold.",
    )
    p.add_argument("path", help="Scaffold directory.")
    p.set_defaults(func=run_drift_explain)
