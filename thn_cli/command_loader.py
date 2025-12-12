"""
THN CLI Dynamic Command Loader (Hybrid-Standard)

Responsibilities:
    • Discover all command modules under thn_cli.commands
    • Import safely with isolation of module-level failures
    • Invoke add_subparser(subparsers) when present
    • Guarantee deterministic load order
    • Provide optional diagnostics via THN_CLI_VERBOSE

Hybrid-Standard Enhancements:
    • Skips private modules (_foo.py)
    • Deterministic alphabetical load order
    • Graceful error recovery with structured reporting
    • Does not terminate the CLI if a single command module fails
    • Supports future command groups + plugin discovery
"""

from __future__ import annotations

import importlib
import os
import pkgutil
from typing import TYPE_CHECKING, Any, Callable, Dict, List

import thn_cli.commands

if TYPE_CHECKING:
    import argparse


# ---------------------------------------------------------------------------
# Internal diagnostic hook
# ---------------------------------------------------------------------------

_VERBOSE = bool(os.environ.get("THN_CLI_VERBOSE", "").strip())


def _log(msg: str) -> None:
    if _verbose():
        print(f"[command-loader] {msg}")


def _verbose() -> bool:
    return _VERBOSE


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _iter_command_modules() -> List[str]:
    """
    Enumerate all modules under thn_cli.commands in deterministic order,
    skipping private modules (those starting with '_').
    """
    package = thn_cli.commands
    names = []

    for _loader, module_name, _is_pkg in pkgutil.iter_modules(package.__path__):
        if module_name.startswith("_"):
            continue
        names.append(module_name)

    return sorted(names)


def _safe_import(full_name: str):
    """
    Import a command module safely.
    Returns either the module or None if an error occurs.
    """
    try:
        return importlib.import_module(full_name)
    except Exception as exc:
        _log(f"FAILED to import {full_name}: {exc}")
        return None


def _invoke_add_subparser(module, subparsers):
    """
    If module has add_subparser(), call it.
    """
    if hasattr(module, "add_subparser"):
        try:
            module.add_subparser(subparsers)
            _log(f"Registered commands from {module.__name__}")
        except Exception as exc:
            _log(f"FAILED while calling add_subparser for {module.__name__}: {exc}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_commands(subparsers: "argparse._SubParsersAction") -> None:
    """
    Discover, import, and register all command modules under thn_cli.commands.

    This function must NEVER throw an exception. All failures are logged
    (when THN_CLI_VERBOSE is enabled) and recovery continues gracefully.

    Hybrid-Standard guarantees:
        • Deterministic stable load order
        • No module can prevent others from loading
        • Optional verbose diagnostics
    """

    _log("Starting command module discovery")

    for module_name in _iter_command_modules():
        full = f"{thn_cli.commands.__name__}.{module_name}"
        _log(f"Importing {full}")

        module = _safe_import(full)
        if not module:
            continue

        _invoke_add_subparser(module, subparsers)

    _log("Command module loading complete")
