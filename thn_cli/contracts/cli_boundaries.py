# thn_cli/contracts/cli_boundaries.py
"""
THN CLI Command Boundary Registry (Hybrid-Standard)
==================================================

RESPONSIBILITIES
----------------
Defines the *single authoritative* registry for CLI boundary classification.

This module is responsible for:
    • Declaring the boundary class for each CLI command (and mode, when applicable)
    • Providing deterministic boundary resolution for parsed argparse invocations
    • Providing validation helpers for loader, tests, and future tooling

BOUNDARY CLASSES
----------------
Authoritative
    Commands that mutate authoritative state and/or whose output represents an
    authoritative outcome.

Diagnostic
    Read-only, safety-critical commands whose output is contract-stable but
    non-authoritative.

Presentation
    Read-only convenience commands with no semantic guarantees; output may evolve
    without versioning.

IMPORTANT
---------
This registry is implemented in Python for type safety and refactor resilience.
It is structured so a JSON export can be added later *only if exercised by real
consumers* (GUI/CI/tooling). This module intentionally avoids committing to a
JSON schema before it is needed.

CONTRACT STATUS
---------------
Authoritative (Policy Registry)

This module:
    • MUST remain deterministic across runs and platforms
    • MUST NOT write to stdout/stderr
    • MUST NOT perform dynamic discovery of commands
    • MUST treat the CLI surface (commands.__all__) as the source of truth,
      with registry coverage enforced by tests and (optionally) loader policy

NON-GOALS
---------
• Runtime mutation interception (engine-level guards)
• Output rewriting or stdout/stderr capture
• Automatic inference of boundaries from filenames or imports

LOCKED BASELINE (MANDATORY)
---------------------------
All top-level CLI commands exposed by argparse MUST have a deterministic
boundary classification via:
  1) Exact path match in BOUNDARY_BY_PATH (including resolvers), OR
  2) Top-level fallback in BOUNDARY_BY_TOP_LEVEL.

No top-level command may remain unclassified. Missing entries are treated as
hard errors by tests to prevent silent authority drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence, Tuple

# ---------------------------------------------------------------------------
# Boundary Types
# ---------------------------------------------------------------------------


class BoundaryClass(str, Enum):
    AUTHORITATIVE = "authoritative"
    DIAGNOSTIC = "diagnostic"
    PRESENTATION = "presentation"


CommandPath = Tuple[str, ...]
BoundaryResolver = Callable[[Any], BoundaryClass]


@dataclass(frozen=True)
class BoundaryResolution:
    boundary: BoundaryClass
    path: CommandPath
    note: str


# ---------------------------------------------------------------------------
# Path Resolution Helpers
# ---------------------------------------------------------------------------


def _path_from_args(args: Any) -> CommandPath:
    """
    Extract the command path from an argparse.Namespace produced by THN CLI.

    This implementation is intentionally conservative and only relies on the
    stable conventions present in thn_cli/cli.py:

        • args.command is the top-level command group
        • nested subparsers use dest names like "<group>_command"
          (e.g., "sync_command" for "thn sync ...")

    If additional nesting exists in the future, it can be extended here
    deliberately without breaking existing resolution.
    """
    top = getattr(args, "command", None)
    if not top:
        return tuple()

    path: List[str] = [str(top)]

    # One level of nesting (current structure).
    nested_dest = f"{top}_command"
    nested_val = getattr(args, nested_dest, None)
    if nested_val:
        path.append(str(nested_val))

    return tuple(path)


# ---------------------------------------------------------------------------
# Path resolvers (for intentionally dual-mode commands)
# ---------------------------------------------------------------------------


def _resolve_sync_web(args: Any) -> BoundaryClass:
    """
    thn sync web defaults to DRY RUN unless --apply is explicitly provided.

    Boundary semantics describe the *authority of the operation*, not whether
    the invocation mutates state in this specific run.
    """
    if bool(getattr(args, "apply", False)):
        return BoundaryClass.AUTHORITATIVE
    return BoundaryClass.DIAGNOSTIC


# ---------------------------------------------------------------------------
# Explicit Path-Level Declarations (Overrides - Highest Precedence)
# ---------------------------------------------------------------------------
#
# Use this for:
# - Known leaf commands with a stricter classification than their parent group
# - Dual-mode leaves that require resolvers
# - Top-level legacy aliases that are dual-mode
# ---------------------------------------------------------------------------


BOUNDARY_BY_PATH: Mapping[CommandPath, BoundaryClass | BoundaryResolver] = {
    # Sync leaf commands
    ("sync", "inspect"): BoundaryClass.DIAGNOSTIC,
    ("sync", "history"): BoundaryClass.DIAGNOSTIC,
    ("sync", "status"): BoundaryClass.DIAGNOSTIC,
    ("sync", "make-test"): BoundaryClass.DIAGNOSTIC,
    ("sync", "apply"): BoundaryClass.AUTHORITATIVE,  # authoritative entrypoint even under --dry-run
    ("sync", "web"): _resolve_sync_web,  # Dual-mode (Sync)
    # Top-level legacy alias
    ("web",): _resolve_sync_web,  # Dual-mode (top-level convenience)
}


# ---------------------------------------------------------------------------
# Top-Level Fallback Declarations (MANDATORY BASELINE)
# ---------------------------------------------------------------------------
#
# Every top-level command registered in thn_cli.commands.__all__
# MUST appear here unless it is fully classified by an exact-path entry in BOUNDARY_BY_PATH.
# No silent defaults are permitted.
#
# Policy note:
#   Fallbacks are intentionally conservative. Leaf/path entries override.
#   Leaf-level declarations may override these defaults via BOUNDARY_BY_PATH.
#
# ---------------------------------------------------------------------------
# Top-Level Boundary Classification Rationale
# ---------------------------------------------------------------------------
#
# Top-level boundaries define the MOST CONSERVATIVE classification for a
# command family when no leaf command is known.
#
# Rules:
#   • If ANY subcommand can mutate authoritative state, the top-level
#     classification MUST be AUTHORITATIVE.
#   • Read-only command families that influence safety decisions are
#     classified as DIAGNOSTIC.
#   • Purely informational or UX-oriented commands are PRESENTATION.
#
# Leaf commands may override these defaults via BOUNDARY_BY_PATH.
#
# This registry is intentionally explicit and complete:
#   • No silent defaults
#   • No inference from filenames or imports
#   • All top-level CLI commands MUST appear here
#
# Tests enforce registry completeness and determinism.
# ---------------------------------------------------------------------------

BOUNDARY_BY_TOP_LEVEL: Mapping[str, BoundaryClass] = {
    # ------------------------------------------------------------------
    # Authoritative (state mutation)
    # ------------------------------------------------------------------
    "accept": BoundaryClass.AUTHORITATIVE,
    "make": BoundaryClass.AUTHORITATIVE,
    "make-project": BoundaryClass.AUTHORITATIVE,
    "migrate": BoundaryClass.AUTHORITATIVE,
    "snapshots": BoundaryClass.AUTHORITATIVE,
    "sync": BoundaryClass.AUTHORITATIVE,  # specific leaves may be diagnostic-only, but authority is engine-owned
    "tasks": BoundaryClass.AUTHORITATIVE,  # orchestration surface; may mutate state
    # ------------------------------------------------------------------
    # Diagnostic (read-only, deterministic)
    # ------------------------------------------------------------------
    "blueprint": BoundaryClass.DIAGNOSTIC,
    "cli": BoundaryClass.DIAGNOSTIC,
    "delta": BoundaryClass.DIAGNOSTIC,
    "dev": BoundaryClass.DIAGNOSTIC,
    "diag": BoundaryClass.DIAGNOSTIC,
    "drift": BoundaryClass.DIAGNOSTIC,
    "hub": BoundaryClass.DIAGNOSTIC,
    "init": BoundaryClass.DIAGNOSTIC,
    "inspect": BoundaryClass.DIAGNOSTIC,
    "keys": BoundaryClass.DIAGNOSTIC,
    "list": BoundaryClass.DIAGNOSTIC,
    "plugins": BoundaryClass.DIAGNOSTIC,
    "registry": BoundaryClass.DIAGNOSTIC,
    "registry-tools": BoundaryClass.DIAGNOSTIC,
    "routing": BoundaryClass.DIAGNOSTIC,
    # ------------------------------------------------------------------
    # Presentation / convenience
    # ------------------------------------------------------------------
    "docs": BoundaryClass.PRESENTATION,
    "ui": BoundaryClass.PRESENTATION,
    "version": BoundaryClass.PRESENTATION,
    # ------------------------------------------------------------------
    # Backward-compat top-level aliases (classified here for determinism)
    # ------------------------------------------------------------------
    "sync-remote": BoundaryClass.AUTHORITATIVE,
    "sync-status": BoundaryClass.DIAGNOSTIC,
}


# ---------------------------------------------------------------------------
# Public Resolution API
# ---------------------------------------------------------------------------


def resolve_boundary(args: Any) -> BoundaryResolution:
    """
    Resolve the boundary class for a parsed argparse invocation.

    Resolution order:
        1) Exact path match in BOUNDARY_BY_PATH (including resolvers)
        2) Top-level fallback in BOUNDARY_BY_TOP_LEVEL
        3) Unresolved => raises ValueError (caller converts to CommandError)

    This method does not write output and does not mutate state.
    """
    path = _path_from_args(args)
    if not path:
        raise ValueError("Cannot resolve boundary: missing command path.")

    entry = BOUNDARY_BY_PATH.get(path)
    if entry is not None:
        if callable(entry):
            boundary = entry(args)
            return BoundaryResolution(
                boundary=boundary,
                path=path,
                note="path:resolver",
            )
        return BoundaryResolution(
            boundary=entry,
            path=path,
            note="path:static",
        )

    top = path[0]
    top_boundary = BOUNDARY_BY_TOP_LEVEL.get(top)
    if top_boundary is not None:
        return BoundaryResolution(
            boundary=top_boundary,
            path=path,
            note="top-level:fallback",
        )

    raise ValueError(f"Cannot resolve boundary: no registry entry for '{top}'.")


# ---------------------------------------------------------------------------
# Introspection / Future-Proofing Helpers
# ---------------------------------------------------------------------------


def get_known_dual_mode_paths() -> Sequence[CommandPath]:
    """
    Return command paths that are intentionally dual-mode and require a resolver.

    Tests use this to assert that dual-mode declarations remain explicit.
    """
    out: List[CommandPath] = []
    for path, entry in BOUNDARY_BY_PATH.items():
        if callable(entry):
            out.append(path)
    return tuple(out)


def is_registry_exportable() -> bool:
    """
    Indicates whether this registry can be exported to JSON without lossy
    transformation.

    Returns True only if the registry contains no callable resolvers.
    This check is intentionally conservative.
    """
    for _path, entry in BOUNDARY_BY_PATH.items():
        if callable(entry):
            return False
    return True
