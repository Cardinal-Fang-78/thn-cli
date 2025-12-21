# thn_cli/commands/commands_migrate.py
"""
THN Migrate Command Group (Hybrid-Standard)
==========================================

RESPONSIBILITIES
----------------
Defines the authoritative CLI entrypoint for **scaffold migration** between
blueprint versions.

This module:
    • Owns `thn migrate scaffold`
    • Validates target paths and blueprint identifiers
    • Resolves migration specifications from version-controlled specs
    • Computes deterministic migration plans
    • Delegates execution to the migration engine
    • Emits structured, stable JSON output

SUPPORTED COMMANDS
------------------
    thn migrate scaffold <path>
        --to blueprint_id@version
        [--dry-run]
        [--force]
        [--note TEXT]

INVARIANTS
----------
    • Target path MUST exist and be a directory
    • Target path MUST reside under THN root
    • Blueprint ID in manifest MUST match migration target
    • Migration specs are resolved from the CLI repository, not user state
    • Planning is deterministic and repeatable
    • All failures MUST raise CommandError
    • Dry-run MUST NOT mutate filesystem state

NON-GOALS
---------
    • Authoring or editing migration specifications
    • Drift acceptance or reconciliation
    • Repair or recovery of partially migrated scaffolds
    • Interactive conflict resolution

Those concerns belong to:
    • migration spec definitions
    • drift accept / recovery commands
    • future GUI orchestration layers

CONTRACT STATUS
---------------
LOCKED CLI OUTPUT SURFACE

The JSON structure emitted by:
    • run_migrate_scaffold()

is externally visible and relied upon by:
    • Automation scripts
    • CI pipelines
    • Golden tests
    • Future GUI tooling

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
from typing import Any, Dict

from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.migrations.engine import migrate_scaffold
from thn_cli.migrations.registry import MigrationRegistry
from thn_cli.pathing import get_thn_paths

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


def _parse_target(s: str) -> tuple[str, str]:
    """
    Parse a migration target specifier.

    Accepted forms:
        • "project_default@2"
        • "module_default@2"
    """
    if "@" not in s:
        raise ValueError("Target must be in form blueprint_id@version (e.g., project_default@2)")

    bid, ver = s.split("@", 1)
    bid = bid.strip()
    ver = ver.strip()

    if not bid or not ver:
        raise ValueError("Target must be in form blueprint_id@version (e.g., project_default@2)")

    return bid, ver


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_migrate_scaffold(args: argparse.Namespace) -> int:
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

    # Must be under THN root
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

    try:
        blueprint_id, to_version = _parse_target(args.to)
    except Exception as exc:
        raise CommandError(
            contract=USER_CONTRACT,
            message=str(exc),
        ) from exc

    # Migration specs live inside the CLI repository for determinism.
    specs_dir = Path(__file__).resolve().parents[1] / "migrations" / "specs"
    reg = MigrationRegistry(specs_dir=specs_dir)

    # Read current blueprint metadata from scaffold manifest
    manifest_path = target_path / ".thn-tree.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        cur_bp = data.get("blueprint", {})
        cur_id = cur_bp.get("id")
        cur_ver = cur_bp.get("version")

        if cur_id != blueprint_id:
            raise ValueError(
                f"Manifest blueprint id '{cur_id}' does not match "
                f"target blueprint '{blueprint_id}'"
            )

        if not isinstance(cur_ver, str) or not cur_ver.strip():
            raise ValueError("Manifest blueprint.version missing or invalid")

    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to read current blueprint version from manifest.",
        ) from exc

    try:
        plan = reg.plan(
            blueprint_id=blueprint_id,
            current=cur_ver,
            target=to_version,
        )
    except Exception as exc:
        raise CommandError(
            contract=USER_CONTRACT,
            message=str(exc),
        ) from exc

    try:
        result = migrate_scaffold(
            root=target_path,
            plan=plan,
            dry_run=bool(args.dry_run),
            note=args.note,
            force=bool(args.force),
        )

    except CommandError:
        # Propagate structured command errors unchanged
        raise

    except ValueError as exc:
        # Semantic / validation failures
        raise CommandError(
            contract=USER_CONTRACT,
            message=str(exc),
        ) from exc

    except Exception as exc:
        # Unexpected internal failures
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=(
                "Migration aborted due to an internal error. "
                "Run with THN_CLI_VERBOSE=1 for diagnostic details."
            ),
        ) from exc

    return _emit(
        {
            "command": "migrate scaffold",
            "status": "OK",
            "plan": {
                "blueprint_id": plan.blueprint_id,
                "from": plan.start.version,
                "to": plan.target.version,
                "hops": [f"{s.from_version}->{s.to_version}" for s in plan.specs],
            },
            "result": {
                "status": result.status,
                "path": result.path,
                "blueprint_id": result.blueprint_id,
                "from_version": result.from_version,
                "to_version": result.to_version,
                "dry_run": result.dry_run,
                "expected_count": result.expected_count,
                "applied": result.applied,
                "notes": result.notes,
            },
        }
    )


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "migrate",
        help="Migration utilities (scaffold upgrades).",
        description="Upgrade scaffolds between blueprint versions using Hybrid migrations.",
    )

    sub = parser.add_subparsers(dest="migrate_cmd", required=True)

    p = sub.add_parser(
        "scaffold",
        help="Migrate a scaffold directory in place.",
    )
    p.add_argument("path", help="Scaffold directory to migrate.")
    p.add_argument(
        "--to",
        required=True,
        help="Target blueprint_id@version (e.g., project_default@2).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and report without applying changes.",
    )
    p.add_argument(
        "--note",
        default=None,
        help="Optional note stored in manifest migration history.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if scaffold has unaccepted drift.",
    )
    p.set_defaults(func=run_migrate_scaffold)

    parser.set_defaults(func=lambda a: parser.print_help())
