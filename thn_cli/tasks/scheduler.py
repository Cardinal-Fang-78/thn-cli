# thn_cli/tasks/scheduler.py
"""
THN Task Scheduler (Hybrid-Standard)
===================================

Purpose
-------
A placeholder scheduling subsystem used by the THN CLI.  
The long-term design supports:

    • Cron-like recurring schedules
    • Conditional tasks
    • Local automation flows (CLI commands, sync operations, diagnostics)
    • Hub-integrated scheduling (optional; tenant-aware)

Current Scope (Stub)
--------------------
This module provides:
    • A persistent task registry (task_registry.json)
    • Add / remove / list operations
    • A deterministic simulated executor for testing and UI display
    • Safe, predictable behaviors with no background threads

No tasks run automatically in this version — all execution
must be triggered manually via `run_task()`.
"""

from __future__ import annotations

import json
import os
import time
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _tasks_root() -> str:
    """
    Return the absolute folder containing task_registry.json.

    This location is stable and relative to the installed THN CLI package.
    """
    return os.path.dirname(os.path.abspath(__file__))


def _registry_path() -> str:
    """Full path to task_registry.json (persistent store)."""
    return os.path.join(_tasks_root(), "task_registry.json")


# ---------------------------------------------------------------------------
# Registry Helpers
# ---------------------------------------------------------------------------

def load_registry() -> Dict[str, Any]:
    """
    Load the task registry from disk.

    Returns:
        {
            "tasks": {
                "<task_name>": {
                    "command": "<string>",
                    "schedule": "<string>",
                    "enabled": <bool>,
                },
                ...
            }
        }

    Failure Conditions:
        • Missing file → returns empty registry
        • Corrupt JSON → returns empty registry
    """
    path = _registry_path()
    if not os.path.isfile(path):
        return {"tasks": {}}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"tasks": {}}
            return data
    except Exception:
        return {"tasks": {}}


def save_registry(registry: Dict[str, Any]) -> None:
    """
    Persist the registry to disk.

    This function never raises — corrupt writes simply do nothing.
    """
    path = _registry_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=4)
    except Exception:
        # Intentionally suppressed to avoid blocking CLI features.
        pass


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------

def list_tasks() -> List[Dict[str, Any]]:
    """
    Return a normalized list of all registered tasks.

    Each item contains:
        name, command, schedule, enabled
    """
    registry = load_registry()
    tasks = registry.get("tasks", {})
    out: List[Dict[str, Any]] = []

    for name, meta in tasks.items():
        out.append(
            {
                "name": name,
                "command": meta.get("command", ""),
                "schedule": meta.get("schedule", ""),
                "enabled": bool(meta.get("enabled", False)),
            }
        )

    return out


def add_task(name: str, command: str, schedule: str) -> bool:
    """
    Add a task to the registry.

    Returns:
        True  → added successfully
        False → name already existed

    Placeholder: schedule string is kept as-is without parsing.
    """
    registry = load_registry()
    tasks = registry.setdefault("tasks", {})

    if name in tasks:
        return False

    tasks[name] = {
        "command": command,
        "schedule": schedule,
        "enabled": False,   # tasks are disabled by default
    }

    save_registry(registry)
    return True


def remove_task(name: str) -> bool:
    """
    Remove a task from the registry.

    Returns:
        True  → removed
        False → does not exist
    """
    registry = load_registry()
    tasks = registry.get("tasks", {})

    if name not in tasks:
        return False

    del tasks[name]
    save_registry(registry)
    return True


# ---------------------------------------------------------------------------
# Execution Stub
# ---------------------------------------------------------------------------

def run_task(name: str) -> Dict[str, Any]:
    """
    Simulate running a task.

    Future (not implemented in stub):
        • spawn THN CLI subprocess with arguments
        • capture stdout/stderr
        • enforce schedule enablement checks

    Returns a normalized result:
        {
            "name": <task>,
            "success": bool,
            "message": <string>,
            "command": <string>,
            "schedule": <string>,
            "enabled": <bool>,
        }
    """
    registry = load_registry()
    tasks = registry.get("tasks", {})

    task = tasks.get(name)
    if not task:
        return {
            "name": name,
            "success": False,
            "message": "Task not found.",
        }

    # Simulated runtime delay
    time.sleep(0.25)

    return {
        "name": name,
        "success": True,
        "message": f"Simulated execution of command: {task.get('command')}",
        "command": task.get("command"),
        "schedule": task.get("schedule"),
        "enabled": bool(task.get("enabled", False)),
    }
