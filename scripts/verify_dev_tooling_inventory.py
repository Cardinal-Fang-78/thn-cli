#!/usr/bin/env python
"""
Developer-only advisory verification tool.

PURPOSE
-------
Validates parity between:
    - scripts/ directory contents
    - docs/DEV_TOOLING_INVENTORY.md

This tool verifies **developer-facing audit and utility scripts only**.

INVARIANTS
----------
- Read-only
- Deterministic
- Non-authoritative
- Developer-only (not runtime, CI, or release gating)
- Fails loudly on any mismatch or parse ambiguity
- Permits structure-only inventories (no tool rows yet)

EXIT CODES
----------
0 = Perfect match or structure-only inventory
1 = Inventory mismatch
2 = Script or parse error
"""

from __future__ import annotations

import pathlib
import re
import sys
from typing import Set

# ---------------------------------------------------------------------------
# Inventory scope classification (advisory only)
# ---------------------------------------------------------------------------

# NOTE:
# This list is advisory only.
# It does not enforce behavior or imply execution authority.

ALLOWED_SCOPES = {
    "Developer",
    "Audit / Verification",
    "Release",
    "Visualization",
}

# ---------------------------------------------------------------------------
# Explicit sources of truth
# ---------------------------------------------------------------------------

SCRIPTS_DIR = pathlib.Path("scripts")
INVENTORY_DOC = pathlib.Path("docs/DEV_TOOLING_INVENTORY.md")

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _die(message: str, *, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def _load_script_files() -> Set[str]:
    if not SCRIPTS_DIR.exists():
        _die(f"Scripts directory not found: {SCRIPTS_DIR}")

    return {
        path.name
        for path in SCRIPTS_DIR.iterdir()
        if path.is_file() and path.suffix in {".py", ".sh", ".ps1", ".bat"}
    }


def _parse_inventory(path: pathlib.Path) -> Set[str] | None:
    if not path.exists():
        _die(f"Inventory document not found: {path}")

    text = path.read_text(encoding="utf-8")

    row_re = re.compile(
        r"^\|\s*`([^`]+)`\s*\|\s*([^|]+)\|",
        re.MULTILINE,
    )

    entries = row_re.findall(text)

    # ------------------------------------------------------------------
    # STRUCTURE-ONLY INVENTORY: EARLY EXIT
    # ------------------------------------------------------------------
    if not entries:
        print(
            "NOTICE: DEV_TOOLING_INVENTORY.md contains no tool entries "
            "(structure-only inventory).",
            file=sys.stderr,
        )
        return None

    scripts: Set[str] = set()
    bad_scopes = set()

    for script, scope in entries:
        script = script.strip()
        scope = scope.strip()
        scripts.add(script)

        if scope not in ALLOWED_SCOPES:
            bad_scopes.add((script, scope))

    if bad_scopes:
        print("WARNING: Unrecognized scope values detected:")
        for script, scope in sorted(bad_scopes):
            print(f"  - {script}: '{scope}'")
        print("Allowed scopes:", ", ".join(sorted(ALLOWED_SCOPES)))
        print()

    raw_rows = [line for line in text.splitlines() if line.lstrip().startswith("| `")]

    if len(scripts) != len(raw_rows):
        _die(
            "Unparsed rows detected in DEV_TOOLING_INVENTORY.md. "
            "Refusing to proceed to avoid silent drift."
        )

    return scripts


# ---------------------------------------------------------------------------
# Main verification
# ---------------------------------------------------------------------------


def main() -> None:
    actual_scripts = _load_script_files()
    documented_scripts = _parse_inventory(INVENTORY_DOC)

    # ------------------------------------------------------------------
    # EARLY EXIT: STRUCTURE-ONLY INVENTORY
    # ------------------------------------------------------------------
    if documented_scripts is None:
        # Structure-only inventory: advisory, non-blocking
        sys.exit(0)

    actual_scripts = _load_script_files()

    missing_in_doc = actual_scripts - documented_scripts
    extra_in_doc = documented_scripts - actual_scripts

    if not missing_in_doc and not extra_in_doc:
        print("OK: DEV tooling inventory is in sync.")
        sys.exit(0)

    print("DEV TOOLING INVENTORY MISMATCH DETECTED\n")

    if missing_in_doc:
        print("Scripts present in scripts/ but missing from inventory:")
        for name in sorted(missing_in_doc):
            print(f"  - {name}")
        print()

    if extra_in_doc:
        print("Scripts present in inventory but missing from scripts/:")
        for name in sorted(extra_in_doc):
            print(f"  - {name}")
        print()

    sys.exit(1)


if __name__ == "__main__":
    main()
