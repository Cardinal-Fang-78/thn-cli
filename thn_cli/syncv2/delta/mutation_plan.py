# thn_cli/syncv2/delta/mutation_plan.py

"""
CDC Mutation Plan Derivation (Hybrid-Standard)
==============================================

RESPONSIBILITIES
----------------
Defines the **single authoritative derivation** of CDC mutation intent
from a Sync V2 manifest.

This logic is shared by:
    • syncv2.engine (authoritative APPLY)
    • syncv2.delta.inspectors (diagnostic INSPECT)

CONTRACT STATUS
---------------
⚠️ CORE SEMANTICS — LOCKED

Any change here:
    • Alters CDC apply semantics
    • MUST be reflected in inspection output
    • MUST be covered by golden tests

NON-GOALS
---------
• No filesystem access
• No payload inspection
• No validation enforcement
• No mutation or apply behavior
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Set, Tuple


def derive_cdc_mutation_plan(
    manifest: Dict[str, Any],
) -> Tuple[Set[str], Set[str]]:
    """
    Derive manifest-declared CDC mutation paths.

    Stage 1:
        manifest["files"]   -> writes

    Stage 2:
        manifest["entries"] -> writes + deletes

    Returns:
        (writes, deletes)

    Raises:
        ValueError if neither files nor entries declare any paths.
    """
    writes: Set[str] = set()
    deletes: Set[str] = set()

    # Stage 1 — legacy / file-based CDC
    declared_files = manifest.get("files")
    if isinstance(declared_files, list) and declared_files:
        for f in declared_files:
            if not isinstance(f, dict):
                continue
            p = f.get("path")
            if isinstance(p, str) and p.strip():
                writes.add(p.strip())
        if writes:
            return writes, deletes

    # Stage 2 — entry-based CDC
    entries: Iterable[Dict[str, Any]] = manifest.get("entries") or []
    if isinstance(entries, list) and entries:
        for e in entries:
            if not isinstance(e, dict):
                continue
            p = e.get("path")
            if not isinstance(p, str) or not p.strip():
                continue
            op = e.get("op", "write")
            if op == "delete":
                deletes.add(p.strip())
            else:
                writes.add(p.strip())
        if writes or deletes:
            return writes, deletes

    raise ValueError("CDC-delta manifest contains neither 'files' nor 'entries'")
