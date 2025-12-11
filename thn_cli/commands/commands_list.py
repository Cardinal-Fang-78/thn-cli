"""
THN Path Listing Command (Hybrid-Standard)
-----------------------------------------

Command:
    thn list

Displays all resolved THN paths as defined by the pathing subsystem.

Hybrid-Standard guarantees:
    • Deterministic JSON output
    • No ambiguous text
    • Stable field names for programmatic consumers
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------------
# JSON Output Helper
# ---------------------------------------------------------------------------

def _out(obj: Dict[str, Any]) -> None:
    print(json.dumps(obj, indent=4))


# ---------------------------------------------------------------------------
# Command Implementation
# ---------------------------------------------------------------------------

def run_list_paths(_: argparse.Namespace) -> int:
    """
    Return all resolved THN directories, normalized and ensured,
    as declared by the pathing subsystem.
    """
    paths = get_thn_paths()

    _out({
        "command": "list",
        "status": "OK",
        "paths": paths,
    })

    return 0


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------

def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "list",
        help="List all THN directories.",
        description=(
            "Displays all resolved and ensured THN directories from "
            "the pathing subsystem (Hybrid-Standard)."
        ),
    )

    parser.set_defaults(func=run_list_paths)
