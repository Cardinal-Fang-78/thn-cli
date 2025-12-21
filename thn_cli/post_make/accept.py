from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from thn_cli.contracts.errors import SYSTEM_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.presentation.replay import compute_replay_tree
from thn_cli.scaffolds.drift_preview import preview_scaffold_drift
from thn_cli.snapshots.snapshot_store import (
    default_snapshot_root,
    next_snapshot_id,
    save_index,
    write_snapshot,
)

from .errors import PostMakeVerificationError
from .policy import AcceptancePolicy
from .snapshot import extract_rules, snapshot_expected_paths

MANIFEST_NAME = ".thn-tree.json"
SUPPORTED_SCHEMA_VERSIONS = {2}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_manifest(root: Path) -> Dict:
    manifest = root / MANIFEST_NAME
    if not manifest.exists():
        raise PostMakeVerificationError(f"accept drift failed: missing {MANIFEST_NAME}")

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        raise PostMakeVerificationError(f"accept drift failed: invalid JSON in {MANIFEST_NAME}")

    if not isinstance(data, dict):
        raise PostMakeVerificationError("accept drift failed: manifest must be a JSON object")

    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise PostMakeVerificationError(
            "accept drift failed: unsupported schema_version "
            f"{schema_version}. Supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )

    return data


def accept_drift(
    *,
    root: Path,
    note: Optional[str] = None,
    policy: Optional[AcceptancePolicy] = None,
) -> Dict:
    """
    Accept current filesystem state as the new expected scaffold state.

    Authoritative mutation:
      - Policy validation (tenant-safe seam)
      - Canonical filesystem snapshot
      - Immutable snapshot write
      - Replay verification
      - Manifest update (enriched for drift history)
    """
    data = _load_manifest(root)

    # ------------------------------------------------------------------
    # Policy enforcement (read-only, deterministic)
    # ------------------------------------------------------------------
    preview = preview_scaffold_drift(root)

    active_policy = policy or AcceptancePolicy()
    violations: List[str] = active_policy.validate(preview)

    if violations:
        raise PostMakeVerificationError(
            "accept drift blocked by policy:\n" + "\n".join(f"- {v}" for v in violations)
        )

    # ------------------------------------------------------------------
    # Canonical snapshot computation
    # ------------------------------------------------------------------
    rules = extract_rules(data.get("rules"))
    tree = snapshot_expected_paths(root=root, rules=rules)

    snapshot_root = default_snapshot_root(root)
    snapshot_id, new_index = next_snapshot_id(snapshot_root)

    accepted_at = _utc_now_iso()

    snapshot_payload = {
        "schema_version": 1,
        "id": snapshot_id,
        "tree": tree,
        "reason": "accept-drift",
        "note": note,
        "accepted_at": accepted_at,
    }

    # ------------------------------------------------------------------
    # Immutable snapshot write (primary authority)
    # ------------------------------------------------------------------
    write_snapshot(snapshot_root, snapshot_id, snapshot_payload)
    save_index(snapshot_root, new_index)

    # ------------------------------------------------------------------
    # Replay verification (safety gate)
    # ------------------------------------------------------------------
    try:
        replayed = compute_replay_tree(
            snapshot={"tree": tree},
            diff={"added": [{"path": p} for p in tree], "removed": []},
        )
    except Exception as exc:
        raise CommandError(
            SYSTEM_CONTRACT,
            "accept drift failed: replay verification error",
        ) from exc

    if sorted(replayed) != sorted(tree):
        raise CommandError(
            SYSTEM_CONTRACT,
            "accept drift failed: replay tree mismatch",
        )

    # ------------------------------------------------------------------
    # Manifest update (secondary authority, enriched)
    # ------------------------------------------------------------------
    new_data = dict(data)
    new_data["expected_paths"] = tree
    new_data["accepted"] = {
        "at": accepted_at,
        "snapshot_id": snapshot_id,
        "note": note,
        "policy": {
            "allow_unexpected": active_policy.allow_unexpected,
            "allow_owned_sub_scaffold": active_policy.allow_owned_sub_scaffold,
            "allow_missing_required": active_policy.allow_missing_required,
        },
        "summary": {
            "notes_count": len(preview.get("notes", [])),
            "path_count": len(tree),
        },
    }

    tmp = root / (MANIFEST_NAME + ".tmp")
    tmp.write_text(json.dumps(new_data, indent=2), encoding="utf-8")
    tmp.replace(root / MANIFEST_NAME)

    return {
        "path": str(root),
        "snapshot_id": snapshot_id,
        "accepted_at": accepted_at,
        "path_count": len(tree),
    }
