# thn_cli/commands/commands_init.py
"""
THN Init Command (Hybrid-Standard)
=================================

RESPONSIBILITIES
----------------
Defines the authoritative CLI entrypoint for initializing the THN
filesystem layout.

This module:
    • Owns the `thn init` command
    • Resolves canonical THN paths via get_thn_paths()
    • Creates required directories deterministically
    • Supports inspection-only and dry-run modes
    • Emits stable JSON output for automation and CI

SUPPORTED MODES
---------------
    thn init
        Create all required THN directories.

    thn init --show
        Display resolved THN paths without creating anything.

    thn init --no-create
        Simulate initialization without writing to disk.

INVARIANTS
----------
    • Directory creation MUST be all-or-nothing per invocation
    • No partial state should persist on failure
    • Path resolution is centralized in get_thn_paths()
    • Output MUST be deterministic and JSON-stable
    • All failures MUST raise CommandError

NON-GOALS
---------
    • Path policy decisions
    • Per-directory permission validation
    • Repair or migration of existing directories
    • Validation of downstream subsystem readiness

Those concerns belong to:
    • thn_cli.pathing
    • migration and recovery commands
    • future diagnostics tooling

CONTRACT STATUS
---------------
LOCKED CLI SURFACE

The JSON output emitted by `thn init` is an externally visible contract
relied upon by:
    • Automation scripts
    • Installers
    • CI pipelines
    • Future GUI initialization flows

Any change to:
    • keys
    • structure
    • semantic meaning

MUST be accompanied by updated golden tests or a versioned CLI change.
"""

from __future__ import annotations

import argparse
import json
import os

from thn_cli.contracts.errors import SYSTEM_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def _safe_make(path: str, created: list[str], simulate: bool) -> None:
    """
    Create a directory if it does not exist.

    CONTRACT
    --------
    • Deterministic
    • Side-effect free when simulate=True
    """
    if simulate:
        if not os.path.exists(path):
            created.append(path)
        return

    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        created.append(path)


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------


def run_init(args: argparse.Namespace) -> int:
    simulate = bool(args.no_create)
    show_only = bool(args.show)

    try:
        paths = get_thn_paths()
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to resolve THN paths.",
        ) from exc

    # SHOW MODE (inspection-only)
    if show_only:
        print(
            json.dumps(
                {
                    "status": "SHOW",
                    "paths": paths,
                },
                indent=4,
            )
        )
        return 0

    created: list[str] = []

    try:
        for path in paths.values():
            _safe_make(path, created, simulate)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Initialization failed while creating directories.",
        ) from exc

    status = "DRY_RUN" if simulate else "OK"

    print(
        json.dumps(
            {
                "status": status,
                "created": created,
                "paths": paths,
            },
            indent=4,
        )
    )

    return 0


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the `thn init` command.
    """
    parser = subparsers.add_parser(
        "init",
        help="Initialize THN system folders.",
        description=(
            "Creates core, sync, routing, blueprints, hub, plugin, and state "
            "directories according to Hybrid-Standard pathing rules."
        ),
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help="Display resolved THN paths without creating anything.",
    )

    parser.add_argument(
        "--no-create",
        action="store_true",
        help="Simulate folder creation without writing to disk.",
    )

    parser.set_defaults(func=run_init)
