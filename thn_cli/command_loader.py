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

DIAGNOSTIC GOVERNANCE (NON-ENFORCING)
------------------------------------
When THN_CLI_VERBOSE is enabled, this loader emits advisory diagnostics for
governance and auditing purposes only.

Specifically:
    • Warns if a CLI command is exposed but missing a boundary registry entry
    • These warnings are diagnostic-only and never affect execution
    • Registry completeness is enforced elsewhere via tests

CONTRACT STATUS
---------------
⚠️ NON-FATAL INFRASTRUCTURE — DIAGNOSTIC SAFE

This module:
    • MUST NOT raise exceptions during command discovery
    • MUST NOT terminate CLI startup
    • MUST NOT write to stdout
    • MUST remain deterministic across runs

Failures and diagnostics are emitted only when explicitly requested.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
import sys
from typing import TYPE_CHECKING, List, Optional, Set

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


def _invoke_add_subparser(
    module: object,
    subparsers: "argparse._SubParsersAction",
    *,
    exposed_commands: Set[str],
) -> None:
    """
    Invoke add_subparser(subparsers) if present on the module.

    Failures are isolated and logged. Successfully registered top-level
    command names are recorded for diagnostic auditing.
    """
    add = getattr(module, "add_subparser", None)
    if not callable(add):
        return

    before = set(subparsers.choices.keys())
    try:
        add(subparsers)
        after = set(subparsers.choices.keys())
        newly_added = after - before
        exposed_commands.update(newly_added)
        _log(f"Registered commands from {module.__name__}")
    except Exception as exc:
        _log(f"FAILED while registering {module.__name__}: {exc}")


# ---------------------------------------------------------------------------
# Diagnostic governance checks (non-enforcing)
# ---------------------------------------------------------------------------


def _diagnose_missing_boundary_entries(
    *,
    exposed_commands: Set[str],
) -> None:
    """
    Emit diagnostic warnings for commands that are exposed via argparse
    but have no boundary registry entry.

    This is advisory-only and does not affect execution or exit codes.
    """
    if not _verbose():
        return

    try:
        from thn_cli.contracts.cli_boundaries import BOUNDARY_BY_TOP_LEVEL, resolve_boundary
    except Exception as exc:
        _log(f"WARNING: unable to load boundary registry for diagnostics: {exc}")
        return

    for cmd in sorted(exposed_commands):
        try:
            # Perform a dry resolution using a minimal namespace.
            class _Args:
                command = cmd

            resolve_boundary(_Args())
        except Exception:
            _log(f"WARNING: command '{cmd}' is exposed but has no boundary registry entry")
            _log("  → add a top-level fallback or path entry in cli_boundaries.py")
            _log("  → this is diagnostic-only and does not affect execution")


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

    exposed_commands: Set[str] = set()

    for module_name in _iter_command_modules():
        full = f"{thn_cli.commands.__name__}.{module_name}"
        _log(f"Importing {full}")

        module = _safe_import(full)
        if module is None:
            continue

        _invoke_add_subparser(
            module,
            subparsers,
            exposed_commands=exposed_commands,
        )

    _diagnose_missing_boundary_entries(
        exposed_commands=exposed_commands,
    )

    _log("Command module loading complete")
