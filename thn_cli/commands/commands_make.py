# thn_cli/commands/commands_make.py
"""
THN Make Command Group (Hybrid-Standard)
=======================================

RESPONSIBILITIES
----------------
Defines the authoritative CLI entrypoints for creating THN projects
and modules via blueprint scaffolding.

This module:
    • Owns `thn make project` and `thn make module`
    • Applies blueprint scaffolds deterministically
    • Persists scaffold identity and variables to the project registry
    • Updates the global THN registry
    • Wires post-make validation and policy hooks
    • Emits stable JSON output for CLI, CI, and GUI consumers

SUPPORTED COMMANDS
------------------
    thn make project <name> [--var key=value ...]
    thn make module <project> <name> [--var key=value ...]

INVARIANTS
----------
    • Scaffold creation is atomic per command invocation
    • Registry updates MUST reflect on-disk state
    • Scaffold identity is written exactly once and never overwritten
    • Blueprint metadata MUST be present after scaffold creation
    • All failures MUST raise CommandError
    • Post-make hooks are optional but structurally enforced

NON-GOALS
---------
    • Blueprint definition or validation logic
    • Acceptance policy enforcement (policy is advisory here)
    • Interactive prompts or UI flows
    • Repair or regeneration of existing scaffolds

Those concerns belong to:
    • blueprint engine and validators
    • drift accept / recovery commands
    • future GUI orchestration layers

CONTRACT STATUS
---------------
LOCKED CLI OUTPUT SURFACE

The JSON output emitted by:
    • run_make_project()
    • run_make_module()

is externally visible and relied upon by:
    • Automation scripts
    • CI pipelines
    • Golden tests
    • Future GUI tooling

Any change to:
    • keys
    • nesting
    • semantic meaning

MUST be accompanied by updated golden tests or a versioned CLI change.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from thn_cli.blueprints.engine import apply_blueprint_scaffold
from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.post_make import run_post_make
from thn_cli.post_make.context import PostMakeContext
from thn_cli.post_make.rules_loader import load_project_acceptance_policy
from thn_cli.registry import load_registry, save_registry

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _parse_vars(var_list: List[str]) -> Dict[str, str]:
    """
    Parse repeated --var key=value arguments into a dictionary.
    """
    out: Dict[str, str] = {}
    for item in var_list or []:
        if "=" in item:
            key, value = item.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def _out(obj: Dict[str, Any]) -> None:
    """
    Emit structured JSON output.

    CONTRACT
    --------
    Output must remain deterministic and stable.
    """
    print(json.dumps(obj, indent=4))


def _write_scaffold_registry(
    *,
    project_path: str,
    blueprint: Dict[str, Any],
    variables: Dict[str, Any],
) -> None:
    """
    Persist scaffold identity and resolved variables for recovery / regen.

    Canonical location:
        <project_root>/.thn/registry/scaffold.json

    INVARIANTS
    ----------
    • Written exactly once at scaffold creation
    • Never overwritten
    • Local to the project (no global state)
    • Schema-versioned for future evolution
    """
    registry_dir = Path(project_path) / ".thn" / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)

    registry_file = registry_dir / "scaffold.json"
    if registry_file.exists():
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"Scaffold registry already exists: {registry_file}",
        )

    payload = {
        "schema_version": 1,
        "blueprint": {
            "id": blueprint.get("id"),
            "version": blueprint.get("version"),
        },
        "variables": dict(variables),
    }

    registry_file.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Project Creation
# ---------------------------------------------------------------------------


def run_make_project(args: argparse.Namespace) -> int:
    paths = get_thn_paths()
    registry = load_registry(paths)

    project_name = args.name
    vars_in = _parse_vars(args.var)

    vars_in.setdefault("project_name", project_name)
    vars_in.setdefault("owner", "Unknown")
    vars_in.setdefault("created", "")

    project_path = os.path.join(paths["projects"], project_name)

    try:
        blueprint_result = apply_blueprint_scaffold(
            blueprint_name="project_default",
            variables=vars_in,
            destination=project_path,
        )
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"Failed to create project '{project_name}'.",
        ) from exc

    blueprint_meta = blueprint_result.get("blueprint")
    if not blueprint_meta:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Internal error: missing blueprint metadata after scaffold.",
        )

    # ------------------------------------------------------------
    # Persist scaffold registry (blueprint + variables)
    # ------------------------------------------------------------
    _write_scaffold_registry(
        project_path=project_path,
        blueprint=blueprint_meta,
        variables=vars_in,
    )

    projects = registry.get("projects", {})
    projects[project_name] = {
        "path": project_path,
        "blueprint": blueprint_meta,
        "modules": [],
    }

    registry["projects"] = projects
    save_registry(paths, registry)

    # ------------------------------------------------------------
    # Context wiring: optional acceptance policy (advisory)
    # ------------------------------------------------------------
    acceptance_policy = load_project_acceptance_policy(Path(project_path))

    ctx = PostMakeContext(
        command="make project",
        project=project_name,
        target_kind="project",
        target_name=project_name,
        blueprint_id=blueprint_meta["id"],
        thn_paths=paths,
        output_path=project_path,
        registry_record=projects[project_name],
        vars_resolved=vars_in,
        make_result=blueprint_result,
        acceptance_policy=acceptance_policy,
    )

    try:
        run_post_make(ctx)
    except Exception:
        import traceback

        traceback.print_exc()
        raise

    _out(
        {
            "command": "make project",
            "status": "OK",
            "project": project_name,
            "result": blueprint_result,
        }
    )
    return 0


# ---------------------------------------------------------------------------
# Module Creation
# ---------------------------------------------------------------------------


def run_make_module(args: argparse.Namespace) -> int:
    paths = get_thn_paths()
    registry = load_registry(paths)

    project_name = args.project
    module_name = args.name
    vars_in = _parse_vars(args.var)

    projects = registry.get("projects", {})
    if project_name not in projects:
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Project '{project_name}' not found in registry.",
        )

    project_path = projects[project_name]["path"]
    module_path = os.path.join(project_path, "modules", module_name)

    vars_in.setdefault("project_name", project_name)
    vars_in.setdefault("module_name", module_name)
    vars_in.setdefault("created", "")

    try:
        blueprint_result = apply_blueprint_scaffold(
            blueprint_name="module_default",
            variables=vars_in,
            destination=module_path,
        )
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"Failed to create module '{module_name}'.",
        ) from exc

    blueprint_meta = blueprint_result.get("blueprint")
    if not blueprint_meta:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Internal error: missing blueprint metadata after scaffold.",
        )

    module_entry = {
        "name": module_name,
        "path": module_path,
        "blueprint": blueprint_meta,
    }

    projects[project_name]["modules"].append(module_entry)
    save_registry(paths, registry)

    # ------------------------------------------------------------
    # Context wiring: policy comes from project root by default
    # ------------------------------------------------------------
    acceptance_policy = load_project_acceptance_policy(Path(project_path))

    ctx = PostMakeContext(
        command="make module",
        project=project_name,
        target_kind="module",
        target_name=module_name,
        blueprint_id=blueprint_meta["id"],
        thn_paths=paths,
        output_path=module_path,
        registry_record=module_entry,
        vars_resolved=vars_in,
        make_result=blueprint_result,
        acceptance_policy=acceptance_policy,
    )

    try:
        run_post_make(ctx)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"Post-make verification failed for module '{module_name}'.",
        ) from exc

    _out(
        {
            "command": "make module",
            "status": "OK",
            "project": project_name,
            "module": module_name,
            "result": blueprint_result,
        }
    )
    return 0


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the `thn make` command group.
    """
    parser = subparsers.add_parser(
        "make",
        help="Create THN projects or modules.",
    )

    sub = parser.add_subparsers(dest="make_command", required=True)

    p_proj = sub.add_parser("project", help="Create a new project.")
    p_proj.add_argument("name")
    p_proj.add_argument("--var", action="append", default=[])
    p_proj.set_defaults(func=run_make_project)

    p_mod = sub.add_parser("module", help="Create a module under a project.")
    p_mod.add_argument("project")
    p_mod.add_argument("name")
    p_mod.add_argument("--var", action="append", default=[])
    p_mod.set_defaults(func=run_make_module)

    parser.set_defaults(func=lambda a: parser.print_help())
