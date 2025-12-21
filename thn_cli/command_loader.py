# thn_cli/command_loader.py
"""
THN CLI Dynamic Command Loader (Hybrid-Standard)
===============================================

RESPONSIBILITIES
----------------
Provides dynamic discovery and registration of CLI command modules.

This module is responsible for:
    • Discovering all public command modules under thn_cli.commands
    • Importing modules safely with isolation of failures
    • Invoking add_subparser(subparsers) when present
    • Guaranteeing deterministic command load order
    • Emitting optional diagnostics when THN_CLI_VERBOSE is enabled

HYBRID-STANDARD ENHANCEMENTS
----------------------------
    • Skips private modules (those starting with '_')
    • Deterministic alphabetical load order
    • Graceful error recovery per module
    • No single command module may prevent others from loading
    • Diagnostic output is opt-in and stderr-only
    • Supports future plugin and extension discovery

CONTRACT STATUS
---------------
⚠️ NON-FATAL INFRASTRUCTURE — DIAGNOSTIC SAFE

This module:
    • MUST NOT raise exceptions during command discovery
    • MUST NOT terminate CLI startup
    • MUST NOT write to stdout
    • MUST remain deterministic across runs

Failures are logged only when explicitly requested.

NOTE
----
This loader operates in accordance with the THN Command Discovery Tenet.
Command exposure authority remains with thn_cli.commands.__all__.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
import sys
from typing import TYPE_CHECKING, List, Optional

import thn_cli.commands

if TYPE_CHECKING:
    import argparse


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def _verbose() -> bool:
    """
    Determine whether verbose command-loader diagnostics are enabled.
    """
    return bool(os.environ.get("THN_CLI_VERBOSE", "").strip())


def _log(msg: str) -> None:
    """
    Emit diagnostic output when verbosity is enabled.

    All output is written to stderr to avoid contaminating CLI output.
    """
    if _verbose():
        sys.stderr.write(f"[command-loader] {msg}\n")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _iter_command_modules() -> List[str]:
    """
    Enumerate all public command modules under thn_cli.commands.

    Behavior:
        • Skips private modules (leading underscore)
        • Deterministic alphabetical order
    """
    package = thn_cli.commands
    names: List[str] = []

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        if module_name.startswith("_"):
            continue
        names.append(module_name)

    return sorted(names)


def _safe_import(full_name: str) -> Optional[object]:
    """
    Import a command module safely.

    Returns:
        • Module object on success
        • None on failure (failure is logged if verbose)
    """
    try:
        return importlib.import_module(full_name)
    except Exception as exc:
        _log(f"FAILED to import {full_name}: {exc}")
        return None


def _invoke_add_subparser(module: object, subparsers: "argparse._SubParsersAction") -> None:
    """
    Invoke add_subparser(subparsers) if present on the module.

    Failures are isolated and logged.
    """
    add = getattr(module, "add_subparser", None)
    if not callable(add):
        return

    try:
        add(subparsers)
        _log(f"Registered commands from {module.__name__}")
    except Exception as exc:
        _log(f"FAILED while registering {module.__name__}: {exc}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_commands(subparsers: "argparse._SubParsersAction") -> None:
    """
    Discover, import, and register all CLI command modules.

    GUARANTEES
    ----------
    • Deterministic load order
    • No fatal failures
    • Per-module isolation
    • Optional diagnostics only
    """
    _log("Starting command module discovery")

    for module_name in _iter_command_modules():
        full = f"{thn_cli.commands.__name__}.{module_name}"
        _log(f"Importing {full}")

        module = _safe_import(full)
        if module is None:
            continue

        _invoke_add_subparser(module, subparsers)

    _log("Command module loading complete")
