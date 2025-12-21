# thn_cli/commands/commands_blueprint.py
"""
THN Blueprint Commands (Hybrid-Standard)
========================================

RESPONSIBILITIES
----------------
Defines the authoritative CLI surface for THN blueprint operations.

This module provides:
    • `thn blueprint apply`
    • `thn blueprint list`
    • `thn blueprint validate`

It is responsible for:
    • CLI argument parsing and validation
    • Delegation to blueprint engine / manager / validator layers
    • Emitting deterministic, structured JSON output
    • Enforcing CommandError-only failure paths

INVARIANTS
----------
    • CLI output MUST remain JSON-stable
    • All user errors MUST raise CommandError(USER_CONTRACT)
    • All internal failures MUST raise CommandError(SYSTEM_CONTRACT)
    • No inline exception rendering
    • No direct filesystem manipulation
    • No blueprint logic embedded in CLI layer

NON-GOALS
---------
    • Blueprint execution logic
    • Blueprint storage or discovery
    • Blueprint schema validation rules
    • Filesystem mutation beyond delegated blueprint application

CONTRACT STATUS
---------------
LOCKED CLI SURFACE

The JSON payloads emitted by:
    • run_blueprint_apply
    • run_blueprint_list
    • run_blueprint_validate

are considered externally visible contracts and are relied upon by:
    • CLI users
    • Automation and scripting
    • CI pipelines
    • Future GUI tooling

Any changes to:
    • keys
    • nesting
    • semantics

MUST be accompanied by updated golden tests or a versioned CLI surface change.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from thn_cli.blueprints.engine import apply_blueprint
from thn_cli.blueprints.manager import list_blueprints
from thn_cli.blueprints.validator import validate_all_blueprints, validate_blueprint
from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _parse_vars(var_args: List[str]) -> Dict[str, Any]:
    """
    Parse repeated:
        --var key=value

    into a dictionary.

    CONTRACT
    --------
    • Malformed entries are ignored safely
    • Later values overwrite earlier ones
    """
    result: Dict[str, Any] = {}
    if not var_args:
        return result

    for item in var_args:
        if "=" not in item:
            continue
        key, val = item.split("=", 1)
        key = key.strip()
        val = val.strip()
        if key:
            result[key] = val

    return result


def _out(payload: Dict[str, Any]) -> None:
    """
    Emit structured JSON output.

    CONTRACT
    --------
    • Deterministic
    • UTF-8 safe
    • Stable for golden tests and automation
    """
    print(json.dumps(payload, indent=4))


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_blueprint_apply(args) -> int:
    """
    Apply a named blueprint with optional variables.
    """
    if not args.name:
        raise CommandError(
            contract=USER_CONTRACT,
            message="--name is required for 'blueprint apply'.",
        )

    vars_in = _parse_vars(args.var)

    try:
        result = apply_blueprint(args.name, vars_in)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"Blueprint '{args.name}' failed to apply.",
        ) from exc

    _out(
        {
            "command": "blueprint apply",
            "status": "OK",
            "blueprint": args.name,
            "vars": vars_in,
            "result": result,
        }
    )
    return 0


def run_blueprint_list(args) -> int:
    """
    List all available blueprints.
    """
    try:
        names = list_blueprints()
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to list blueprints.",
        ) from exc

    _out(
        {
            "command": "blueprint list",
            "status": "OK",
            "count": len(names),
            "blueprints": names,
        }
    )
    return 0


def run_blueprint_validate(args) -> int:
    """
    Validate one or all blueprints.
    """
    if args.all:
        try:
            result = validate_all_blueprints()
        except Exception as exc:
            raise CommandError(
                contract=SYSTEM_CONTRACT,
                message="Failed to validate all blueprints.",
            ) from exc

        _out(
            {
                "command": "blueprint validate",
                "status": "OK",
                "mode": "all",
                "result": result,
            }
        )
        return 0

    if not args.name:
        raise CommandError(
            contract=USER_CONTRACT,
            message="Either --name or --all must be provided.",
        )

    try:
        result = validate_blueprint(args.name)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message=f"Blueprint '{args.name}' failed validation.",
        ) from exc

    _out(
        {
            "command": "blueprint validate",
            "status": "OK",
            "mode": "single",
            "blueprint": args.name,
            "result": result,
        }
    )
    return 0


# ---------------------------------------------------------------------------
# Command Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers) -> None:
    """
    Register the `thn blueprint` command group.
    """
    parser = subparsers.add_parser(
        "blueprint",
        help="Blueprint utilities for THN.",
        description="Apply, list, and validate THN blueprints.",
    )

    sub = parser.add_subparsers(dest="blueprint_command", required=True)

    p_apply = sub.add_parser("apply", help="Apply a blueprint.")
    p_apply.add_argument("--name", required=True)
    p_apply.add_argument("--var", action="append", default=[])
    p_apply.set_defaults(func=run_blueprint_apply)

    p_list = sub.add_parser("list", help="List available blueprints.")
    p_list.set_defaults(func=run_blueprint_list)

    p_validate = sub.add_parser("validate", help="Validate blueprints.")
    p_validate.add_argument("--name")
    p_validate.add_argument("--all", action="store_true")
    p_validate.set_defaults(func=run_blueprint_validate)

    parser.set_defaults(func=lambda args: parser.print_help())
