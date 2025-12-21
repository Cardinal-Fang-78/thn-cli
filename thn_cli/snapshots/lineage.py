from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SnapshotLineageError(Exception):
    pass


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SnapshotRecord:
    id: str
    parent_id: Optional[str]
    created_at: str
    reason: str
    blueprint_id: str
    blueprint_version: str
    txlog_run_id: Optional[str]
    notes: Optional[str]


@dataclass(frozen=True)
class SnapshotIndex:
    schema_version: int
    snapshots: Dict[str, SnapshotRecord]


# ---------------------------------------------------------------------------
# Loader / Validator
# ---------------------------------------------------------------------------

_INDEX_REL_PATH = Path(".thn") / "snapshots" / "index.json"
_SUPPORTED_SCHEMA_VERSION = 1


def load_snapshot_index(scaffold_root: Path) -> SnapshotIndex:
    """
    Load and validate the snapshot index from a scaffold.

    This function is read-only and performs no filesystem mutation.
    """
    index_path = (scaffold_root / _INDEX_REL_PATH).resolve()

    if not index_path.exists():
        raise SnapshotLineageError(f"Snapshot index not found: {index_path}")

    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SnapshotLineageError(f"Failed to parse snapshot index: {exc}") from exc

    if not isinstance(raw, dict):
        raise SnapshotLineageError("Snapshot index root must be a JSON object")

    schema_version = raw.get("schema_version")
    if schema_version != _SUPPORTED_SCHEMA_VERSION:
        raise SnapshotLineageError(f"Unsupported snapshot index schema_version: {schema_version}")

    raw_snaps = raw.get("snapshots")
    if not isinstance(raw_snaps, list):
        raise SnapshotLineageError("Snapshot index 'snapshots' must be a list")

    snapshots: Dict[str, SnapshotRecord] = {}

    for entry in raw_snaps:
        if not isinstance(entry, dict):
            raise SnapshotLineageError("Snapshot entry must be an object")

        try:
            rec = SnapshotRecord(
                id=str(entry["id"]),
                parent_id=entry.get("parent_id"),
                created_at=str(entry["created_at"]),
                reason=str(entry["reason"]),
                blueprint_id=str(entry["blueprint"]["id"]),
                blueprint_version=str(entry["blueprint"]["version"]),
                txlog_run_id=entry.get("txlog_run_id"),
                notes=entry.get("notes"),
            )
        except Exception as exc:
            raise SnapshotLineageError(f"Invalid snapshot entry: {exc}") from exc

        if rec.id in snapshots:
            raise SnapshotLineageError(f"Duplicate snapshot id detected: {rec.id}")

        snapshots[rec.id] = rec

    return SnapshotIndex(schema_version=schema_version, snapshots=snapshots)


# ---------------------------------------------------------------------------
# Lineage Resolution
# ---------------------------------------------------------------------------


def resolve_lineage(
    index: SnapshotIndex, *, snapshot_id: Optional[str] = None
) -> List[SnapshotRecord]:
    """
    Resolve a snapshot lineage chain.

    If snapshot_id is None, resolves from the most recent snapshot.
    Returns lineage ordered from root -> leaf.
    """
    if not index.snapshots:
        return []

    # Determine starting snapshot
    if snapshot_id:
        if snapshot_id not in index.snapshots:
            raise SnapshotLineageError(f"Snapshot id not found: {snapshot_id}")
        current = index.snapshots[snapshot_id]
    else:
        # Latest snapshot = lexicographically highest id
        current = index.snapshots[sorted(index.snapshots.keys())[-1]]

    chain: List[SnapshotRecord] = []
    seen: set[str] = set()

    while True:
        if current.id in seen:
            raise SnapshotLineageError(f"Cycle detected in snapshot lineage at {current.id}")
        seen.add(current.id)
        chain.append(current)

        if current.parent_id is None:
            break

        if current.parent_id not in index.snapshots:
            raise SnapshotLineageError(
                f"Missing parent snapshot '{current.parent_id}' for '{current.id}'"
            )

        current = index.snapshots[current.parent_id]

    return list(reversed(chain))


# ---------------------------------------------------------------------------
# Diagnostics Helpers
# ---------------------------------------------------------------------------


def validate_lineage_consistency(chain: List[SnapshotRecord]) -> List[str]:
    """
    Perform consistency checks across a resolved lineage chain.
    Returns a list of warning strings (empty if clean).
    """
    warnings: List[str] = []

    if not chain:
        return warnings

    root = chain[0]
    if root.parent_id is not None:
        warnings.append("Root snapshot has non-null parent_id")

    last_bp_id = root.blueprint_id
    for rec in chain[1:]:
        if rec.blueprint_id != last_bp_id:
            warnings.append(f"Blueprint changed across lineage: {last_bp_id} -> {rec.blueprint_id}")
        last_bp_id = rec.blueprint_id

    return warnings
