from __future__ import annotations

"""
THN Snapshot Metadata (Hybrid-Standard)

Responsibilities:
    • Provide a canonical, normalized snapshot metadata view (read-only)
    • Tolerate older snapshots and index entries that lack modern fields
    • Produce diagnostic-only warnings for missing metadata fields
    • Provide a compact metadata shape suitable for:
        - snapshot index entries
        - CLI diagnostics
        - future GUI consumption

Phase 4.2 upgrades:
    • Normalize metadata from either:
        - a full snapshot payload, or
        - an index entry (id + partial fields)
    • Provide helpers for index convergence:
        - build_index_entry()
        - normalize_index_entry()

Guarantees:
    • Pure functions (no filesystem writes)
    • Missing fields are handled safely and surfaced as non-blocking warnings
    • Warning outputs are explicitly non-blocking
"""

from typing import Any, Dict, List, Optional


def _diag_warning(code: str, message: str) -> Dict[str, Any]:
    return {
        "severity": "warning",
        "blocking": False,
        "code": code,
        "message": message,
    }


def normalize_snapshot_metadata(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a normalized metadata dict for a snapshot payload.

    Input may be:
        • A full snapshot JSON payload, OR
        • A dict that already resembles metadata / an index entry

    This function does NOT enforce schema and does not mutate the input.
    It produces a consistent shape for diagnostics and GUI usage.
    """
    meta: Dict[str, Any] = {}

    if not isinstance(snapshot, dict):
        return {
            "schema_version": 1,
            "id": None,
            "blueprint": {},
            "created_at": None,
            "source": None,
            "notes": [],
        }

    meta["schema_version"] = snapshot.get("schema_version", 1)
    meta["id"] = snapshot.get("id") or snapshot.get("snapshot_id") or snapshot.get("sid")

    bp = snapshot.get("blueprint") or {}
    if isinstance(bp, dict):
        meta["blueprint"] = {
            "id": bp.get("id"),
            "version": bp.get("version"),
        }
    else:
        meta["blueprint"] = {}

    meta["created_at"] = snapshot.get("created_at") or snapshot.get("_metadata", {}).get(
        "created_at"
    )
    meta["source"] = snapshot.get("source") or snapshot.get("_metadata", {}).get("source")

    notes = snapshot.get("notes") or snapshot.get("_metadata", {}).get("notes")
    meta["notes"] = notes if isinstance(notes, list) else []

    return meta


def snapshot_metadata_warnings(meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return diagnostic-only warnings for missing metadata fields.

    Expected warning shape:
        {
            "severity": "warning",
            "blocking": False,
            "code": "...",
            "message": "..."
        }
    """
    warnings: List[Dict[str, Any]] = []

    if not isinstance(meta, dict):
        return [_diag_warning("SNAPSHOT_META_INVALID", "Snapshot metadata is not a dict.")]

    if not meta.get("created_at"):
        warnings.append(
            _diag_warning(
                "SNAPSHOT_CREATED_AT_MISSING", "Snapshot is missing created_at timestamp."
            )
        )

    bp = meta.get("blueprint") or {}
    if not isinstance(bp, dict) or not bp.get("id"):
        warnings.append(
            _diag_warning("SNAPSHOT_BLUEPRINT_ID_MISSING", "Snapshot blueprint id is missing.")
        )

    # version can be string or int; treat None as missing
    if isinstance(bp, dict) and bp.get("version") is None:
        warnings.append(
            _diag_warning(
                "SNAPSHOT_BLUEPRINT_VERSION_MISSING", "Snapshot blueprint version is missing."
            )
        )

    return warnings


def build_index_entry(snapshot_id: str, snapshot_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a compact snapshot index entry from a full snapshot payload.
    """
    meta = normalize_snapshot_metadata(snapshot_payload)
    meta["id"] = snapshot_id

    # Keep index entries compact and stable.
    return {
        "id": snapshot_id,
        "schema_version": meta.get("schema_version", 1),
        "created_at": meta.get("created_at"),
        "source": meta.get("source"),
        "blueprint": meta.get("blueprint") if isinstance(meta.get("blueprint"), dict) else {},
    }


def normalize_index_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an index entry into the same compact shape expected by the index.

    Accepts legacy string-only ids converted to {"id": "..."} by the caller.
    """
    if not isinstance(entry, dict):
        return {
            "id": None,
            "schema_version": 1,
            "created_at": None,
            "source": None,
            "blueprint": {},
        }

    bp = entry.get("blueprint")
    if not isinstance(bp, dict):
        bp = {}

    return {
        "id": entry.get("id"),
        "schema_version": entry.get("schema_version", 1),
        "created_at": entry.get("created_at"),
        "source": entry.get("source"),
        "blueprint": (
            {
                "id": bp.get("id"),
                "version": bp.get("version"),
            }
            if isinstance(bp, dict)
            else {}
        ),
    }
