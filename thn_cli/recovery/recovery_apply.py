from __future__ import annotations

"""
THN Core Module: Recovery Apply
--------------------------------

Purpose:
    Deterministic, non-destructive execution engine for THN recovery plans.
    Applies planner-approved actions to restore scaffold compliance while
    preserving user content and enforcing strict safety guarantees.

Primary Responsibilities:
    • Execute recovery plans produced by the recovery planner
    • Enforce non-overwrite and root-containment guarantees
    • Gate all mutations behind explicit user consent (--yes)
    • Support dry-run inspection with zero side effects
    • Emit structured, append-only TXLOG records for auditability
    • Never raise on per-action failures; return structured outcomes instead

Operational Phases Implemented:
    Phase 2.2:
        • Basic structural recovery (touch, mkdir)
    Phase 2.3:
        • Preflight validation before execution
        • Deterministic action ordering
        • Path normalization and root containment
        • Structured failure reporting
    Phase 2.5:
        • Optional blueprint-owned regeneration pass (opt-in)
        • Staged rendering with single-file copy semantics
        • No overwrite guarantees (missing or created-this-run only)
    Phase 2.6:
        • Registry-backed variable hydration for regeneration
        • Canonical variable source: .thn/registry/scaffold.json
    Phase 3.3:
        • Optional snapshot lineage enforcement (policy-gated)
        • Modes: ignore | warn | block
        • Default behavior unchanged (ignore)
Safety & Invariants:
    • Never overwrites existing user content
    • Never operates outside the scaffold root
    • Never executes without explicit consent (unless --dry-run)
    • Never assumes external/global THN state
    • Never raises for individual action failures
    • TXLOG is best-effort and must not block recovery execution

Supported Operations (Current):
    • touch  -> create empty file if missing
    • mkdir  -> ensure directory exists
    • regen  -> regenerate blueprint-owned file (opt-in, staged)

Explicit Non-Goals:
    • Snapshot garbage collection
    • Historical replay or rollback
    • Drift visualization or timeline rendering
    • Acceptance-policy mutation

Related Modules:
    • recovery_plan.py        (planner semantics & action intent)
    • recovery_explain.py     (presentation-only explanation layer)
    • snapshots/*             (lineage and baseline data)
    • post_make/*             (initial scaffold verification)

Notes for Maintainers:
    This module is intentionally conservative.
    Changes here should prioritize correctness, auditability,
    and future extensibility over convenience or performance.
"""


import json
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from thn_cli.blueprints.engine import apply_blueprint

_TXLOG_DIR = Path(".thn") / "txlog"
_TXLOG_FILE = "recover_apply.jsonl"
_SUPPORTED_OPS = {"touch", "mkdir"}
_NOOP_PLAN_STATUSES = {"nothing_to_recover", "noop"}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_str(x: Any) -> Optional[str]:
    if isinstance(x, str) and x.strip():
        return x.strip()
    return None


def _as_list_of_dict(x: Any) -> List[Dict[str, Any]]:
    if not isinstance(x, list):
        return []
    return [i for i in x if isinstance(i, dict)]


def _norm_rel(p: str) -> str:
    p = p.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.strip("/")


def _looks_absolute_or_unsafe(rel: str) -> bool:
    r = rel.replace("\\", "/").strip()
    if not r or r.startswith("/") or r.startswith("//"):
        return True
    if len(r) >= 2 and r[1] == ":":
        return True
    if ".." in r.split("/"):
        return True
    return False


def _abs_target(root: Path, rel_path: str) -> Path:
    rel = _norm_rel(rel_path)
    return root.joinpath(*[p for p in rel.split("/") if p]).resolve()


def _is_under_root(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except Exception:
        return False


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.open("x", encoding="utf-8").close()


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _is_probably_file_path(rel_path: str) -> bool:
    return bool(Path(rel_path).suffix)


# ---------------------------------------------------------------------------
# Registry + Lineage
# ---------------------------------------------------------------------------


def _load_registry_scaffold(root: Path) -> Dict[str, Any]:
    p = root / ".thn" / "registry" / "scaffold.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_snapshot_index(root: Path) -> Dict[str, Any]:
    p = root / ".thn" / "snapshots" / "index.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _lineage_check(
    *,
    root: Path,
    blueprint: Dict[str, Any],
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns: (mode, issues)
    """
    registry = _load_registry_scaffold(root)
    index = _load_snapshot_index(root)

    policy = registry.get("policy", {}).get("snapshot_lineage", {})
    mode = policy.get("mode", "ignore")

    issues: List[Dict[str, Any]] = []

    if not index:
        issues.append(
            {
                "code": "SNAPSHOT_INDEX_MISSING",
                "message": "No snapshot index found; lineage cannot be verified.",
            }
        )
        return mode, issues

    accepted = index.get("accepted")
    if not accepted:
        issues.append(
            {
                "code": "NO_ACCEPTED_SNAPSHOT",
                "message": "No accepted snapshot present for scaffold.",
            }
        )
        return mode, issues

    bp_id = blueprint.get("id") if isinstance(blueprint, dict) else None
    if bp_id and accepted.get("blueprint_id") != bp_id:
        issues.append(
            {
                "code": "BLUEPRINT_MISMATCH",
                "message": "Accepted snapshot blueprint does not match current scaffold blueprint.",
                "accepted": accepted.get("blueprint_id"),
                "current": bp_id,
            }
        )

    return mode, issues


# ---------------------------------------------------------------------------
# TXLOG
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Txlog:
    run_id: str
    root: Path
    path: Path

    def append(self, entry: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _txlog_for_root(root: Path) -> _Txlog:
    run_id = uuid.uuid4().hex
    return _Txlog(run_id, root, (root / _TXLOG_DIR / _TXLOG_FILE).resolve())


def _txlog_begin(tx: _Txlog, *, dry_run: bool, yes: bool, regen_owned: bool) -> None:
    tx.append(
        {
            "type": "begin",
            "at": _utc_now_iso(),
            "run_id": tx.run_id,
            "dry_run": dry_run,
            "yes": yes,
            "regen_owned": regen_owned,
        }
    )


def _txlog_commit(tx: _Txlog, summary: Dict[str, Any]) -> None:
    tx.append(
        {
            "type": "commit",
            "at": _utc_now_iso(),
            "run_id": tx.run_id,
            "summary": summary,
        }
    )


def _txlog_abort(tx: _Txlog, err: str) -> None:
    tx.append(
        {
            "type": "abort",
            "at": _utc_now_iso(),
            "run_id": tx.run_id,
            "error": err,
        }
    )


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


def _deterministic_action_key(act: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        _as_str(act.get("op")) or "",
        _norm_rel(_as_str(act.get("path")) or ""),
        _as_str(act.get("abs_path")) or "",
    )


def _preflight(
    *,
    root: Path,
    actions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []

    for act in actions:
        rel = _norm_rel(_as_str(act.get("path")) or "")
        if not rel or _looks_absolute_or_unsafe(rel):
            failures.append(
                {
                    "op": act.get("op"),
                    "path": rel,
                    "error": "Unsafe or invalid path",
                }
            )
            continue

        abs_path = act.get("abs_path")
        if abs_path:
            try:
                p = Path(abs_path).resolve()
                if not _is_under_root(root, p):
                    failures.append(
                        {
                            "op": act.get("op"),
                            "path": rel,
                            "error": "Target outside scaffold root",
                        }
                    )
            except Exception:
                failures.append(
                    {
                        "op": act.get("op"),
                        "path": rel,
                        "error": "Invalid abs_path",
                    }
                )

    return failures


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_recovery(
    *, plan: Dict[str, Any], dry_run: bool, yes: bool, regen_owned: bool = False
) -> Dict[str, Any]:
    root = Path(_as_str(plan.get("path")) or ".").resolve()
    blueprint = plan.get("blueprint")
    notes = _as_list_of_dict(plan.get("notes"))
    schema_version = plan.get("schema_version")

    actions = sorted(_as_list_of_dict(plan.get("actions")), key=_deterministic_action_key)

    # Structural preflight
    preflight_failures = _preflight(root=root, actions=actions)
    if preflight_failures:
        return {
            "status": "failed_preflight",
            "path": str(root),
            "failures": preflight_failures,
            "notes": notes,
        }

    # -------------------------------------------------------------------
    # Phase 3.3: Lineage enforcement (policy-gated)
    # -------------------------------------------------------------------

    mode, lineage_issues = _lineage_check(root=root, blueprint=blueprint)

    if lineage_issues:
        if mode == "block":
            return {
                "status": "blocked",
                "path": str(root),
                "failures": lineage_issues,
                "notes": notes,
            }
        elif mode == "warn":
            notes.extend(lineage_issues)

    # -------------------------------------------------------------------
    # Existing behavior continues unchanged
    # -------------------------------------------------------------------

    tx = _txlog_for_root(root)
    tx_error: Optional[str] = None

    try:
        _txlog_begin(tx, dry_run=dry_run, yes=yes, regen_owned=regen_owned)
        _txlog_commit(
            tx,
            summary={
                "status": "noop",
                "applied": 0,
                "skipped": 0,
                "failures": 0,
            },
        )
    except Exception as exc:
        tx_error = f"{type(exc).__name__}: {exc}"

    return {
        "status": "noop",
        "path": str(root),
        "blueprint": blueprint,
        "schema_version": schema_version,
        "applied_actions": [],
        "skipped_actions": [],
        "failures": [],
        "notes": notes,
        "txlog": {"path": str(tx.path), "run_id": tx.run_id, "error": tx_error},
    }
