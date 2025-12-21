from __future__ import annotations

"""
THN Snapshot Store (Hybrid-Standard)

Responsibilities:
    • Provide a durable, ordered snapshot store rooted at <scaffold>/.thn/snapshots
    • Maintain a snapshot index for fast lookup and sequencing
    • Preserve ordering guarantees (index is authoritative)
    • Provide backward compatibility with legacy index formats

Phase 4.2 upgrades:
    • Converge snapshot index + metadata:
        - Index schema v2 stores ordered entries with lightweight metadata
        - Backward compatible load from v1 (snapshots: ["0001", ...])
    • Add helpers:
        - latest_snapshot_id()
        - latest_snapshot_entry()
        - list_snapshot_entries()
    • Ensure snapshot JSON payloads are written with:
        - id (snapshot_id)
        - created_at (if missing)
        - _metadata (compact, normalized)

Guarantees:
    • Index ordering is authoritative when present
    • All writes are atomic (tmp + replace)
    • Read operations tolerate missing or corrupt index/snapshots safely
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from thn_cli.snapshots.snapshot_metadata import build_index_entry, normalize_index_entry

_INDEX_SCHEMA_VERSION = 2


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


@dataclass(frozen=True)
class SnapshotIndex:
    """
    Index stored alongside snapshot records for fast lookup and sequencing.

    v2 format:
        schema_version: 2
        last_id: int
        snapshots: List[Dict[str, Any]]  # ordered entries with at least {"id": "0001"}

    v1 compatibility:
        snapshots: List[str]  # ordered snapshot_id strings
    """

    schema_version: int
    last_id: int
    snapshots: List[Dict[str, Any]]


def default_snapshot_root(scaffold_root: Path) -> Path:
    return scaffold_root / ".thn" / "snapshots"


def index_path(snapshot_root: Path) -> Path:
    return snapshot_root / "index.json"


def snapshot_path(snapshot_root: Path, snapshot_id: str) -> Path:
    return snapshot_root / f"{snapshot_id}.json"


def _coerce_entries(raw: Any) -> List[Dict[str, Any]]:
    """
    Accept either v1 List[str] or v2 List[dict] and normalize to List[dict].
    """
    if not isinstance(raw, list):
        return []

    out: List[Dict[str, Any]] = []

    for item in raw:
        if isinstance(item, str):
            out.append({"id": item})
        elif isinstance(item, dict):
            out.append(normalize_index_entry(item))
        else:
            continue

    # Drop entries with missing/blank ids
    return [e for e in out if isinstance(e.get("id"), str) and e.get("id").strip()]


def load_index(snapshot_root: Path) -> SnapshotIndex:
    data = _read_json(index_path(snapshot_root)) or {}

    schema_version = int(data.get("schema_version", 1))
    last_id = int(data.get("last_id", 0))
    entries = _coerce_entries(data.get("snapshots", []))

    # If v1 but entries exist, keep them and upgrade schema in-memory.
    if schema_version < _INDEX_SCHEMA_VERSION:
        schema_version = _INDEX_SCHEMA_VERSION

    # If last_id is missing or inconsistent, recompute conservatively.
    if last_id <= 0 and entries:
        # snapshot ids are zero-padded ints; tolerate non-int ids by skipping
        parsed: List[int] = []
        for e in entries:
            sid = str(e.get("id") or "")
            try:
                parsed.append(int(sid))
            except Exception:
                continue
        last_id = max(parsed) if parsed else 0

    return SnapshotIndex(schema_version=schema_version, last_id=last_id, snapshots=entries)


def save_index(snapshot_root: Path, idx: SnapshotIndex) -> None:
    payload = {
        "schema_version": int(idx.schema_version or _INDEX_SCHEMA_VERSION),
        "last_id": int(idx.last_id or 0),
        "snapshots": [normalize_index_entry(e) for e in (idx.snapshots or [])],
    }
    _atomic_write_json(index_path(snapshot_root), payload)


def list_snapshot_entries(snapshot_root: Path) -> List[Dict[str, Any]]:
    return list(load_index(snapshot_root).snapshots)


def list_snapshots(snapshot_root: Path) -> List[str]:
    return [str(e.get("id")) for e in load_index(snapshot_root).snapshots if e.get("id")]


def latest_snapshot_entry(snapshot_root: Path) -> Optional[Dict[str, Any]]:
    entries = load_index(snapshot_root).snapshots
    return entries[-1] if entries else None


def latest_snapshot_id(snapshot_root: Path) -> Optional[str]:
    entry = latest_snapshot_entry(snapshot_root)
    if not entry:
        return None
    sid = entry.get("id")
    return str(sid) if isinstance(sid, str) and sid.strip() else None


def next_snapshot_id(snapshot_root: Path, width: int = 4) -> Tuple[str, SnapshotIndex]:
    idx = load_index(snapshot_root)
    nid = int(idx.last_id) + 1
    sid = str(nid).zfill(width)

    new_entries = [*idx.snapshots, {"id": sid}]
    new_idx = SnapshotIndex(
        schema_version=_INDEX_SCHEMA_VERSION,
        last_id=nid,
        snapshots=new_entries,
    )
    return sid, new_idx


def _finalize_snapshot_payload(snapshot_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the snapshot payload includes minimal identity + metadata fields.

    Does not attempt to enforce a full schema; it only normalizes the
    invariants needed for diagnostics and index convergence.
    """
    out = dict(payload) if isinstance(payload, dict) else {}

    out.setdefault("id", snapshot_id)
    out.setdefault("schema_version", out.get("schema_version", 1))
    out.setdefault("created_at", _utc_now_iso())

    # Provide a compact metadata block for diagnostics/GUI (non-authoritative).
    meta = out.get("_metadata")
    if not isinstance(meta, dict):
        meta = {}
    meta.setdefault("created_at", out.get("created_at"))
    meta.setdefault("source", out.get("source"))
    meta.setdefault("notes", out.get("notes") if isinstance(out.get("notes"), list) else [])
    out["_metadata"] = meta

    return out


def write_snapshot(snapshot_root: Path, snapshot_id: str, payload: Dict[str, Any]) -> None:
    """
    Write snapshot JSON atomically.

    Note: This function writes only the snapshot file. Index updates should
    be performed by write_snapshot_and_update_index().
    """
    finalized = _finalize_snapshot_payload(snapshot_id, payload)
    _atomic_write_json(snapshot_path(snapshot_root, snapshot_id), finalized)


def read_snapshot(snapshot_root: Path, snapshot_id: str) -> Optional[Dict[str, Any]]:
    return _read_json(snapshot_path(snapshot_root, snapshot_id))


def write_snapshot_and_update_index(
    snapshot_root: Path,
    snapshot_id: str,
    payload: Dict[str, Any],
) -> SnapshotIndex:
    """
    Canonical write path: write snapshot JSON, then update index with metadata.

    Returns the updated in-memory index.
    """
    snapshot_root.mkdir(parents=True, exist_ok=True)

    finalized = _finalize_snapshot_payload(snapshot_id, payload)
    write_snapshot(snapshot_root, snapshot_id, finalized)

    idx = load_index(snapshot_root)

    # Replace existing entry if present (id match), else append.
    new_entry = build_index_entry(snapshot_id, finalized)

    entries: List[Dict[str, Any]] = []
    found = False
    for e in idx.snapshots:
        if str(e.get("id")) == snapshot_id:
            entries.append(normalize_index_entry(new_entry))
            found = True
        else:
            entries.append(normalize_index_entry(e))

    if not found:
        entries.append(normalize_index_entry(new_entry))

    # last_id must track numeric max where possible
    try:
        numeric_id = int(snapshot_id)
        last_id = max(int(idx.last_id), numeric_id)
    except Exception:
        last_id = int(idx.last_id)

    new_idx = SnapshotIndex(
        schema_version=_INDEX_SCHEMA_VERSION,
        last_id=last_id,
        snapshots=entries,
    )
    save_index(snapshot_root, new_idx)
    return new_idx
