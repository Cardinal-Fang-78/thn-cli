from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

MANIFEST_NAME = ".thn-tree.json"  # Legacy snapshots (older phases)
LEGACY_SNAPSHOT_DIR = ".thn-snapshots"  # Newer snapshots (index-based)
INDEX_SNAPSHOT_DIR = Path(".thn") / "snapshots"
INDEX_FILE = "index.json"


# ---------------------------------------------------------------------------
# Small utils (kept local to avoid cross-module import coupling in Phase 1)
# ---------------------------------------------------------------------------


def _norm_rel(p: str) -> str:
    p = p.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.strip("/")


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _load_manifest(root: Path) -> Dict[str, Any]:
    data = _read_json(root / MANIFEST_NAME)
    return data or {}


def _normalize_expected_paths(*, expected_paths: Sequence[Any], root: Path) -> List[str]:
    """
    Normalize expected paths into scaffold-relative coordinates.

    Handles legacy manifests that include deep paths like:
      DemoProj/modules/core/README.txt
    If the scaffold root name appears in the path segments, everything up to and
    including that segment is trimmed.
    """
    root_name = root.name
    out: List[str] = []

    for raw in expected_paths or []:
        if not isinstance(raw, str):
            continue

        p = _norm_rel(raw)
        parts = p.split("/")
        if root_name in parts:
            idx = parts.index(root_name)
            p = "/".join(parts[idx + 1 :])

        p = _norm_rel(p)
        if p:
            out.append(p)

    # Deterministic unique
    return sorted(set(out))


def _is_probably_file(rel_path: str) -> bool:
    """
    Heuristic only: if it has a suffix, treat as file; else directory.
    This is planning-only; execution can refine behavior later.
    """
    return bool(Path(rel_path).suffix)


def _abs_target(root: Path, rel_path: str) -> Path:
    return (root / Path(rel_path)).resolve()


def _is_internal_thn_path(rel_path: str) -> bool:
    rel = _norm_rel(rel_path)
    return rel == ".thn" or rel.startswith(".thn/")


# ---------------------------------------------------------------------------
# Snapshot loading (supports both index-based and legacy folders)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SnapshotRef:
    kind: str  # "index" | "legacy" | "none"
    snapshot_id: str
    path: Optional[Path]
    payload: Dict[str, Any]


def _load_index_snapshot(root: Path, snapshot_id: Optional[str]) -> Optional[SnapshotRef]:
    snap_root = root / INDEX_SNAPSHOT_DIR
    idx_path = snap_root / INDEX_FILE
    if not idx_path.exists():
        return None

    idx = _read_json(idx_path) or {}
    snaps = idx.get("snapshots", [])
    if not isinstance(snaps, list):
        snaps = []
    snaps_out = [str(x) for x in snaps if isinstance(x, str)]

    if not snaps_out:
        return SnapshotRef(kind="index", snapshot_id="", path=None, payload={})

    chosen = (
        snapshot_id.strip()
        if isinstance(snapshot_id, str) and snapshot_id.strip()
        else snaps_out[-1]
    )
    if chosen not in snaps_out:
        return SnapshotRef(kind="index", snapshot_id=chosen, path=None, payload={})

    p = snap_root / f"{chosen}.json"
    payload = _read_json(p) or {}
    return SnapshotRef(kind="index", snapshot_id=chosen, path=p, payload=payload)


def _load_legacy_snapshot(root: Path, snapshot_id: Optional[str]) -> Optional[SnapshotRef]:
    d = root / LEGACY_SNAPSHOT_DIR
    if not d.exists():
        return None

    snaps = sorted(p for p in d.glob("*.json") if p.is_file())
    if not snaps:
        return SnapshotRef(kind="legacy", snapshot_id="", path=None, payload={})

    if isinstance(snapshot_id, str) and snapshot_id.strip():
        cand = d / f"{snapshot_id.strip()}.json"
        if cand.exists():
            payload = _read_json(cand) or {}
            return SnapshotRef(kind="legacy", snapshot_id=cand.stem, path=cand, payload=payload)
        return SnapshotRef(kind="legacy", snapshot_id=snapshot_id.strip(), path=None, payload={})

    chosen_path = snaps[-1]
    payload = _read_json(chosen_path) or {}
    return SnapshotRef(
        kind="legacy", snapshot_id=chosen_path.stem, path=chosen_path, payload=payload
    )


def _pick_snapshot(root: Path, snapshot_id: Optional[str]) -> SnapshotRef:
    idx_ref = _load_index_snapshot(root, snapshot_id)
    if idx_ref is not None and (idx_ref.path is not None or idx_ref.snapshot_id == ""):
        return idx_ref

    legacy_ref = _load_legacy_snapshot(root, snapshot_id)
    if legacy_ref is not None and (legacy_ref.path is not None or legacy_ref.snapshot_id == ""):
        return legacy_ref

    return SnapshotRef(kind="none", snapshot_id="", path=None, payload={})


# ---------------------------------------------------------------------------
# Phase 2.4: Recovery plan semantics
# ---------------------------------------------------------------------------


def _semantics_for_missing_path(*, rel_path: str) -> str:
    """
    Classify recovery semantics:
      - placeholder_ok: mkdir is a correct end-state; internal THN paths are always structural
      - regen_recommended: blueprint-owned file likely needs content regeneration
    """
    if _is_internal_thn_path(rel_path):
        return "placeholder_ok"

    if _is_probably_file(rel_path):
        return "regen_recommended"

    return "placeholder_ok"


def build_recovery_plan(
    *,
    root: Path,
    snapshot_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Phase 1/2.4 (read-only):
      - Load manifest expected_paths
      - Detect which expected paths are missing on disk
      - Attach best-effort snapshot metadata (index-based or legacy)
      - Produce a deterministic plan that can later be executed

    No filesystem writes occur here.
    """
    scaffold_root = root.resolve()
    manifest = _load_manifest(scaffold_root)

    expected_raw = manifest.get("expected_paths", [])
    expected = _normalize_expected_paths(expected_paths=expected_raw, root=scaffold_root)

    missing: List[str] = []
    for rel in expected:
        if not _abs_target(scaffold_root, rel).exists():
            missing.append(rel)
    missing = sorted(missing)

    snap = _pick_snapshot(scaffold_root, snapshot_id)

    blueprint = manifest.get("blueprint", {})
    blueprint_id = ""
    blueprint_version = ""
    if isinstance(blueprint, dict):
        blueprint_id = str(blueprint.get("id") or "")
        blueprint_version = str(blueprint.get("version") or "")

    actions: List[Dict[str, Any]] = []
    for rel in missing:
        abs_path = _abs_target(scaffold_root, rel)
        op = "touch" if _is_probably_file(rel) else "mkdir"
        semantics = _semantics_for_missing_path(rel_path=rel)

        action: Dict[str, Any] = {
            "op": op,
            "path": rel,
            "abs_path": str(abs_path),
            "reason": "expected_but_missing",
            "recovery_semantics": semantics,
            "phase1_note": (
                "Planner result. Apply currently restores structural compliance only (touch/mkdir). "
                "If recovery_semantics is regen_recommended, a future opt-in phase may regenerate "
                "blueprint-owned file contents."
            ),
        }

        if semantics == "regen_recommended":
            action["regen_hint"] = {
                "kind": "blueprint_owned_file",
                "blueprint_id": blueprint_id,
                "blueprint_version": blueprint_version,
                "suggested_future_op": "regen",
            }

        actions.append(action)

    notes: List[Dict[str, str]] = []
    for rel in missing:
        notes.append(
            {
                "code": "RECOVERABLE_MISSING",
                "path": rel,
                "message": f"{rel} expected but missing; included in recovery plan",
            }
        )

    if isinstance(snapshot_id, str) and snapshot_id.strip():
        requested = snapshot_id.strip()
        if snap.kind in ("index", "legacy") and snap.snapshot_id == requested and snap.path is None:
            notes.append(
                {
                    "code": "SNAPSHOT_NOT_FOUND",
                    "path": "",
                    "message": f"Requested snapshot_id not found: {requested} (kind={snap.kind})",
                }
            )

    schema_version = int(manifest.get("schema_version", 1) or 1)

    return {
        "status": "plan_ready" if actions else "nothing_to_recover",
        "path": str(scaffold_root),
        "blueprint": blueprint if isinstance(blueprint, dict) else {},
        "schema_version": schema_version,
        "snapshot": {
            "kind": snap.kind,
            "snapshot_id": snap.snapshot_id,
            "path": str(snap.path) if snap.path else "",
            "payload_present": bool(snap.payload),
        },
        "missing": missing,
        "actions": actions,
        "notes": notes,
    }
