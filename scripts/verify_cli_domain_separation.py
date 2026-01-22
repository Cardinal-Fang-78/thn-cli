#!/usr/bin/env python
"""
Developer-only mechanical guard.

PURPOSE
-------
Enforces a hard structural invariant:

    Sync and Delta CLI domains must remain strictly separate.

No command module may combine both domains in its name or registration.

This prevents forbidden command shapes such as:
    - thn sync delta
    - thn sync-delta
    - commands_sync_delta.py

INVARIANTS
----------
- Read-only
- Deterministic
- Non-authoritative
- Developer-only
- Advisory safety net (not runtime or CI gating by default)

EXIT CODES
----------
0 = Invariant satisfied
1 = Invariant violation detected
2 = Script error
"""

from __future__ import annotations

import importlib
import sys
from typing import Iterable, List


def _die(message: str, *, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def _load_registry_modules() -> List[str]:
    try:
        module = importlib.import_module("thn_cli.commands")
    except Exception as exc:
        _die(f"Failed to import thn_cli.commands: {exc}")

    if not hasattr(module, "__all__"):
        _die("thn_cli.commands has no __all__")

    return list(module.__all__)


def _find_domain_collisions(modules: Iterable[str]) -> List[str]:
    """
    Detect command modules that combine sync and delta domains.
    """
    offenders: List[str] = []

    for mod in modules:
        if not mod.startswith("commands_"):
            continue

        name = mod[len("commands_") :]

        has_sync = "sync" in name.split("_")
        has_delta = "delta" in name.split("_")

        if has_sync and has_delta:
            offenders.append(mod)

    return offenders


def main() -> None:
    modules = _load_registry_modules()
    offenders = _find_domain_collisions(modules)

    if not offenders:
        print("OK: Sync and Delta CLI domains remain structurally separated.")
        sys.exit(0)

    print("CLI DOMAIN SEPARATION VIOLATION DETECTED\n")
    print("The following command modules illegally combine Sync and Delta domains:\n")

    for mod in sorted(offenders):
        print(f"  - {mod}")

    print(
        "\nThis violates the locked CLI invariant:\n"
        "  • Delta is a diagnostic domain\n"
        "  • Sync is an execution/transport domain\n"
        "  • They must never be semantically or structurally coupled\n"
    )

    sys.exit(1)


if __name__ == "__main__":
    main()
