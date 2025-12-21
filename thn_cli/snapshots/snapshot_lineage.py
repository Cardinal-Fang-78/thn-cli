from __future__ import annotations

"""
THN Snapshot Lineage Graph (Hybrid-Standard)

Responsibilities:
    • Build a read-only lineage graph linking:
        - registry scaffold lineage
        - snapshot chain (index + optional payload reads)
        - recovery plan baseline metadata (if available)
    • Provide deterministic, GUI-ready nodes/edges
    • Emit diagnostic-only, non-blocking warnings

Guarantees:
    • Read-only (no filesystem writes)
    • Safe for missing/legacy data
    • Deterministic output ordering
    • Warnings are non-blocking and explicitly marked
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from thn_cli.snapshots.snapshot_metadata import (
    normalize_snapshot_metadata,
    snapshot_metadata_warnings,
)
from thn_cli.snapshots.snapshot_store import default_snapshot_root, load_index, read_snapshot


def _diag_warning(code: str, message: str) -> Dict[str, Any]:
    return {
        "severity": "warning",
        "blocking": False,
        "code": code,
        "message": message,
    }


def _read_registry_scaffold(root: Path) -> Optional[Dict[str, Any]]:
    p = root / ".thn" / "registry" / "scaffold.json"
    if not p.exists() or not p.is_file():
        return None
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    bp = payload.get("blueprint")
    if not isinstance(bp, dict):
        return None
    return {
        "path": str(p),
        "schema_version": payload.get("schema_version"),
        "blueprint": bp,
        "variables": payload.get("variables") if isinstance(payload.get("variables"), dict) else {},
    }


@dataclass(frozen=True)
class LineageGraph:
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


def build_lineage_graph(
    *,
    scaffold_root: Path,
    recovery_plan: Optional[Dict[str, Any]] = None,
    include_snapshot_payload_reads: bool = False,
) -> LineageGraph:
    """
    Build a lineage graph for diagnostics and GUI.

    include_snapshot_payload_reads:
        False: use index metadata only (fast)
        True:  also read snapshot JSONs to augment metadata + warnings (slower)
    """
    root = scaffold_root.resolve()

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # --- Registry node ---
    reg = _read_registry_scaffold(root)
    if reg:
        reg_node_id = "registry:scaffold"
        nodes.append(
            {
                "id": reg_node_id,
                "kind": "registry_scaffold",
                "path": reg.get("path"),
                "schema_version": reg.get("schema_version"),
                "blueprint": reg.get("blueprint"),
            }
        )
    else:
        reg_node_id = "registry:missing"
        nodes.append({"id": reg_node_id, "kind": "registry_missing"})
        warnings.append(
            _diag_warning("REGISTRY_MISSING", "Registry scaffold.json is missing or unreadable.")
        )

    # --- Snapshot chain nodes (index-driven) ---
    snap_root = default_snapshot_root(root)
    idx = load_index(snap_root) if snap_root.exists() else None
    snap_ids: List[str] = idx.snapshots if idx else []
    idx_meta: Dict[str, Dict[str, Any]] = idx.metadata if idx else {}

    snaps_node_id = "snapshots:root"
    nodes.append(
        {
            "id": snaps_node_id,
            "kind": "snapshots_root",
            "path": str(snap_root),
            "present": bool(snap_root.exists()),
            "count": len(snap_ids),
        }
    )

    if not snap_root.exists():
        warnings.append(
            _diag_warning(
                "SNAPSHOTS_ROOT_MISSING", "Snapshots root does not exist for this scaffold."
            )
        )
    elif not snap_ids:
        warnings.append(
            _diag_warning("SNAPSHOTS_EMPTY", "Snapshots root exists but no snapshots are indexed.")
        )

    # Create snapshot nodes in order and chain edges
    prev_node: Optional[str] = None
    for sid in snap_ids:
        node_id = f"snapshot:{sid}"

        meta = idx_meta.get(sid)
        if not isinstance(meta, dict):
            meta = {}

        nodes.append(
            {
                "id": node_id,
                "kind": "snapshot",
                "snapshot_id": sid,
                "path": str(snap_root / f"{sid}.json"),
                "metadata": meta,
            }
        )

        # root -> snapshot edge
        edges.append(
            {
                "from": snaps_node_id,
                "to": node_id,
                "kind": "contains",
            }
        )

        # chain edge
        if prev_node:
            edges.append({"from": prev_node, "to": node_id, "kind": "next"})
        prev_node = node_id

        # Optional payload read to enrich meta and warnings
        if include_snapshot_payload_reads:
            payload = read_snapshot(snap_root, sid) or {}
            if payload:
                # Merge normalized metadata if index lacks it
                if not meta:
                    nodes[-1]["metadata"] = normalize_snapshot_metadata(payload)
                warnings.extend(snapshot_metadata_warnings(payload))
            else:
                warnings.append(
                    _diag_warning("SNAPSHOT_UNREADABLE", f"Snapshot JSON could not be read: {sid}")
                )

    # --- Registry -> latest snapshot edge + mismatch warnings ---
    latest_sid = snap_ids[-1] if snap_ids else None
    if reg and latest_sid:
        latest_meta = idx_meta.get(latest_sid) or {}
        r_bp = reg.get("blueprint") or {}
        s_bp = (latest_meta.get("blueprint") or {}) if isinstance(latest_meta, dict) else {}

        edges.append(
            {
                "from": "registry:scaffold",
                "to": f"snapshot:{latest_sid}",
                "kind": "compared_to_latest",
            }
        )

        if r_bp.get("id") and s_bp.get("id") and r_bp.get("id") != s_bp.get("id"):
            warnings.append(
                _diag_warning(
                    "BLUEPRINT_ID_MISMATCH",
                    f"Registry blueprint id '{r_bp.get('id')}' differs from latest snapshot blueprint id '{s_bp.get('id')}'.",
                )
            )
        if r_bp.get("version") is not None and s_bp.get("version") is not None:
            if str(r_bp.get("version")) != str(s_bp.get("version")):
                warnings.append(
                    _diag_warning(
                        "BLUEPRINT_VERSION_MISMATCH",
                        f"Registry blueprint version '{r_bp.get('version')}' differs from latest snapshot blueprint version '{s_bp.get('version')}'.",
                    )
                )

    # --- Recovery plan node (optional) ---
    if isinstance(recovery_plan, dict):
        plan_node_id = "recovery_plan:current"
        plan_bp = recovery_plan.get("blueprint")
        plan_snapshot = recovery_plan.get("snapshot") or {}
        nodes.append(
            {
                "id": plan_node_id,
                "kind": "recovery_plan",
                "status": recovery_plan.get("status"),
                "blueprint": plan_bp if isinstance(plan_bp, dict) else {},
                "snapshot_baseline": plan_snapshot if isinstance(plan_snapshot, dict) else {},
            }
        )

        # edge: plan -> registry
        edges.append({"from": plan_node_id, "to": reg_node_id, "kind": "references_registry"})

        # edge: plan -> latest snapshot (if plan claims a snapshot baseline)
        if (
            latest_sid
            and isinstance(plan_snapshot, dict)
            and plan_snapshot.get("kind") not in (None, "none")
        ):
            edges.append(
                {"from": plan_node_id, "to": f"snapshot:{latest_sid}", "kind": "baseline_candidate"}
            )

    # Deterministic ordering
    nodes_sorted = sorted(nodes, key=lambda n: str(n.get("id", "")))
    edges_sorted = sorted(
        edges, key=lambda e: (str(e.get("from", "")), str(e.get("to", "")), str(e.get("kind", "")))
    )
    warnings_sorted = sorted(warnings, key=lambda w: str(w.get("code", "")))

    return LineageGraph(nodes=nodes_sorted, edges=edges_sorted, warnings=warnings_sorted)
