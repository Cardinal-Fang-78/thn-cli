"""
THN Init Command (Hybrid-Standard)
----------------------------------

Initializes the full THN directory structure as defined by get_thn_paths().
Guarantees:

    • deterministic JSON output
    • no partial state on error
    • optional dry-run behavior
    • optional folder inspection mode

Command:

    thn init
    thn init --show        (shows resolved paths only)
    thn init --no-create   (simulate initialization without writing)
"""

from __future__ import annotations

import argparse
import os
import json

from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------------
# Core Implementation
# ---------------------------------------------------------------------------

def _safe_make(path: str, created: list, simulate: bool) -> None:
    """
    Create a directory unless simulate=True.
    Tracks newly created directories in `created`.
    """
    if simulate:
        if not os.path.exists(path):
            created.append(path)
        return

    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        created.append(path)


# ---------------------------------------------------------------------------
# Command Handler
# ---------------------------------------------------------------------------

def run_init(args: argparse.Namespace) -> int:
    """
    Initialize THN directory structures.
    """
    simulate = args.no_create
    show_only = args.show

    try:
        paths = get_thn_paths()
    except Exception as exc:
        print(json.dumps({
            "status": "ERROR",
            "message": "Failed to resolve THN paths.",
            "exception": str(exc),
        }, indent=4))
        return 1

    # SHOW MODE: no creation, no simulation — only display path map
    if show_only:
        print(json.dumps({
            "status": "SHOW",
            "paths": paths,
        }, indent=4))
        return 0

    created: list[str] = []

    # Attempt to create directories
    try:
        for name, path in paths.items():
            _safe_make(path, created, simulate)

        status = "DRY_RUN" if simulate else "OK"

        print(json.dumps({
            "status": status,
            "created": created,
            "paths": paths,
        }, indent=4))
        return 0

    except Exception as exc:
        print(json.dumps({
            "status": "ERROR",
            "message": "Initialization failed.",
            "exception": str(exc),
            "partial_created": created,
        }, indent=4))
        return 1


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------

def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """
    Register: thn init
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
