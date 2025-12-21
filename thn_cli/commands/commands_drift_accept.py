from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.post_make.accept import accept_drift
from thn_cli.post_make.errors import PostMakeVerificationError


def _emit(obj: Dict[str, Any]) -> int:
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


def run_drift_accept(args: argparse.Namespace) -> int:
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

    note: Optional[str] = getattr(args, "note", None)

    try:
        result = accept_drift(root=target_path, note=note)

    except PostMakeVerificationError as exc:
        raise CommandError(
            contract=USER_CONTRACT,
            message=str(exc),
        ) from exc

    except CommandError:
        raise

    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to accept scaffold drift.",
        ) from exc

    payload: Dict[str, Any] = {
        "status": {
            "code": "accepted",
            "message": "Drift accepted and baseline updated",
        },
        "path": result.get("path", str(target_path)),
        "accepted_at": result.get("accepted_at", ""),
        "path_count": int(result.get("path_count", 0) or 0),
    }

    if note:
        payload["note"] = note

    return _emit(payload)


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "accept",
        help="Accept current filesystem state as the new expected scaffold state.",
        description=(
            "Accept current drift by writing a new expected baseline "
            "and capturing an immutable snapshot."
        ),
    )
    p.add_argument("path", help="Scaffold directory.")
    p.add_argument(
        "--note",
        help="Optional note to record alongside the acceptance event.",
        default=None,
    )
    p.set_defaults(func=run_drift_accept)
