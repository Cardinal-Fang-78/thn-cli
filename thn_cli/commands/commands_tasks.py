# thn_cli/commands_tasks.py

"""
THN Tasks Command Group (Hybrid-Standard)
=========================================

Commands:

    thn tasks list
    thn tasks add <name> <cmd> <schedule> [--json]
    thn tasks remove <name> [--json]
    thn tasks run <name> [--json]

This is the lightweight task scheduler interface used by THN's
automation subsystem. The scheduler is intentionally simple:
no background daemon, all tasks run explicitly through CLI calls.

Hybrid-Standard guarantees:
    • JSON-safe automation mode
    • Predictable error model
    • Never throws uncaught exceptions
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from thn_cli.tasks.scheduler import add_task, list_tasks, remove_task, run_task

# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------


def _emit_json(obj: Dict[str, Any]) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _ok(json_mode: bool, **payload) -> int:
    out = {"status": "OK"}
    out.update(payload)
    if json_mode:
        _emit_json(out)
    else:
        print(json.dumps(out, indent=4))
        print()
    return 0


def _err(msg: str, json_mode: bool, **extra) -> int:
    out = {"status": "ERROR", "message": msg}
    out.update(extra)
    if json_mode:
        _emit_json(out)
    else:
        print(f"\nError: {msg}")
        if extra:
            print(json.dumps(extra, indent=4))
        print()
    return 1


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------


def run_tasks_list(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)

    try:
        tasks = list_tasks()
    except Exception as exc:
        return _err("Failed to list tasks.", json_mode, error=str(exc))

    if json_mode:
        return _ok(json_mode, tasks=tasks)

    print("\nTHN Tasks\n")
    if not tasks:
        print("(none)\n")
        return 0

    for t in tasks:
        status = "enabled" if t.get("enabled") else "disabled"
        print(f"- {t['name']} [{status}]")
        print(f"    Command : {t['command']}")
        print(f"    Schedule: {t['schedule']}\n")

    return 0


def run_tasks_add(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)

    try:
        ok = add_task(args.name, args.command, args.schedule)
    except Exception as exc:
        return _err("Internal scheduler error.", json_mode, error=str(exc))

    if not ok:
        return _err(
            f"Task '{args.name}' already exists.",
            json_mode,
            name=args.name,
        )

    return _ok(
        json_mode,
        message="task added",
        name=args.name,
        command=args.command,
        schedule=args.schedule,
    )


def run_tasks_remove(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)

    try:
        ok = remove_task(args.name)
    except Exception as exc:
        return _err("Internal scheduler error.", json_mode, error=str(exc))

    if not ok:
        return _err(
            f"Task '{args.name}' not found.",
            json_mode,
            name=args.name,
        )

    return _ok(json_mode, message="task removed", name=args.name)


def run_tasks_run(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)

    try:
        result = run_task(args.name)
    except Exception as exc:
        return _err("Task execution failed.", json_mode, error=str(exc))

    return _ok(json_mode, message="task executed", name=args.name, result=result)


# ---------------------------------------------------------------------------
# Subparser Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "tasks",
        help="Manage scheduled THN tasks.",
        description="List, add, remove, and run tasks.",
    )

    sub = parser.add_subparsers(
        dest="tasks_cmd",
        required=True,
    )

    # list --------------------------------------------------------
    p_list = sub.add_parser("list", help="List all tasks.")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=run_tasks_list)

    # add ---------------------------------------------------------
    p_add = sub.add_parser("add", help="Add a new task.")
    p_add.add_argument("name")
    p_add.add_argument("command")
    p_add.add_argument("schedule")
    p_add.add_argument("--json", action="store_true")
    p_add.set_defaults(func=run_tasks_add)

    # remove ------------------------------------------------------
    p_remove = sub.add_parser("remove", help="Remove a task.")
    p_remove.add_argument("name")
    p_remove.add_argument("--json", action="store_true")
    p_remove.set_defaults(func=run_tasks_remove)

    # run ---------------------------------------------------------
    p_run = sub.add_parser("run", help="Run a task immediately.")
    p_run.add_argument("name")
    p_run.add_argument("--json", action="store_true")
    p_run.set_defaults(func=run_tasks_run)

    # default -----------------------------------------------------
    parser.set_defaults(func=lambda args: parser.print_help())
