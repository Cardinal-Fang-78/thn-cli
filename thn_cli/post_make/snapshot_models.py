from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

SNAPSHOT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SnapshotBlueprint:
    id: str
    version: str


@dataclass(frozen=True)
class SnapshotRecord:
    """
    Immutable snapshot record.

    Snapshots are append-only and never rewritten once persisted.
    """

    schema_version: int
    snapshot_id: str  # e.g. "0001"
    at_utc: str  # ISO-8601 UTC, e.g. "2025-12-15T05:12:31Z"
    event: str  # e.g. "accept_drift", "make_project", "migrate_scaffold"
    path: str  # absolute scaffold root
    blueprint: SnapshotBlueprint
    status: str  # "clean" or "drifted" (from drift engine)
    tree: List[str]  # normalized relative paths (deterministic ordering)
    diff: List[Dict[str, str]]  # [{"op":"add"/"remove","path":"..."}]
    parent: Optional[str]  # previous snapshot_id or None
    note: Optional[str] = None  # optional user/admin note
    meta: Dict[str, Any] = None  # optional structured metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.snapshot_id,
            "at": self.at_utc,
            "event": self.event,
            "path": self.path,
            "blueprint": {"id": self.blueprint.id, "version": self.blueprint.version},
            "status": self.status,
            "tree": list(self.tree),
            "diff": list(self.diff),
            "parent": self.parent,
            "note": self.note,
            "meta": dict(self.meta or {}),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SnapshotRecord":
        bp = data.get("blueprint") or {}
        return SnapshotRecord(
            schema_version=int(data.get("schema_version", SNAPSHOT_SCHEMA_VERSION)),
            snapshot_id=str(data.get("id", "")),
            at_utc=str(data.get("at", "")),
            event=str(data.get("event", "")),
            path=str(data.get("path", "")),
            blueprint=SnapshotBlueprint(
                id=str(bp.get("id", "")),
                version=str(bp.get("version", "")),
            ),
            status=str(data.get("status", "")),
            tree=[str(x) for x in (data.get("tree") or []) if isinstance(x, str)],
            diff=[dict(x) for x in (data.get("diff") or []) if isinstance(x, dict)],
            parent=(str(data["parent"]) if data.get("parent") else None),
            note=(str(data["note"]) if data.get("note") else None),
            meta=(dict(data.get("meta") or {})),
        )
