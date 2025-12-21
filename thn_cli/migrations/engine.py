"""
THN Migration Engine (Hybrid-Standard)
-------------------------------------

RESPONSIBILITIES
----------------
This module is the **authoritative execution engine** for scaffold migrations.

It is responsible for:
    • Validating migration preconditions (clean state or forced)
    • Loading and validating the scaffold manifest
    • Applying ordered migration steps from a MigrationPlan
    • Updating blueprint version state atomically
    • Recomputing expected paths after migration
    • Recording migration history entries
    • Capturing authoritative post-migration snapshots

This engine defines the **ground truth semantics** for:
    • thn migrate scaffold
    • Hybrid migration application
    • Migration audit history

CONTRACT STATUS
---------------
⚠️ CRITICAL MUTATION ENGINE — SEMANTICS LOCKED

Changes to this module may:
    • Modify user project files
    • Alter blueprint version lineage
    • Affect snapshot integrity
    • Break migration reproducibility

Any modification MUST be accompanied by:
    • Contract review
    • Migration test updates (where applicable)
    • Clear intent regarding backward compatibility

NON-GOALS
---------
• This module does NOT parse CLI arguments
• This module does NOT format user-facing output
• This module does NOT plan migrations (see MigrationRegistry)
• This module does NOT infer or generate migration specs
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from thn_cli.post_make.errors import PostMakeVerificationError
from thn_cli.post_make.snapshot import extract_rules, snapshot_expected_paths, write_snapshot

from .models import MigrationPlan, MigrationResult
from .ops import op_delete, op_mkdir, op_touch, op_write_json
from .preflight import ensure_clean_or_forced

MANIFEST_NAME = ".thn-tree.json"
SUPPORTED_MANIFEST_SCHEMA = {2}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_manifest(root: Path) -> Dict[str, Any]:
    p = root / MANIFEST_NAME
    if not p.exists():
        raise PostMakeVerificationError(f"migrate failed: missing {MANIFEST_NAME}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        raise PostMakeVerificationError(f"migrate failed: invalid JSON in {MANIFEST_NAME}")

    if not isinstance(data, dict):
        raise PostMakeVerificationError("migrate failed: manifest must be a JSON object")

    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_MANIFEST_SCHEMA:
        raise PostMakeVerificationError(
            f"migrate failed: unsupported manifest schema_version {schema_version}"
        )

    bp = data.get("blueprint")
    if (
        not isinstance(bp, dict)
        or not isinstance(bp.get("id"), str)
        or not isinstance(bp.get("version"), str)
    ):
        raise PostMakeVerificationError("migrate failed: manifest missing blueprint {id, version}")

    return data


def _atomic_write_manifest(root: Path, data: Dict[str, Any]) -> None:
    tmp = root / (MANIFEST_NAME + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(root / MANIFEST_NAME)


def _run_hook(*, root: Path, module: str, context: Dict[str, Any]) -> Dict[str, Any]:
    import importlib

    m = importlib.import_module(module)
    fn = getattr(m, "run", None)
    if fn is None or not callable(fn):
        raise PostMakeVerificationError(
            f"Migration hook '{module}' must expose callable run(*, root, context) -> dict"
        )

    result = fn(root=root, context=context)
    if not isinstance(result, dict):
        raise PostMakeVerificationError(
            f"Migration hook '{module}' returned invalid result (must be dict)"
        )

    return {"op": "hook", "module": module, "result": result}


def _apply_step(*, root: Path, op: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if op == "mkdir":
        return op_mkdir(root=root, rel=str(args.get("path", "")))

    if op == "touch":
        return op_touch(root=root, rel=str(args.get("path", "")))

    if op == "write_json":
        return op_write_json(
            root=root,
            rel=str(args.get("path", "")),
            data=args.get("data"),
        )

    if op == "delete":
        return op_delete(root=root, rel=str(args.get("path", "")))

    if op == "hook":
        return _run_hook(
            root=root,
            module=str(args.get("module", "")),
            context=args.get("context") or {},
        )

    raise PostMakeVerificationError(f"Unknown migration op: {op}")


def migrate_scaffold(
    *,
    root: Path,
    plan: MigrationPlan,
    dry_run: bool = False,
    note: Optional[str] = None,
    force: bool = False,
) -> MigrationResult:
    ensure_clean_or_forced(root=root, force=force)

    manifest = _load_manifest(root)
    bp = manifest["blueprint"]

    if bp["id"] != plan.blueprint_id:
        raise PostMakeVerificationError("migrate failed: blueprint id mismatch")

    if bp["version"] != plan.start.version:
        raise PostMakeVerificationError(
            f"migrate failed: manifest version {bp['version']} != expected {plan.start.version}"
        )

    if plan.start.version == plan.target.version:
        return MigrationResult(
            status="NOOP",
            path=str(root),
            blueprint_id=plan.blueprint_id,
            from_version=plan.start.version,
            to_version=plan.target.version,
            applied=[],
            notes=["Already at target version"],
            dry_run=dry_run,
        )

    applied: List[Dict[str, Any]] = []

    if dry_run:
        return MigrationResult(
            status="OK",
            path=str(root),
            blueprint_id=plan.blueprint_id,
            from_version=plan.start.version,
            to_version=plan.target.version,
            applied=[
                {"spec": f"{s.from_version}->{s.to_version}", "steps": len(s.steps)}
                for s in plan.specs
            ],
            notes=["dry-run only"],
            dry_run=True,
        )

    # --- Apply migration steps ---
    for spec in plan.specs:
        for step in spec.steps:
            applied.append(_apply_step(root=root, op=step.op, args=step.args))

        manifest["blueprint"]["version"] = spec.to_version
        _atomic_write_manifest(root, manifest)

    # --- Recompute expected_paths ---
    rules = extract_rules(manifest.get("rules"))
    expected_paths = snapshot_expected_paths(root=root, rules=rules)
    manifest["expected_paths"] = expected_paths

    # --- Record migration entry ---
    entry = {
        "at": _utc_now_iso(),
        "from": {"id": plan.blueprint_id, "version": plan.start.version},
        "to": {"id": plan.blueprint_id, "version": plan.target.version},
    }
    if note:
        entry["note"] = note

    manifest.setdefault("migrations", []).append(entry)
    _atomic_write_manifest(root, manifest)

    # --- Snapshot capture (authoritative) ---
    write_snapshot(
        root=root,
        expected_paths=expected_paths,
        blueprint=manifest.get("blueprint", {}),
        reason="migrate",
        note=note,
    )

    return MigrationResult(
        status="OK",
        path=str(root),
        blueprint_id=plan.blueprint_id,
        from_version=plan.start.version,
        to_version=plan.target.version,
        applied=applied,
        notes=[],
        dry_run=False,
        expected_count=len(expected_paths),
    )
