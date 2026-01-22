#!/usr/bin/env python
"""
Developer-only advisory verification tool.

PURPOSE
-------
Validates parity between:
    - thn_cli.commands.__all__          (authoritative CLI registry)
    - docs/cli/THN_CLI_Command_Inventory.md (Top-level command inventory only)

This tool verifies **top-level, user-visible CLI commands** only.
Path-level commands (e.g. `thn sync apply`) are intentionally excluded.

INVARIANTS
----------
- Read-only
- Deterministic
- Non-authoritative
- Developer-only (not runtime, CI, or release gating)
- Fails loudly on any mismatch or parse ambiguity

EXIT CODES
----------
0 = Perfect match
1 = Registry / documentation mismatch
2 = Script or parse error
"""

from __future__ import annotations

import importlib
import pathlib
import re
import sys
from typing import Iterable, Set

# ---------------------------------------------------------------------------
# Explicit sources of truth (DO NOT INLINE)
# ---------------------------------------------------------------------------

SOURCE_OF_TRUTH = "thn_cli.commands.__all__"
INVENTORY_DOC = pathlib.Path("docs/cli/THN_CLI_Command_Inventory.md")

# ---------------------------------------------------------------------------
# Registry normalization rules
# ---------------------------------------------------------------------------

# Maps registry module names to CLI commands.
# None means "intentionally excluded (non-command / adapter / alias-only)".
MODULE_TO_COMMAND_MAP = {
    # Pluralization mismatch
    "commands_blueprints": "blueprint",
    # Top-level CDC / delta domain
    "commands_sync_delta": "delta",
    # Backward-compat aliases that ARE real commands
    "commands_sync_status_alias": "sync-status",
    # Internal routing adapters (not top-level commands)
    "commands_sync_web": None,
    # Explicit presentation command
    "commands_version": "version",
}

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _die(message: str, *, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def _load_registry_modules() -> Set[str]:
    try:
        module = importlib.import_module("thn_cli.commands")
    except Exception as exc:
        _die(f"Failed to import thn_cli.commands: {exc}")

    if not hasattr(module, "__all__"):
        _die("thn_cli.commands has no __all__")

    return set(module.__all__)


def _extract_top_level_commands(registry_modules: Iterable[str]) -> Set[str]:
    """
    Convert commands_* module names into top-level CLI command names,
    applying explicit normalization and exclusions.
    """
    commands: Set[str] = set()

    for mod in registry_modules:
        if not mod.startswith("commands_"):
            continue

        # Explicit mapping wins
        if mod in MODULE_TO_COMMAND_MAP:
            mapped = MODULE_TO_COMMAND_MAP[mod]
            if mapped is not None:
                commands.add(mapped)
            continue

        # Default transformation
        name = mod[len("commands_") :]

        # Defensive guard: internal helpers should never leak
        if name.endswith("_alias"):
            continue

        commands.add(name.replace("_", "-"))

    return commands


def _parse_inventory_doc(path: pathlib.Path) -> Set[str]:
    """
    Parse ONLY the 'Top-Level Command Inventory' table.

    This intentionally ignores:
    - Path-level override tables
    - Legacy shim tables
    """
    if not path.exists():
        _die(f"Inventory document not found: {path}")

    text = path.read_text(encoding="utf-8")

    # Isolate the Top-Level Command Inventory section
    section_re = re.compile(
        r"## Top-Level Command Inventory(.*?)\n## ",
        re.DOTALL,
    )

    match = section_re.search(text + "\n## ")
    if not match:
        _die("Failed to locate 'Top-Level Command Inventory' section")

    section = match.group(1)

    row_re = re.compile(r"^\|\s*`thn\s+([^`]+)`\s*\|", re.MULTILINE)
    commands = set(cmd.strip() for cmd in row_re.findall(section))

    if not commands:
        _die("No commands parsed from Top-Level Command Inventory")

    # Guard: ensure no silent row loss
    raw_rows = [line for line in section.splitlines() if line.lstrip().startswith("| `thn ")]

    if len(commands) != len(raw_rows):
        _die(
            "Unparsed rows detected in Top-Level Command Inventory. "
            "Refusing to proceed to avoid silent drift."
        )

    return commands


# ---------------------------------------------------------------------------
# Main verification
# ---------------------------------------------------------------------------


def main() -> None:
    registry_modules = _load_registry_modules()
    registry_commands = _extract_top_level_commands(registry_modules)
    doc_commands = _parse_inventory_doc(INVENTORY_DOC)

    missing_in_doc = registry_commands - doc_commands
    extra_in_doc = doc_commands - registry_commands

    if not missing_in_doc and not extra_in_doc:
        print("OK: CLI registry and inventory document are in sync.")
        sys.exit(0)

    print("CLI INVENTORY MISMATCH DETECTED\n")

    if missing_in_doc:
        print("Commands present in registry but missing from inventory:")
        for name in sorted(missing_in_doc):
            print(f"  - thn {name}")
        print()

    if extra_in_doc:
        print("Commands present in inventory but missing from registry:")
        for name in sorted(extra_in_doc):
            print(f"  - thn {name}")
        print()

    sys.exit(1)


if __name__ == "__main__":
    main()
