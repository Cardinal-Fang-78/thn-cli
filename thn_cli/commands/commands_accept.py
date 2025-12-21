# thn_cli/commands/commands_accept.py
"""
THN Accept Commands (Hybrid-Standard)
=====================================

RESPONSIBILITIES
----------------
Defines CLI commands for accepting *intentional scaffold drift*.

This module:
    • Exposes `thn accept drift`
    • Validates target paths and THN-root constraints
    • Delegates drift acceptance to post-make logic
    • Emits deterministic, structured JSON output

This command represents a **state mutation boundary**:
    it intentionally updates the expected scaffold state.

INVARIANTS
----------
    • Target path MUST exist
    • Target path MUST be a directory
    • Target path MUST reside under the THN root
    • Errors MUST surface via CommandError
    • Output MUST remain JSON-stable for automation

NON-GOALS
---------
    • Drift detection or diffing
    • Scaffold inspection
    • Migration logic
    • Registry or snapshot management
    • Any filesystem mutation beyond delegated accept logic

CONTRACT STATUS
---------------
LOCKED CLI SURFACE

The JSON output of `run_accept_drift` is externally visible and relied upon by:
    • CLI users
    • CI pipelines
    • Automation / scripting

Any changes to:
    • keys
    • nesting
    • semantics

MUST be accompanied by updated golden tests or a versioned CLI change.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.post_make.accept import accept_drift

# ---------------------------------------------------------------------------
# Output Helper
# ---------------------------------------------------------------------------


def _emit(obj: Dict[str, Any]) -> int:
    """
    Emit structured JSON output.

    CONTRACT
    --------
    • Deterministic
    • UTF-8 safe
    • Stable for golden tests and automation
    """
    print(json.dumps(obj, indent=4))
    return 0


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_accept_drift(args: argparse.Namespace) -> int:
    """
    Accept intentional drift for a scaffold directory.

    Promotes the current on-disk state to the new expected scaffold.
    """
    target = Path(args.path)

    if not target.exists():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path does not exist: {target}",
        )

    if not target.is_dir():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path is not a directory: {target}",
        )

    paths = get_thn_paths()
    thn_root = paths.get("root")
    if isinstance(thn_root, str) and thn_root.strip():
        try:
            target.resolve().relative_to(Path(thn_root).resolve())
        except Exception:
            raise CommandError(
                contract=USER_CONTRACT,
                message=("Target is not under THN root. " f"target={target} thn_root={thn_root}"),
            )

    try:
        result = accept_drift(root=target, note=args.note)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to accept drift.",
        ) from exc

    return _emit(
        {
            "command": "accept drift",
            "status": "OK",
            "result": result,
        }
    )


# ---------------------------------------------------------------------------
# Command Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the `thn accept` command group.
    """
    parser = subparsers.add_parser(
        "accept",
        help="Accept intentional scaffold drift.",
        description="Promote current filesystem state to the new expected scaffold.",
    )

    sub = parser.add_subparsers(dest="accept_cmd", required=True)

    p = sub.add_parser(
        "drift",
        help="Accept drift for a scaffold path.",
    )
    p.add_argument("path", help="Scaffold directory to accept drift for.")
    p.add_argument(
        "--note",
        help="Optional note describing why drift was accepted.",
        default=None,
    )
    p.set_defaults(func=run_accept_drift)

    parser.set_defaults(func=lambda a: parser.print_help())
