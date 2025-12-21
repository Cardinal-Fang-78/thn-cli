from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .policy import AcceptancePolicy


def _load_rules_file(project_root: Path) -> Dict[str, Any]:
    rules_path = project_root / ".thn-rules.json"
    if not rules_path.exists():
        return {}

    try:
        data = json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def load_project_rules(project_root: Path) -> Dict[str, List[str]]:
    """
    Load per-project rule overrides.

    Returns a dict with optional keys:
        - allow_children
        - ignore
    """
    data = _load_rules_file(project_root)

    out: Dict[str, List[str]] = {}

    for key in ("allow_children", "ignore"):
        val = data.get(key)
        if isinstance(val, list):
            out[key] = [str(x) for x in val if isinstance(x, str)]

    return out


def load_project_acceptance_policy(project_root: Path) -> Optional[AcceptancePolicy]:
    """
    Load an optional acceptance policy from .thn-rules.json.

    Expected shape:
      {
        "acceptance_policy": {
          "allow_unexpected": true|false,
          "allow_owned_sub_scaffold": true|false,
          "allow_missing_required": true|false
        }
      }

    Returns:
      - AcceptancePolicy if present and valid
      - None if not present or invalid (inert default behavior)
    """
    data = _load_rules_file(project_root)
    raw = data.get("acceptance_policy")

    if raw is None:
        return None

    if not isinstance(raw, dict):
        return None

    def _bool_or_none(v: Any) -> Optional[bool]:
        return v if isinstance(v, bool) else None

    allow_unexpected = _bool_or_none(raw.get("allow_unexpected"))
    allow_owned = _bool_or_none(raw.get("allow_owned_sub_scaffold"))
    allow_missing = _bool_or_none(raw.get("allow_missing_required"))

    # If the object exists but contains no usable fields, treat as absent.
    if allow_unexpected is None and allow_owned is None and allow_missing is None:
        return None

    return AcceptancePolicy(
        allow_unexpected=True if allow_unexpected is None else allow_unexpected,
        allow_owned_sub_scaffold=True if allow_owned is None else allow_owned,
        allow_missing_required=False if allow_missing is None else allow_missing,
    )


def merge_rules(
    base: Dict[str, List[str]] | None,
    override: Dict[str, List[str]] | None,
) -> Dict[str, List[str]]:
    """
    Merge blueprint rules with project overrides.

    Union-only. Never deletes existing rules.
    """
    merged: Dict[str, List[str]] = {}

    for src in (base or {}, override or {}):
        for key, vals in src.items():
            merged.setdefault(key, [])
            for v in vals:
                if v not in merged[key]:
                    merged[key].append(v)

    return merged
