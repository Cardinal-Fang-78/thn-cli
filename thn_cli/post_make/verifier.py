from __future__ import annotations

"""
Post-Make Output Verifier (Hybrid-Standard)
===========================================

RESPONSIBILITIES
----------------
Provides **authoritative post-make verification** for scaffold outputs.

This module is responsible for:
    • Loading the authoritative scaffold manifest (.thn-tree.json)
    • Enumerating the actual filesystem state after make/migrate
    • Comparing expected_paths against actual paths (schema v2+)
    • Raising structured verification failures when invariants are violated

This verifier enforces the **post-make safety contract**:
    - The scaffold on disk must exactly match the expected structure
      declared in the manifest after make or migration.

CONTRACT STATUS
---------------
⚠️ AUTHORITATIVE VERIFICATION LOGIC — SEMANTICS LOCKED

Any change to this module may:
    • Alter post-make safety guarantees
    • Change failure detection behavior
    • Affect migration correctness
    • Break golden tests or recovery workflows

Changes MUST:
    • Preserve deterministic behavior
    • Maintain schema-version gating
    • Emit PostMakeVerificationError on failure

NON-GOALS
---------
• This module does NOT modify filesystem state
• This module does NOT write manifests or snapshots
• This module does NOT format CLI output
• This module does NOT attempt auto-repair

All remediation is handled by higher-level tooling.
"""

import json
from pathlib import Path
from typing import List, Set

from .errors import PostMakeVerificationError
from .snapshot import norm_rel

MANIFEST_NAME = ".thn-tree.json"


# ---------------------------------------------------------------------------
# Manifest Loading
# ---------------------------------------------------------------------------


def _load_manifest(root: Path) -> dict:
    """
    Load and minimally validate the scaffold manifest.

    Raises PostMakeVerificationError if the manifest is missing,
    unreadable, or structurally invalid.
    """
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.exists():
        raise PostMakeVerificationError(f"Post-make verify failed: missing {MANIFEST_NAME}")

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        raise PostMakeVerificationError(f"Post-make verify failed: invalid JSON in {MANIFEST_NAME}")

    if not isinstance(data, dict):
        raise PostMakeVerificationError(
            f"Post-make verify failed: {MANIFEST_NAME} must be a JSON object"
        )

    return data


# ---------------------------------------------------------------------------
# Filesystem Enumeration
# ---------------------------------------------------------------------------


def _walk_actual_paths(root: Path) -> Set[str]:
    """
    Collect all actual scaffold paths relative to root.

    Behavior:
        • Excludes the manifest itself
        • Includes both files and directories
        • Normalizes all paths to forward-slash form
        • Deterministic set-based output
    """
    actual: Set[str] = set()

    for p in root.rglob("*"):
        if p.name == MANIFEST_NAME:
            continue
        try:
            rel = norm_rel(p.relative_to(root).as_posix())
        except Exception:
            continue
        actual.add(rel)

    # Explicitly include directories (even if empty)
    for p in root.rglob("*"):
        if p.is_dir():
            try:
                rel = norm_rel(p.relative_to(root).as_posix())
            except Exception:
                continue
            actual.add(rel)

    return actual


# ---------------------------------------------------------------------------
# Public Verification Entry Point
# ---------------------------------------------------------------------------


def verify_make_output(ctx) -> None:
    """
    Verify that the post-make filesystem state matches manifest expectations.

    Behavior:
        • No-op for schema versions < 2
        • Strict comparison for schema v2+
        • Raises PostMakeVerificationError on any mismatch
    """
    root = Path(ctx.output_path).resolve()

    manifest = _load_manifest(root)

    schema_version = manifest.get("schema_version", 1)
    expected: List[str] = manifest.get("expected_paths", [])

    # Schema v1 and earlier do not define expected_paths
    if schema_version < 2:
        return

    expected_set = {norm_rel(p) for p in expected}
    actual_set = _walk_actual_paths(root)

    missing = sorted(p for p in expected_set if p not in actual_set)
    extra = sorted(p for p in actual_set if p not in expected_set)

    if missing or extra:
        lines = ["Post-make verify failed (schema v2):"]
        for p in missing:
            lines.append(f"- missing: {p}")
        for p in extra:
            lines.append(f"- extra: {p}")
        raise PostMakeVerificationError("\n".join(lines))
