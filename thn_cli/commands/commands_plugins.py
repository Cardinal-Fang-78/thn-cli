# thn_cli/commands/commands_plugins.py

"""
THN Plugin Command Group
------------------------

Provides:

    thn plugins list
    thn plugins show <name>
    thn plugins reload
"""

from __future__ import annotations

import argparse
import json

from thn_cli.plugins.plugin_loader import (
    list_plugins,
    load_plugin,
    load_registry,
    save_registry,
)


# ---------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------

def run_plugins_list(args: argparse.Namespace) -> int:
    plugins = list_plugins()

    print("\nTHN Plugins\n")
    if not plugins:
        print("(none)\n")
        return 0

    for p in plugins:
        print(f"- {p}")
    print()
    return 0


def run_plugins_show(args: argparse.Namespace) -> int:
    name = args.name
    plugin = load_plugin(name)

    print("\nTHN Plugin Details\n")
    if plugin is None:
        print(f"Plugin '{name}' not found.\n")
        return 1

    print(json.dumps(plugin, indent=4))
    print()
    return 0


def run_plugins_reload(args: argparse.Namespace) -> int:
    registry = load_registry()
    save_registry(registry)

    print("\nTHN Plugins Reloaded\n")
    print(json.dumps(registry, indent=4))
    print()
    return 0


# ---------------------------------------------------------------------
# Subparser Registration
# ---------------------------------------------------------------------

def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "plugins",
        help="Inspect and manage THN plugins.",
        description="List, inspect, and reload the THN plugin registry.",
    )

    sub = parser.add_subparsers(dest="plugins_cmd", required=True)

    # list
    p_list = sub.add_parser("list", help="List plugins.")
    p_list.set_defaults(func=run_plugins_list)

    # show
    p_show = sub.add_parser("show", help="Show plugin details.")
    p_show.add_argument("name")
    p_show.set_defaults(func=run_plugins_show)

    # reload registry
    p_reload = sub.add_parser("reload", help="Reload plugin registry.")
    p_reload.set_defaults(func=run_plugins_reload)

    parser.set_defaults(func=lambda args: parser.print_help())
