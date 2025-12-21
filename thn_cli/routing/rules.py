# thn_cli/routing/rules.py

"""
THN Routing Rules Loader (Hybrid-Standard)
------------------------------------------

RESPONSIBILITIES
----------------
Load, normalize, and expose routing configuration used by the THN
routing engine and diagnostics subsystem.

This module is responsible for:
    • Loading routing_rules.json from disk
    • Providing safe defaults when files are missing or invalid
    • Normalizing rule structure for engine consumption
    • Returning a merged routing configuration bundle

RETURN CONTRACT
---------------
load_routing_rules() ALWAYS returns a dict of the form:

    {
        "rules": {
            "tag_patterns": {...},
            "project_mappings": {...},
            "default_category": <str>,
            "default_subfolder": <str>,
        },
        "classifier": {
            "patterns": {...},
            "weights": {...},
            "minimum_confidence": <float>,
        },
        "schema": {
            "required_keys": [...],
        }
    }

AUTHORITY BOUNDARY
------------------
This module:
    • Does NOT perform routing
    • Does NOT inspect payloads
    • Does NOT mutate state
    • Does NOT validate destinations

Routing decisions are owned by:
    • thn_cli.routing.engine.auto_route

FUTURE EXPANSION
----------------
Additional routing layers (tenant-aware rules, profile overlays,
or GUI-managed rule sets) may be introduced by extending the returned
structure—never by changing the return shape.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from thn_cli.pathing import get_thn_paths

# ---------------------------------------------------------------------------
# Default Configuration
# ---------------------------------------------------------------------------


_DEFAULT_RULES: Dict[str, Any] = {
    "tag_patterns": {
        # Examples:
        # "assets*": {"category": "assets", "subfolder": "incoming"},
        # "docs*":   {"category": "docs",   "subfolder": "incoming"},
    },
    "project_mappings": {
        # Examples:
        # "project-alpha*": "AlphaProject",
    },
    "default_category": "assets",
    "default_subfolder": "incoming",
}


_DEFAULT_CLASSIFIER: Dict[str, Any] = {
    "patterns": {
        "*.png": "images",
        "*.jpg": "images",
        "*.jpeg": "images",
        "*.md": "docs",
        "*.txt": "docs",
        "*.css": "styles",
    },
    "weights": {
        "images": 0.70,
        "docs": 0.55,
        "styles": 0.60,
    },
    "minimum_confidence": 0.50,
}


_DEFAULT_SCHEMA: Dict[str, Any] = {
    "required_keys": [
        "tag_patterns",
        "project_mappings",
        "default_category",
        "default_subfolder",
    ]
}


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _rules_path(paths: Dict[str, str]) -> str:
    """Return absolute path to routing_rules.json."""
    return paths["routing_rules"]


def _safe_load_json(path: str) -> Dict[str, Any]:
    """Load JSON from disk, returning an empty dict on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _merge_defaults(user: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Shallow-merge user config over defaults without mutation.
    """
    merged = defaults.copy()
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            tmp = merged[k].copy()
            tmp.update(v)
            merged[k] = tmp
        else:
            merged[k] = v
    return merged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_routing_rules() -> Dict[str, Any]:
    """
    Load and normalize routing configuration.

    Behavior:
        • Missing file → defaults
        • Invalid JSON → defaults
        • Partial config → merged with defaults

    This function NEVER raises.
    """
    paths = get_thn_paths()
    rules_path = _rules_path(paths)

    raw: Dict[str, Any] = {}
    if os.path.exists(rules_path):
        raw = _safe_load_json(rules_path)

    rules = _merge_defaults(raw.get("rules", {}), _DEFAULT_RULES)
    classifier = _merge_defaults(raw.get("classifier", {}), _DEFAULT_CLASSIFIER)
    schema = _merge_defaults(raw.get("schema", {}), _DEFAULT_SCHEMA)

    return {
        "rules": rules,
        "classifier": classifier,
        "schema": schema,
    }
