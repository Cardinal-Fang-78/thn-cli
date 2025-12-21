from __future__ import annotations

"""
Scaffold Inspector (Diagnostic-Only, Hybrid-Standard)
====================================================

RESPONSIBILITIES
----------------
Provides a **read-only diagnostic inspection** of a scaffold’s current state.

This module is responsible for:
    • Loading scaffold manifest metadata
    • Enumerating actual filesystem paths
    • Computing missing and extra paths
    • Merging scaffold and project-level rules
    • Classifying drift for diagnostic presentation

This inspector is used for:
    • Human-readable diagnostics
    • CLI inspection commands
    • Future GUI inspection views

CONTRACT STATUS
---------------
⚠️ DIAGNOSTIC-ONLY — NON-AUTHORITATIVE

This module:
    • MUST NOT mutate filesystem state
    • MUST NOT write manifests or snapshots
    • MUST NOT enforce acceptance or rejection
    • MUST NOT block make, migrate, or accept flows

Its outputs are **informational only** and may evolve
without constituting a breaking contract.

AUTHORITATIVE SOURCES
---------------------
Authoritative correctness is enforced by:
    • post_make.verifier (schema v2+ enforcement)
    • migrations.engine
    • drift acceptance logic

NON-GOALS
---------
• This module does NOT perform post-make verification
• This module does NOT decide correctness
• This module does NOT apply policy
• This module does NOT persist results
"""

import json
from pathlib import Path
from typing import Dict, List, Set

from .classifier import classify_drift
from .rules_loader import load_project_rules, merge_rules
from .verifier import MANIFEST_NAME, _norm_rel


class ScaffoldInspectionError(Exception):
    """Raised when scaffold inspection cannot be performed safely."""

    pass


# ---------------------------------------------------------------------------
# Filesystem Enumeration
# ---------------------------------------------------------------------------


def _walk_rel_paths(root: Path) -> Set[str]:
    """
    Walk the scaffold directory and return all relative paths.

    Behavior:
        • Excludes the manifest itself
        • Normalizes paths using _net_rel
        • Read-only and deterministic
    """
    rels: Set[str] = set()
    for item in root.rglob("*"):
        if item.name == MANIFEST_NAME:
            continue
        try:
            rel = item.relative_to(root).as_posix()
        except Exception:
            continue
        rels.add(_norm_rel(rel))
    return rels


# ---------------------------------------------------------------------------
# Manifest Loading
# ---------------------------------------------------------------------------


def _read_manifest(root: Path) -> Dict[str, object]:
    """
    Load minimal inspection metadata from the scaffold manifest.

    This function intentionally extracts only the fields needed
    for diagnostic inspection.
    """
    manifest = root / MANIFEST_NAME
    if not manifest.exists():
        raise ScaffoldInspectionError(f"Missing scaffold manifest: {manifest}")

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        raise ScaffoldInspectionError(f"Invalid JSON in {manifest}")

    if not isinstance(data, dict):
        raise ScaffoldInspectionError("Manifest must be a JSON object")

    return {
        "schema_version": data.get("schema_version", 1),
        "blueprint": data.get("blueprint"),
        "expected": [_norm_rel(p) for p in data.get("expected_paths", [])],
        "rules": data.get("rules"),
    }


# ---------------------------------------------------------------------------
# Public Inspection API
# ---------------------------------------------------------------------------


def inspect_scaffold(path: str) -> Dict[str, object]:
    """
    Inspect a scaffold directory and return a diagnostic summary.

    Returns:
        {
            "status": str,
            "path": str,
            "blueprint": dict | None,
            "missing": list[str],
            "extra": list[str],
            "notes": list[str],
        }
    """
    root = Path(path)

    if not root.exists() or not root.is_dir():
        raise ScaffoldInspectionError(f"Invalid scaffold path: {root}")

    manifest = _read_manifest(root)

    expected = manifest["expected"]
    actual = _walk_rel_paths(root)

    missing = sorted(set(expected) - actual)
    extra = sorted(actual - set(expected))

    # Only projects can define override rules
    project_rules = load_project_rules(root)
    merged_rules = merge_rules(manifest["rules"], project_rules)

    classified = classify_drift(
        expected=expected,
        missing=missing,
        extra=extra,
        rules=merged_rules,
    )

    return {
        "status": classified["status"],
        "path": str(root),
        "blueprint": manifest["blueprint"],
        "missing": classified["missing"],
        "extra": classified["extra"],
        "notes": classified.get("notes", []),
    }
