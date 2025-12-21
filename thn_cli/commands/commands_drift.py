# thn_cli/commands/commands_drift.py
"""
THN Drift Command Group (Hybrid-Standard)
========================================

RESPONSIBILITIES
----------------
Defines the authoritative CLI surface for scaffold drift inspection,
analysis, and control.

This module:
    • Owns the `thn drift` command group
    • Registers all drift-related subcommands
    • Provides the primary read-only drift preview entrypoint
    • Delegates specialized drift operations to submodules

Subcommands registered here include:
    • thn drift preview
    • thn drift diff
    • thn drift explain
    • thn drift history
    • thn drift accept

INVARIANTS
----------
    • Drift preview and analysis commands MUST be read-only
    • Filesystem mutation is ONLY permitted via `drift accept`
    • CLI output MUST remain deterministic and JSON-stable
    • All failures MUST raise CommandError with the correct contract
    • No inline printing of tracebacks or raw exceptions

NON-GOALS
---------
    • Drift detection logic
    • Diff computation algorithms
    • Drift persistence or history storage
    • Acceptance policy enforcement
    • Presentation formatting internals

These concerns are delegated to:
    • thn_cli.scaffolds.*
    • thn_cli.presentation.drift
    • thn_cli.commands.commands_drift_*

CONTRACT STATUS
---------------
LOCKED CLI SURFACE

The JSON structures emitted by:
    • run_drift_preview
    • subordinate drift subcommands

are externally visible contracts relied upon by:
    • CLI users
    • Automation
    • CI pipelines
    • Future GUI tooling

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

from thn_cli.commands.commands_drift_accept import add_subparser as add_accept_subparser
from thn_cli.commands.commands_drift_diff import add_subparser as add_diff_subparser
from thn_cli.commands.commands_drift_explain import add_subparser as add_explain_subparser
from thn_cli.commands.commands_drift_history import add_subparser as add_history_subparser
from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.presentation.drift import present_diff, present_notes, present_status
from thn_cli.scaffolds.drift_preview import preview_scaffold_drift

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _emit(obj: Dict[str, Any]) -> int:
    """
    Emit structured JSON output.

    CONTRACT
    --------
    • Deterministic
    • UTF-8 safe
    • Stable for golden tests and GUI consumers
    """
    print(json.dumps(obj, indent=4))
    return 0


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_drift_preview(args: argparse.Namespace) -> int:
    """
    Preview scaffold drift in a read-only manner.
    """
    target_path = Path(args.path)

    if not target_path.exists():
        raise CommandError(
            USER_CONTRACT,
            f"Path does not exist: {target_path}",
        )

    if not target_path.is_dir():
        raise CommandError(
            USER_CONTRACT,
            f"Path is not a directory: {target_path}",
        )

    paths = get_thn_paths()
    thn_root = paths.get("root", "")
    if isinstance(thn_root, str) and thn_root.strip():
        try:
            target_path.resolve().relative_to(Path(thn_root).resolve())
        except Exception:
            raise CommandError(
                USER_CONTRACT,
                f"Target is not under THN root: {target_path} (root={thn_root})",
            )

    try:
        raw = preview_scaffold_drift(target_path)
    except Exception as exc:
        raise CommandError(
            SYSTEM_CONTRACT,
            "Failed to preview scaffold drift.",
        ) from exc

    return _emit(
        {
            "status": present_status(raw["status"]),
            "path": raw["path"],
            "blueprint": raw.get("blueprint", {}),
            "changes": present_diff(raw.get("diff", [])),
            "notes": present_notes(raw.get("notes", [])),
        }
    )


# ---------------------------------------------------------------------------
# Command Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the `thn drift` command group.
    """
    parser = subparsers.add_parser(
        "drift",
        help="Drift inspection and control utilities.",
        description="Inspect, analyze, and intentionally accept scaffold drift.",
    )

    sub = parser.add_subparsers(dest="drift_cmd", required=True)

    # --- drift preview (read-only) ---
    p = sub.add_parser(
        "preview",
        help="Preview drift for a scaffold directory.",
    )
    p.add_argument("path", help="Scaffold directory to preview.")
    p.set_defaults(func=run_drift_preview)

    # --- drift diff (read-only) ---
    add_diff_subparser(sub)

    # --- drift explain (classified, read-only) ---
    add_explain_subparser(sub)

    # --- drift history (read-only timeline) ---
    add_history_subparser(sub)

    # --- drift accept (authoritative mutation) ---
    add_accept_subparser(sub)

    parser.set_defaults(func=lambda args: parser.print_help())
