from __future__ import annotations

"""
THN Recover Commands (Hybrid-Standard)

Responsibilities:
    • Expose recovery planning, simulation, explanation, and application
    • Provide read-only diagnostics for scaffold state and lineage
    • Enforce THN root containment for all operations
    • Serve as the primary CLI entrypoint for recovery-related flows

Phase 3.3 upgrades:
    • Add `recover inspect` diagnostics command (read-only)
    • Surface snapshot, registry, and recovery-plan metadata

Phase 3.4 upgrades:
    • Snapshot lineage cross-check (diagnostics only)
    • Compare registry vs latest snapshot blueprint identity
    • Surface soft warnings for mismatch or missing lineage
    • No mutation, no enforcement, no blocking behavior

Phase 3.6 upgrades:
    • Explicitly mark diagnostic-only warnings as non-blocking
    • Add warning metadata fields:
        - severity: "warning"
        - blocking: false
    • Integrate normalized snapshot metadata + metadata warnings
    • Keep output future-proof for:
        - --strict modes
        - GUI colorization
        - CI reporting

Guarantees:
    • Inspect operations are strictly read-only
    • Recovery execution remains explicitly gated
    • Output is deterministic JSON suitable for CLI or GUI
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from thn_cli.contracts.errors import USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.recovery.recovery_apply import apply_recovery
from thn_cli.recovery.recovery_explain import explain_recovery
from thn_cli.recovery.recovery_plan import build_recovery_plan
from thn_cli.recovery.recovery_simulate import simulate_recovery
from thn_cli.snapshots.snapshot_metadata import (
    normalize_snapshot_metadata,
    snapshot_metadata_warnings,
)
from thn_cli.snapshots.snapshot_store import default_snapshot_root, list_snapshots, read_snapshot

# ---------------------------------------------------------------------------
# Utilities / Diagnostics / Provenance
# ---------------------------------------------------------------------------


def _diag_warning(code: str, message: str) -> Dict[str, Any]:
    """Canonical diagnostic-only warning shape (non-blocking)."""
    return {
        "severity": "warning",
        "blocking": False,
        "code": code,
        "message": message,
    }


def _derive_provenance(
    plan: Dict[str, Any],
    registry: Optional[Dict[str, Any]],
    snapshot_present: bool,
) -> List[Dict[str, Any]]:
    """
    Derive per-action provenance information indicating which authoritative
    sources contributed to each recovery decision.
    """
    provenance: List[Dict[str, Any]] = []

    snapshot_info = plan.get("snapshot") or {}
    snapshot_used = snapshot_present and snapshot_info.get("kind") != "none"

    for act in plan.get("actions", []):
        sources: List[str] = ["blueprint"]

        if registry:
            sources.append("registry")

        if snapshot_used:
            sources.append("snapshot")

        provenance.append(
            {
                "path": act.get("path"),
                "sources": sorted(set(sources)),
                "recovery_semantics": act.get("recovery_semantics") or "structural",
            }
        )

    return provenance


def _emit(obj: Dict[str, Any]) -> int:
    print(json.dumps(obj, indent=4))
    return 0


def _ensure_under_thn_root(target_path: Path) -> None:
    paths = get_thn_paths()
    thn_root = paths.get("root", "")
    if isinstance(thn_root, str) and thn_root.strip():
        try:
            target_path.resolve().relative_to(Path(thn_root).resolve())
        except Exception as exc:
            raise CommandError(
                contract=USER_CONTRACT,
                message=f"Target is not under THN root: {target_path} (root={thn_root})",
            ) from exc


def _validate_target(path: Path) -> None:
    if not path.exists():
        raise CommandError(USER_CONTRACT, f"Path does not exist: {path}")
    if not path.is_dir():
        raise CommandError(USER_CONTRACT, f"Path is not a directory: {path}")
    _ensure_under_thn_root(path)


def _load_registry_lineage(root: Path) -> Optional[Dict[str, Any]]:
    reg = root / ".thn" / "registry" / "scaffold.json"
    if not reg.exists():
        return None

    try:
        payload = json.loads(reg.read_text(encoding="utf-8"))
    except Exception:
        return None

    bp = payload.get("blueprint")
    if not isinstance(bp, dict):
        return None

    return {
        "source": "registry",
        "path": str(reg),
        "blueprint": bp,
        "schema_version": payload.get("schema_version"),
    }


def _load_latest_snapshot(root: Path) -> Optional[Dict[str, Any]]:
    snap_root = default_snapshot_root(root)
    if not snap_root.exists():
        return None

    ids = list_snapshots(snap_root)
    if not ids:
        return None

    return read_snapshot(snap_root, sorted(ids)[-1])


def _compare_lineage(
    registry: Optional[Dict[str, Any]],
    snapshot: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compare registry and snapshot lineage and emit diagnostic-only warnings.
    """
    warnings: List[Dict[str, Any]] = []

    if registry and not snapshot:
        warnings.append(
            _diag_warning(
                "SNAPSHOT_MISSING",
                "Registry exists but no snapshots are present for this scaffold.",
            )
        )

    if snapshot and not registry:
        warnings.append(
            _diag_warning(
                "REGISTRY_MISSING",
                "Snapshots exist but registry scaffold.json is missing.",
            )
        )

    if registry and snapshot:
        r_bp = registry.get("blueprint") or {}
        s_bp = snapshot.get("blueprint") or {}

        if r_bp.get("id") != s_bp.get("id"):
            warnings.append(
                _diag_warning(
                    "BLUEPRINT_ID_MISMATCH",
                    f"Registry blueprint id '{r_bp.get('id')}' "
                    f"differs from snapshot blueprint id '{s_bp.get('id')}'.",
                )
            )

        if str(r_bp.get("version")) != str(s_bp.get("version")):
            warnings.append(
                _diag_warning(
                    "BLUEPRINT_VERSION_MISMATCH",
                    f"Registry blueprint version '{r_bp.get('version')}' "
                    f"differs from snapshot blueprint version '{s_bp.get('version')}'.",
                )
            )

    if snapshot:
        normalized_meta = normalize_snapshot_metadata(snapshot)
        warnings.extend(snapshot_metadata_warnings(normalized_meta))

    return warnings


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_recover_plan(args: argparse.Namespace) -> int:
    target = Path(args.path)
    _validate_target(target)
    return _emit(build_recovery_plan(root=target))


def run_recover_simulate(args: argparse.Namespace) -> int:
    target = Path(args.path)
    _validate_target(target)
    plan = build_recovery_plan(root=target)
    return _emit(simulate_recovery(plan=plan))


def run_recover_explain(args: argparse.Namespace) -> int:
    target = Path(args.path)
    _validate_target(target)
    plan = build_recovery_plan(root=target)
    return _emit(explain_recovery(plan=plan, regen_owned=bool(args.regen_owned)))


def run_recover_apply(args: argparse.Namespace) -> int:
    target = Path(args.path)
    _validate_target(target)
    plan = build_recovery_plan(root=target)
    return _emit(
        apply_recovery(
            plan=plan,
            dry_run=bool(args.dry_run),
            yes=bool(args.yes),
            regen_owned=bool(args.regen_owned),
        )
    )


def run_recover_inspect(args: argparse.Namespace) -> int:
    target = Path(args.path)
    _validate_target(target)

    plan = build_recovery_plan(root=target)
    registry = _load_registry_lineage(target)
    snapshot = _load_latest_snapshot(target)

    snap_root = default_snapshot_root(target)
    snap_ids = list_snapshots(snap_root) if snap_root.exists() else []

    normalized_snapshot_meta = normalize_snapshot_metadata(snapshot) if snapshot else None

    lineage_warnings = _compare_lineage(registry, snapshot)
    provenance = _derive_provenance(plan, registry, snapshot_present=bool(snapshot))

    return _emit(
        {
            "status": "inspected",
            "path": str(target.resolve()),
            "blueprint": plan.get("blueprint"),
            "plan_status": plan.get("status"),
            "actions": {
                "total": len(plan.get("actions", [])),
                "regen_candidates": sum(
                    1
                    for a in plan.get("actions", [])
                    if a.get("recovery_semantics") == "regen_recommended"
                ),
            },
            "registry": registry or {"present": False},
            "latest_snapshot": (
                {
                    "id": snapshot.get("id"),
                    "metadata": normalized_snapshot_meta,
                }
                if snapshot
                else {"present": False}
            ),
            "snapshots": {
                "root": str(snap_root),
                "count": len(snap_ids),
                "ids": snap_ids,
            },
            "lineage_warnings": lineage_warnings,
            "provenance": provenance,
            "notes": plan.get("notes", []),
        }
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "recover",
        help="Recovery planning and diagnostics utilities.",
        description="Plan, inspect, and execute scaffold recovery operations.",
    )

    sub = parser.add_subparsers(dest="recover_cmd", required=True)

    sub.add_parser("plan").add_argument("path")
    sub.add_parser("simulate").add_argument("path")

    p_exp = sub.add_parser("explain")
    p_exp.add_argument("path")
    p_exp.add_argument("--regen-owned", action="store_true")

    p_app = sub.add_parser("apply")
    p_app.add_argument("path")
    p_app.add_argument("--dry-run", action="store_true")
    p_app.add_argument("--yes", action="store_true")
    p_app.add_argument("--regen-owned", action="store_true")

    p_ins = sub.add_parser("inspect")
    p_ins.add_argument("path")

    for name, fn in {
        "plan": run_recover_plan,
        "simulate": run_recover_simulate,
        "explain": run_recover_explain,
        "apply": run_recover_apply,
        "inspect": run_recover_inspect,
    }.items():
        sub.choices[name].set_defaults(func=fn)

    parser.set_defaults(func=lambda a: parser.print_help())
