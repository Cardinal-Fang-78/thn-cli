from __future__ import annotations

"""
Scaffold Drift Preview Engine (Diagnostic-Only, Hybrid-Standard)
===============================================================

RESPONSIBILITIES
----------------
Provides a **canonical, read-only drift preview** for scaffolds.

This module is responsible for:
    • Loading scaffold manifests (best-effort)
    • Enumerating actual filesystem state
    • Normalizing expected paths across schema versions
    • Computing missing and extra paths
    • Producing a deterministic structural diff
    • Classifying drift using merged rules (schema v2+)

This engine is used by:
    • thn inspect scaffold
    • drift preview
    • drift accept (preflight only)
    • migration preflight
    • future GUI inspection flows

CONTRACT STATUS
---------------
⚠️ DIAGNOSTIC-ONLY — NON-AUTHORITATIVE

This module:
    • MUST NOT mutate filesystem state
    • MUST NOT write manifests or snapshots
    • MUST NOT accept or reject drift
    • MUST NOT enforce policy

Its output is **informational** and may evolve without
constituting a breaking contract.

AUTHORITATIVE SOURCES
---------------------
Authoritative enforcement occurs in:
    • post_make.verifier
    • drift accept / migrate logic
    • migration engine
    • snapshot capture

NON-GOALS
---------
• This module does NOT persist state
• This module does NOT enforce correctness
• This module does NOT block execution
• This module does NOT resolve conflicts
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set

from thn_cli.post_make.classifier import classify_drift
from thn_cli.post_make.rules_loader import load_project_rules, merge_rules

MANIFEST_NAME = ".thn-tree.json"


# ---------------------------------------------------------------------------
# Path normalization helpers
# ---------------------------------------------------------------------------


def _norm_rel(p: str) -> str:
    p = p.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.strip("/")


def _walk_rel_paths(root: Path) -> Set[str]:
    """
    Enumerate all scaffold paths relative to root.

    Behavior:
        • Excludes the manifest itself
        • Normalizes to forward-slash paths
        • Deterministic and read-only
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
# Manifest loading / normalization
# ---------------------------------------------------------------------------


def _read_manifest(root: Path) -> Dict[str, Any]:
    """
    Best-effort manifest loader for diagnostic use.

    Failures are treated as empty manifests rather than errors.
    """
    manifest = root / MANIFEST_NAME
    if not manifest.exists():
        return {}

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def _normalize_expected_paths(
    *,
    expected_paths: List[str],
    root: Path,
) -> List[str]:
    """
    Normalize expected paths into scaffold-relative coordinates.

    Handles legacy manifests that include deep or absolute-like paths
    (e.g. DemoProj/modules/core/README.txt).
    """
    root_name = root.name
    normalized: List[str] = []

    for raw in expected_paths:
        if not isinstance(raw, str):
            continue

        p = _norm_rel(raw)

        parts = p.split("/")
        if root_name in parts:
            idx = parts.index(root_name)
            p = "/".join(parts[idx + 1 :])

        normalized.append(_norm_rel(p))

    return normalized


# ---------------------------------------------------------------------------
# Diff construction
# ---------------------------------------------------------------------------


def _build_diff(
    *,
    missing: List[str],
    extra: List[str],
) -> List[Dict[str, str]]:
    """
    Deterministic structural diff.

    Semantics:
        extra   → present but not expected → add
        missing → expected but absent      → remove
    """
    diff: List[Dict[str, str]] = []

    for p in sorted(extra):
        diff.append({"op": "add", "path": p})

    for p in sorted(missing):
        diff.append({"op": "remove", "path": p})

    return diff


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def preview_scaffold_drift(path: Path) -> Dict[str, Any]:
    """
    Preview scaffold drift in a read-only, diagnostic manner.

    Returns a normalized structure suitable for CLI, tests, or GUI use.
    """
    root = path.resolve()
    manifest = _read_manifest(root)

    blueprint = manifest.get("blueprint", {})
    schema_version = manifest.get("schema_version", 1)

    expected = _normalize_expected_paths(
        expected_paths=manifest.get("expected_paths", []),
        root=root,
    )

    actual = _walk_rel_paths(root)

    missing = sorted(set(expected) - actual)
    extra = sorted(actual - set(expected))

    # -------------------------
    # Schema v1: strict
    # -------------------------
    if schema_version == 1:
        status = "clean" if not missing and not extra else "drifted"
        return {
            "status": status,
            "path": str(root),
            "blueprint": blueprint,
            "missing": missing,
            "extra": extra,
            "diff": _build_diff(missing=missing, extra=extra),
            "notes": [],
        }

    # -------------------------
    # Schema v2+: classified
    # -------------------------
    project_rules = load_project_rules(root)
    merged_rules = merge_rules(manifest.get("rules"), project_rules)

    classified = classify_drift(
        expected=expected,
        missing=missing,
        extra=extra,
        rules=merged_rules,
    )

    diff = _build_diff(
        missing=classified["missing"],
        extra=classified["extra"],
    )

    return {
        "status": classified["status"],
        "path": str(root),
        "blueprint": blueprint,
        "missing": classified["missing"],
        "extra": classified["extra"],
        "diff": diff,
        "notes": classified.get("notes", []),
    }
