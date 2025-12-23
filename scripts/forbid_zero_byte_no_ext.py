#!/usr/bin/env python3
"""
Block zero-byte files with no extension.

Purpose:
    Prevent accidental CMD.exe artifact files that silently appear
    due to Windows shell parsing errors.

Behavior:
    • Recursively scan the repository
    • Detect files with:
          - size == 0 bytes
          - no file extension
    • Exclude virtual environments (venv/)
    • Fail with a clear diagnostic if any are found

This script is intentionally cross-platform and CI-safe.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    root = Path(".").resolve()
    offenders: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        # Exclude virtual environments
        if "venv" in path.parts:
            continue

        try:
            if path.stat().st_size == 0 and path.suffix == "":
                offenders.append(path)
        except OSError:
            # If we cannot stat a file, ignore it
            continue

    if offenders:
        print()
        print("ERROR: Zero-byte files with no extension detected.", file=sys.stderr)
        print(
            "These are usually caused by CMD.exe parsing mistakes.",
            file=sys.stderr,
        )
        print(file=sys.stderr)

        for file in offenders:
            print(f" - {file}", file=sys.stderr)

        print(file=sys.stderr)
        print(
            "Fix: delete these files and use PowerShell instead of cmd.exe.",
            file=sys.stderr,
        )
        print(file=sys.stderr)

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
