"""
Plugin Management Commands
--------------------------

Commands:

    thn plugins list
    thn plugins enable <name>
    thn plugins disable <name>
    thn plugins load <name>
"""

from __future__ import annotations

import argparse
import json

from thn_cli.plugins.plugin_loader import (
    disable_plugin,
    enable_plugin,
    list_plugins,
    load_plugin,
    load_plugin_registry,
)

# ---------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------


def run_plugins_list(args: argparse.Namespace) -> int:
    plugins = list_plugins()

    print("\nTHN Plugins\n")
    if not plugins:
        print("(none found)\n")
        return 0

    for p in plugins:
        st = "enabled" if p.get("enabled") else "disabled"
        print(f"- {p['name']} [{st}]")

    print()
    return 0


def run_plugins_enable(args: argparse.Namespace) -> int:
    enable_plugin(args.name)
    print(f"\nPlugin '{args.name}' enabled.\n")
    return 0


def run_plugins_disable(args: argparse.Namespace) -> int:
    ok = disable_plugin(args.name)
    if not ok:
        print(f"\nPlugin '{args.name}' not found.\n")
        return 1

    print(f"\nPlugin '{args.name}' disabled.\n")
    return 0


def run_plugins_load(args: argparse.Namespace) -> int:
    try:
        module = load_plugin(args.name)
        print("\nTHN Plugin Load Result\n")
        print(json.dumps({"loaded": True, "module": module.__name__}, indent=4))
        print()
        return 0
    except ImportError:
        print(f"\nError: plugin '{args.name}' not found.\n")
        return 1


# ---------------------------------------------------------
# Subparser Registration
# ---------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "plugins",
        help="Manage THN plugins.",
        description="List, enable, disable, or load plugins.",
    )

    sub = parser.add_subparsers(dest="plugins_cmd", required=True)

    # list
    p_list = sub.add_parser("list")
    p_list.set_defaults(func=run_plugins_list)

    # enable
    p_enable = sub.add_parser("enable")
    p_enable.add_argument("name")
    p_enable.set_defaults(func=run_plugins_enable)

    # disable
    p_disable = sub.add_parser("disable")
    p_disable.add_argument("name")
    p_disable.set_defaults(func=run_plugins_disable)

    # load
    p_load = sub.add_parser("load")
    p_load.add_argument("name")
    p_load.set_defaults(func=run_plugins_load)

    parser.set_defaults(func=lambda a: parser.print_help())
