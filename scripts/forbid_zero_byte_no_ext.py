#!/usr/bin/env python3
"""
Detect and report shell artifact files.

Purpose:
    Prevent accidental shell artifact files that silently appear
    due to Windows shell parsing or redirection behavior.

Behavior:
    • Recursively scan the repository
    • Detect files with:
          - size == 0 bytes                  → HARD ERROR
          - no extension + known transient   → NOTICE (ERROR in --strict)
          - no extension + unknown name      → NOTICE (advisory)
    • Exclude VCS and tooling internals
    • Read-only, deterministic, CI-safe
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXCLUDED_DIRS = {
    ".git",
    ".nox",
    ".pytest_cache",
}

EXCLUDED_SUFFIXES = {
    ".egg-info",
}

LEGIT_EXTENSIONLESS_FILES = {
    "Makefile",
}

KNOWN_TRANSIENT_FILES = {
    "nox",
}


def _is_excluded(path: Path) -> bool:
    parts = set(path.parts)

    if parts & EXCLUDED_DIRS:
        return True

    for part in path.parts:
        for suffix in EXCLUDED_SUFFIXES:
            if part.endswith(suffix):
                return True

    return False


def main(argv: list[str]) -> int:
    strict_mode = "--strict" in argv
    json_mode = "--json" in argv
    explain_mode = "--explain" in argv

    root = Path(".").resolve()

    zero_byte_offenders: list[Path] = []
    transient_artifacts: list[Path] = []
    unknown_extensionless: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if _is_excluded(path):
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue

        if path.suffix == "":
            if path.name.startswith("."):
                continue

            if path.name in LEGIT_EXTENSIONLESS_FILES:
                continue

            if size == 0:
                zero_byte_offenders.append(path)
            elif path.name in KNOWN_TRANSIENT_FILES:
                transient_artifacts.append(path)
            else:
                unknown_extensionless.append(path)

    # ------------------------------------------------------------------
    # JSON MODE
    # ------------------------------------------------------------------

    if json_mode:
        if zero_byte_offenders:
            status = "error"
        elif transient_artifacts and strict_mode:
            status = "error"
        elif transient_artifacts or unknown_extensionless:
            status = "warning"
        else:
            status = "ok"

        payload = {
            "status": status,
            "zero_byte_files": [str(p) for p in zero_byte_offenders],
            "known_transient_files": [str(p) for p in transient_artifacts],
            "unknown_extensionless_files": [str(p) for p in unknown_extensionless],
            "strict": strict_mode,
        }

        print(json.dumps(payload, indent=2))
        return 1 if status == "error" else 0

    # ------------------------------------------------------------------
    # Human-readable output
    # ------------------------------------------------------------------

    had_output = False

    if transient_artifacts:
        had_output = True
        print(file=sys.stderr)
        print(
            (
                "ERROR: Known transient shell artifacts detected (--strict enabled)."
                if strict_mode
                else "NOTICE: Known transient shell artifacts detected (non-fatal)."
            ),
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for file in transient_artifacts:
            print(f" - {file}", file=sys.stderr)

    if unknown_extensionless:
        had_output = True
        print(file=sys.stderr)
        print(
            "NOTICE: Extensionless files with content detected (review recommended).",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for file in unknown_extensionless:
            print(f" - {file}", file=sys.stderr)

    if zero_byte_offenders:
        had_output = True
        print(file=sys.stderr)
        print(
            "ERROR: Zero-byte files with no extension detected.",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for file in zero_byte_offenders:
            print(f" - {file}", file=sys.stderr)
        print(file=sys.stderr)
        print(
            "Fix: delete these files and avoid shell redirection to bare filenames.",
            file=sys.stderr,
        )

    if not had_output:
        print("OK: No shell-generated junk files detected.")

    if zero_byte_offenders:
        return 1

    if transient_artifacts and strict_mode:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
