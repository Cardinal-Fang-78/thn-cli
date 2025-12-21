from __future__ import annotations

"""
Scaffold Drift History Builder (Diagnostic-Only, Hybrid-Standard)
================================================================

RESPONSIBILITIES
----------------
Build a chronological, read-only history of scaffold evolution events.

This module:
    • Aggregates accepted drift records from the scaffold manifest
    • Aggregates migration records from the scaffold manifest
    • Correlates events with snapshot artifacts (best-effort)
    • Produces a deterministic timeline suitable for CLI or GUI display

The resulting history is:
    • Informational only
    • Immutable
    • Derived entirely from existing on-disk records

DATA SOURCES
------------
    • <scaffold>/.thn-tree.json
    • <scaffold>/.thn-snapshots/*.json

CONTRACT STATUS
---------------
⚠️ DIAGNOSTIC / PRESENTATION LAYER — NON-AUTHORITATIVE

This module does NOT:
    • Validate scaffold correctness
    • Recompute drift
    • Enforce policy
    • Mutate state
    • Infer missing history

All entries reflect only what has been explicitly recorded.

BEST-EFFORT GUARANTEES
---------------------
    • Missing or malformed files are tolerated
    • Snapshot correlation is heuristic (timestamp-based)
    • Ordering is stable when timestamps are present

NON-GOALS
---------
• This module is NOT a source of truth
• This module is NOT used by accept/migrate/apply flows
• This module does NOT repair or reconcile state
"""

import json
from pathlib import Path
from typing import Any, Dict, List

MANIFEST_NAME = ".thn-tree.json"
SNAPSHOT_DIR = ".thn-snapshots"


def _load_manifest(root: Path) -> Dict[str, Any]:
    p = root / MANIFEST_NAME
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _list_snapshots(root: Path) -> List[str]:
    d = root / SNAPSHOT_DIR
    if not d.exists():
        return []
    return sorted(p.name for p in d.glob("*.json"))


def build_drift_history(root: Path) -> List[Dict[str, Any]]:
    """
    Build an immutable drift timeline from manifest + snapshots.

    The returned list is sorted chronologically when timestamps are present.
    Missing or malformed data is skipped gracefully.
    """
    manifest = _load_manifest(root)
    snapshots = _list_snapshots(root)

    timeline: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Accepted drift records
    # ------------------------------------------------------------------
    accepted = manifest.get("accepted")
    if isinstance(accepted, dict):
        timeline.append(
            {
                "timestamp": accepted.get("at"),
                "type": "accept",
                "summary": "Accepted intentional scaffold changes",
                "details": accepted,
            }
        )

    # ------------------------------------------------------------------
    # Migration records
    # ------------------------------------------------------------------
    for mig in manifest.get("migrations", []):
        timeline.append(
            {
                "timestamp": mig.get("at"),
                "type": "migration",
                "summary": (
                    f"Migration from {mig.get('from', {}).get('version')} "
                    f"to {mig.get('to', {}).get('version')}"
                ),
                "details": mig,
            }
        )

    # ------------------------------------------------------------------
    # Best-effort snapshot association
    # ------------------------------------------------------------------
    for entry in timeline:
        ts = entry.get("timestamp", "")
        if not ts:
            continue
        match = next(
            (s for s in snapshots if s.startswith(ts.replace(":", "_"))),
            None,
        )
        if match:
            entry["snapshot"] = match

    return sorted(
        timeline,
        key=lambda e: e.get("timestamp") or "",
    )
