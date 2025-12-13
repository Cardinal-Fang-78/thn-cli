# thn_cli/commands_blueprints.py

"""
THN Blueprint Command Group (Hybrid-Standard)
=============================================

Implements:

    thn blueprint apply    --name NAME --var key=value ... [--json]
    thn blueprint list     [--json]
    thn blueprint validate --name NAME [--json]
    thn blueprint validate --all       [--json]

This Hybrid-Standard rewrite provides:

    • Structured JSON mode for automation
    • Unified error model
    • Consistent return schemas
    • Safe variable parsing
    • Predictable CLI UX identical to other THN Modern commands
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from thn_cli.blueprints.engine import apply_blueprint
from thn_cli.blueprints.manager import list_blueprints
from thn_cli.blueprints.validator import validate_all_blueprints, validate_blueprint

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _emit_json(obj: Any) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _ok(json_mode: bool, **payload) -> int:
    if json_mode:
        _emit_json({"status": "OK", **payload})
        return 0

    # Text mode
    print(json.dumps({"status": "OK", **payload}, indent=4))
    print()
    return 0


def _err(msg: str, json_mode: bool, **kw) -> int:
    if json_mode:
        _emit_json({"status": "ERROR", "message": msg, **kw})
        return 1

    print(f"\nError: {msg}\n")
    if kw:
        print(json.dumps(kw, indent=4))
        print()
    return 1


def _parse_vars(var_args: List[str]) -> Dict[str, Any]:
    """
    Parse repeated:
        --var key=value
    into dict. Malformed entries are ignored.
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


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_blueprint_apply(args) -> int:
    json_mode = bool(args.json)

    if not args.name:
        return _err("--name is required for 'blueprint apply'.", json_mode)

    var_dict = _parse_vars(args.var)

    try:
        result = apply_blueprint(args.name, var_dict)
    except Exception as exc:
        return _err(
            "Blueprint apply failed.",
            json_mode,
            blueprint=args.name,
            error=str(exc),
            vars=var_dict,
        )

    return _ok(
        json_mode,
        message="blueprint applied",
        blueprint=args.name,
        vars=var_dict,
        result=result,
    )


def run_blueprint_list(args) -> int:
    json_mode = bool(args.json)

    try:
        names = list_blueprints()
    except Exception as exc:
        return _err("Failed to list blueprints.", json_mode, error=str(exc))

    return _ok(
        json_mode,
        message="blueprint list",
        count=len(names),
        blueprints=names,
    )


def run_blueprint_validate(args) -> int:
    json_mode = bool(args.json)

    # Validate all
    if args.all:
        try:
            result = validate_all_blueprints()
        except Exception as exc:
            return _err("Failed to validate all blueprints.", json_mode, error=str(exc))

        return _ok(
            json_mode,
            message="validated all blueprints",
            result=result,
        )

    # Validate single
    if not args.name:
        return _err("Either --name or --all must be provided.", json_mode)

    try:
        result = validate_blueprint(args.name)
    except Exception as exc:
        return _err(
            "Blueprint validation failed.",
            json_mode,
            blueprint=args.name,
            error=str(exc),
        )

    return _ok(
        json_mode,
        message="validated blueprint",
        blueprint=args.name,
        result=result,
    )


# ---------------------------------------------------------------------------
# Command Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser(
        "blueprint",
        help="Blueprint utilities for THN.",
        description="Apply, list, and validate THN blueprints.",
    )

    sub = parser.add_subparsers(dest="blueprint_command")

    # ----------------------------------------------------------------------
    # thn blueprint apply
    # ----------------------------------------------------------------------
    p_apply = sub.add_parser(
        "apply",
        help="Apply a blueprint to generate files.",
        description="Applies a blueprint using provided template variables.",
    )
    p_apply.add_argument("--name", required=True, help="Blueprint name.")
    p_apply.add_argument("--var", action="append", default=[], help="Template variable key=value.")
    p_apply.add_argument("--json", action="store_true", help="Output in JSON format.")
    p_apply.set_defaults(func=run_blueprint_apply)

    # ----------------------------------------------------------------------
    # thn blueprint list
    # ----------------------------------------------------------------------
    p_list = sub.add_parser(
        "list",
        help="List available blueprints.",
    )
    p_list.add_argument("--json", action="store_true", help="Output in JSON format.")
    p_list.set_defaults(func=run_blueprint_list)

    # ----------------------------------------------------------------------
    # thn blueprint validate
    # ----------------------------------------------------------------------
    p_validate = sub.add_parser(
        "validate",
        help="Validate blueprint definitions and templates.",
    )
    p_validate.add_argument("--name", help="Validate a single blueprint.")
    p_validate.add_argument("--all", action="store_true", help="Validate all blueprints.")
    p_validate.add_argument("--json", action="store_true", help="Output in JSON format.")
    p_validate.set_defaults(func=run_blueprint_validate)

    # Default action → help
    parser.set_defaults(func=lambda args: parser.print_help())
