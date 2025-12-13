"""
THN Make Command Group (Hybrid-Standard)
---------------------------------------

Provides project and module creation using blueprint-driven scaffolding.

Commands:
    thn make project <name> --var key=value ...
    thn make module  <project> <name> --var key=value ...

Hybrid-Standard Guarantees:
    • Deterministic JSON output only
    • No ambiguous human text
    • Stable field names for programmatic use
    • Safe registry merges
    • No implicit assumptions about existing structure
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from thn_cli.blueprints.engine import apply_blueprint
from thn_cli.pathing import get_thn_paths
from thn_cli.registry import load_registry, save_registry

# ---------------------------------------------------------------------------
# Utility: Parse --var key=value
# ---------------------------------------------------------------------------


def _parse_vars(var_list: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not var_list:
        return out

    for item in var_list:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        out[key.strip()] = value.strip()

    return out


# ---------------------------------------------------------------------------
# Output Wrapper
# ---------------------------------------------------------------------------


def _out(obj: Dict[str, Any]) -> None:
    print(json.dumps(obj, indent=4))


# ---------------------------------------------------------------------------
# Project Creation
# ---------------------------------------------------------------------------


def run_make_project(args: argparse.Namespace) -> int:
    """
    Creates a THN project using blueprint "project_default".
    """
    paths = get_thn_paths()
    registry = load_registry(paths)

    project_name = args.name
    vars_in = _parse_vars(args.var)

    # Required minimum variables for project scaffolding
    vars_in.setdefault("project_name", project_name)
    vars_in.setdefault("owner", "Unknown")
    vars_in.setdefault("created", "")

    output_root = paths["projects"]

    try:
        blueprint_result = apply_blueprint(
            blueprint_name="project_default",
            variables=vars_in,
            output_root=output_root,
        )
    except Exception as exc:
        _out(
            {
                "command": "make project",
                "status": "ERROR",
                "project": project_name,
                "error": str(exc),
            }
        )
        return 1

    # Registry update
    projects = registry.get("projects", {})
    existing = projects.get(project_name, {})

    project_path = os.path.join(output_root, project_name)

    record = {
        "owner": vars_in.get("owner", existing.get("owner", "Unknown")),
        "created": vars_in.get("created", existing.get("created", "")),
        "path": existing.get("path", project_path),
        "modules": existing.get("modules", []),
        "meta": existing.get("meta", {}),
    }

    projects[project_name] = record
    registry["projects"] = projects
    save_registry(paths, registry)

    _out(
        {
            "command": "make project",
            "status": "OK",
            "project": project_name,
            "blueprint": blueprint_result,
            "registry_record": record,
        }
    )

    return 0


# ---------------------------------------------------------------------------
# Module Creation
# ---------------------------------------------------------------------------


def run_make_module(args: argparse.Namespace) -> int:
    """
    Creates a module under an existing THN project using blueprint "module_default".
    """
    paths = get_thn_paths()
    registry = load_registry(paths)

    project_name = args.project
    module_name = args.name
    vars_in = _parse_vars(args.var)

    projects = registry.get("projects", {})
    if project_name not in projects:
        _out(
            {
                "command": "make module",
                "status": "ERROR",
                "project": project_name,
                "module": module_name,
                "error": "Project not found in registry.",
            }
        )
        return 1

    record_project = projects[project_name]
    project_path = record_project.get("path", os.path.join(paths["projects"], project_name))

    module_path = os.path.join(project_path, "modules", module_name)

    vars_in.setdefault("project_name", project_name)
    vars_in.setdefault("module_name", module_name)
    vars_in.setdefault("created", "")

    try:
        blueprint_result = apply_blueprint(
            blueprint_name="module_default",
            variables=vars_in,
            output_root=paths["projects"],
        )
    except Exception as exc:
        _out(
            {
                "command": "make module",
                "status": "ERROR",
                "project": project_name,
                "module": module_name,
                "error": str(exc),
            }
        )
        return 1

    # Normalize module list
    modules = record_project.get("modules", [])
    if isinstance(modules, dict):
        modules = list(modules.values())

    # Remove any prior module with the same name
    modules = [m for m in modules if m.get("name") != module_name]

    module_record = {
        "name": module_name,
        "created": vars_in.get("created", ""),
        "path": module_path,
        "tasks": [],
        "config": {},
        "meta": {
            "type": "module",
            "version": 1,
        },
    }

    modules.append(module_record)
    record_project["modules"] = modules
    projects[project_name] = record_project
    registry["projects"] = projects
    save_registry(paths, registry)

    _out(
        {
            "command": "make module",
            "status": "OK",
            "project": project_name,
            "module": module_name,
            "blueprint": blueprint_result,
            "registry_project": record_project,
            "registry_module": module_record,
        }
    )

    return 0


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """
    Register:

        thn make project <name> [--var key=value]
        thn make module  <project> <name> [--var key=value]
    """
    parser = subparsers.add_parser(
        "make",
        help="Create THN projects or modules (Hybrid-Standard).",
        description="Blueprint-driven scaffolding for THN development.",
    )

    sub = parser.add_subparsers(dest="make_command")

    # project
    p_proj = sub.add_parser("project", help="Create a new THN project.")
    p_proj.add_argument("name")
    p_proj.add_argument("--var", action="append", default=[])
    p_proj.set_defaults(func=run_make_project)

    # module
    p_mod = sub.add_parser("module", help="Create a module under an existing project.")
    p_mod.add_argument("project")
    p_mod.add_argument("name")
    p_mod.add_argument("--var", action="append", default=[])
    p_mod.set_defaults(func=run_make_module)

    parser.set_defaults(func=lambda a: parser.print_help())
