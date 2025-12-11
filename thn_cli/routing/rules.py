# thn_cli/routing/rules.py

"""
THN Routing Rules (Hybrid-Standard)

Defines how high-level routing targets are resolved based on tags.

The routing integration layer uses:

    from thn_cli.routing.rules import load_routing_rules

to obtain:

    {
        "version": 1,
        "tag_routes": {
            "web":  {"target": "web"},
            "cli":  {"target": "cli"},
            "docs": {"target": "docs"},
        },
        "default_target": "web",
    }
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------
# Default Rule Set
# ---------------------------------------------------------------------

_DEFAULT_RULES: Dict[str, Any] = {
    "version": 1,
    "tag_routes": {
        "web":  {"target": "web"},
        "cli":  {"target": "cli"},
        "docs": {"target": "docs"},
    },
    "default_target": "web",
}


# ---------------------------------------------------------------------
# Load Rules
# ---------------------------------------------------------------------

def _rules_path(paths: Dict[str, str]) -> str:
    """
    Return absolute path to routing_rules.json.

    Uses the 'routing_rules' file entry in the THN path map.
    """
    return paths["routing_rules"]


def load_routing_rules(paths: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Load routing rules from disk.

    If routing_rules.json does not exist or is invalid, return defaults.
    """
    if paths is None:
        paths = get_thn_paths()

    path = _rules_path(paths)

    if not os.path.exists(path):
        return _DEFAULT_RULES.copy()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _DEFAULT_RULES.copy()

    # Ensure required fields exist
    data.setdefault("version", _DEFAULT_RULES["version"])
    data.setdefault("tag_routes", _DEFAULT_RULES["tag_routes"].copy())
    data.setdefault("default_target", _DEFAULT_RULES["default_target"])

    return data
