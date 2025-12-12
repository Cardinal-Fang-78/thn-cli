"""
Tasks Diagnostic
----------------

Evaluates the THN Tasks subsystem:

    • Task registry health
    • Missing/duplicate task entries
    • Task scheduler behavior
    • Dry-run task execution validation
    • Schema correctness

Produces a Hybrid-Standard DiagnosticResult structure consistent with
the entire diagnostics suite.
"""

from __future__ import annotations

from typing import Any, Dict, List

from thn_cli.tasks.scheduler import list_tasks, run_task

from .diagnostic_result import DiagnosticResult

# ---------------------------------------------------------------------------
# Internal validation helpers
# ---------------------------------------------------------------------------


def _validate_task_entry(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate individual task metadata structure.

    Expected schema:
        {
            "name": str,
            "command": str,
            "schedule": str,
            "enabled": bool
        }
    """
    errors: List[str] = []
    warnings: List[str] = []

    required = {
        "name": str,
        "command": str,
        "schedule": str,
        "enabled": bool,
    }

    for key, expected_type in required.items():
        if key not in task:
            errors.append(f"Missing required field '{key}'.")
            continue

        value = task[key]
        if not isinstance(value, expected_type):
            errors.append(
                f"Field '{key}' expected {expected_type.__name__}, "
                f"got {type(value).__name__}."
            )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _validate_task_list(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate the entire task registry list.

    Checks for:
        • duplicates by name
        • missing fields
        • invalid schema
    """
    errors: List[str] = []
    warnings: List[str] = []
    seen = set()

    for task in tasks:
        name = task.get("name")
        if name in seen:
            errors.append(f"Duplicate task name detected: '{name}'.")
        else:
            seen.add(name)

        entry_result = _validate_task_entry(task)
        if not entry_result["ok"]:
            errors.extend(
                [f"Task '{name or '<unknown>'}': {e}" for e in entry_result["errors"]]
            )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _test_task_execution(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Attempt a DRY-RUN execution of all enabled tasks.

    Returns:
        {
            "ok": bool,
            "results": {task_name: {...}},
            "errors": [...],
        }
    """
    errors: List[str] = []
    results: Dict[str, Any] = {}

    for task in tasks:
        if not task.get("enabled", False):
            continue

        name = task.get("name", "<unknown>")

        try:
            # The scheduler handles no-op if dry-run is unsupported
            out = run_task(name)
            results[name] = out

        except Exception as exc:
            errors.append(f"Task '{name}' execution raised exception: {exc}")

    return {
        "ok": not errors,
        "results": results,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Public Diagnostic
# ---------------------------------------------------------------------------


def diagnose_tasks() -> Dict[str, Any]:
    """
    Hybrid-standard diagnostic for the THN Tasks subsystem.

    Evaluates:
        • registry load
        • schema correctness
        • enabled-task execution testing
        • aggregated errors/warnings
    """
    try:
        tasks = list_tasks()
    except Exception as exc:
        return DiagnosticResult(
            component="tasks",
            ok=False,
            errors=[f"Exception during list_tasks(): {exc}"],
            details={"exception": str(exc)},
        ).as_dict()

    # Validate full registry
    list_check = _validate_task_list(tasks)

    # Test task execution paths
    exec_check = _test_task_execution(tasks)

    errors: List[str] = []
    warnings: List[str] = []

    if not list_check["ok"]:
        errors.extend(list_check["errors"])
    if list_check["warnings"]:
        warnings.extend(list_check["warnings"])

    if not exec_check["ok"]:
        errors.extend(exec_check["errors"])

    ok = not errors

    details = {
        "tasks_raw": tasks,
        "task_list_validation": list_check,
        "execution_test": exec_check,
    }

    return DiagnosticResult(
        component="tasks",
        ok=ok,
        details=details,
        warnings=warnings,
        errors=errors,
    ).as_dict()
