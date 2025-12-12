"""
THN Registry Subsystem
----------------------

The registry is a lightweight, JSON-based state store used by:
    • Sync V2 (apply + rollback tracking)
    • Diagnostics suite
    • Blueprint manager
    • Routing + classification metadata
    • Plugin subsystem

This module provides a stable interface for reading, writing,
validating, and extracting recent events from the registry.

Registry file layout:

    {
        "version": 1,
        "projects": { ... },
        "events": [
            {
                "ts": "2025-01-01T12:00:00Z",
                "category": "sync",
                "detail": "...",
                "extra": { ... }
            },
            ...
        ]
    }
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from .pathing import get_thn_paths

# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _registry_path() -> str:
    """
    Return full absolute path to the registry.json file.
    Ensures directory exists.
    """
    paths = get_thn_paths()
    reg_dir = paths["root"]
    path = os.path.join(reg_dir, "registry.json")
    return path


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
    Load registry.json if present and valid.
    If missing or corrupted, return a fresh default registry.
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
    Validate basic structure of the registry.
    """

    missing = []
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
# Event Helpers
# ---------------------------------------------------------------------------


def add_registry_event(
    category: str,
    detail: str,
    *,
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    Append a new event into the registry event history.
    Timestamps are always stored in ISO-8601 UTC.

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
    registry: Dict[str, Any], limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Return the last N registry events, newest first.
    """
    events = registry.get("events", [])
    if not isinstance(events, list):
        return []

    return list(reversed(events[-limit:]))
