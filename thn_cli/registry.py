"""
THN Registry Subsystem (Hybrid-Standard)
=======================================

RESPONSIBILITIES
----------------
Provides a lightweight, JSON-based persistent registry used for
cross-cutting system state and historical bookkeeping.

This module is responsible for:
    • Loading and saving the global registry.json file
    • Providing a stable in-memory registry structure
    • Validating minimal registry schema integrity
    • Recording append-only event history
    • Surfacing recent events for diagnostics and tooling

The registry is used by:
    • Sync V2 (apply + rollback tracking)
    • Diagnostics suite
    • Blueprint manager
    • Routing and classification metadata
    • Plugin subsystem
    • Future automation and audit tooling

REGISTRY SHAPE (v1)
------------------
{
    "version": 1,
    "projects": { ... },
    "events": [
        {
            "ts": "2025-01-01T12:00:00Z",
            "category": "sync",
            "detail": "...",
            "extra": { ... }
        }
    ]
}

CONTRACT STATUS
---------------
⚠️ SHARED STATE — SEMANTICS STABLE

This module:
    • Is append-friendly but not transactional
    • Is tolerant of missing or corrupted files
    • Must never raise on read-path corruption
    • Must preserve backward compatibility of registry shape

NON-GOALS
---------
• This module does NOT enforce policy
• This module does NOT perform migrations
• This module does NOT validate deep schema correctness
• This module does NOT coordinate locking or concurrency
• This module does NOT act as an authoritative source of truth

The registry is informational and supportive, not controlling.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from .pathing import get_thn_paths

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _registry_path() -> str:
    """
    Return the absolute path to the registry.json file.

    Directory existence is guaranteed via get_thn_paths().
    """
    paths = get_thn_paths()
    return os.path.join(paths["root"], "registry.json")


def _default_registry() -> Dict[str, Any]:
    """
    Return a fully-formed empty registry structure.
    """
    return {
        "version": 1,
        "projects": {},
        "events": [],
    }


# ---------------------------------------------------------------------------
# Public API: Load / Save
# ---------------------------------------------------------------------------


def load_registry(paths: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Load registry.json if present and structurally valid.

    Behavior:
        • Missing file → return default registry
        • Corrupt file → return default registry
        • Invalid shape → return default registry

    This function MUST NOT raise.
    """
    reg_path = _registry_path()

    if not os.path.exists(reg_path):
        return _default_registry()

    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return _default_registry()

        return data

    except Exception:
        return _default_registry()


def save_registry(paths: Dict[str, str] | None, registry: Dict[str, Any]) -> None:
    """
    Serialize registry structure back to JSON.

    This is a write-path and may raise if persistence fails.
    """
    reg_path = _registry_path()

    try:
        with open(reg_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=4)
    except Exception as exc:
        raise RuntimeError(f"Failed to save registry to {reg_path}: {exc}")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_registry(registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform minimal structural validation of the registry.

    This validation is intentionally shallow and non-authoritative.
    """
    missing: List[str] = []

    for key in ("version", "projects", "events"):
        if key not in registry:
            missing.append(key)

    if missing:
        return {
            "valid": False,
            "missing": missing,
            "message": f"Missing required registry keys: {', '.join(missing)}",
        }

    if not isinstance(registry.get("events"), list):
        return {
            "valid": False,
            "missing": ["events"],
            "message": "Registry 'events' must be a list.",
        }

    return {
        "valid": True,
        "missing": [],
        "message": "OK",
    }


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------


def add_registry_event(
    category: str,
    detail: str,
    *,
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    Append a new event into the registry event history.

    Timestamps are stored as ISO-8601 UTC.

    Used by:
        • Sync V2 apply
        • Diagnostics logging
        • Future automation systems
    """
    from datetime import datetime, timezone

    reg = load_registry(None)

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "detail": detail,
        "extra": extra or {},
    }

    reg.setdefault("events", []).append(event)
    save_registry(None, reg)


def get_recent_events(
    registry: Dict[str, Any],
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Return the most recent registry events, newest first.
    """
    events = registry.get("events", [])
    if not isinstance(events, list):
        return []

    return list(reversed(events[-limit:]))
