"""
THN Routing Configuration Loader (Hybrid-Standard)
=================================================

This module loads, validates, and merges three routing configuration files:

    • routing_rules.json
    • classifier_config.json
    • routing_schema.json

It provides a SINGLE stable API:

    load_routing_config(paths)

which returns a unified and normalized configuration bundle suitable for:

    • routing.engine.auto_route
    • routing.integration.resolve_routing
    • Sync V2 executor/engine
    • blueprint system
    • future Hub routing extensions

This module NEVER performs routing.
That responsibility belongs to:
    thn_cli.routing.engine
    thn_cli.routing.integration
"""

from __future__ import annotations

import json
import os
from typing import Dict, Any

from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------------
# Safe JSON Loader
# ---------------------------------------------------------------------------

def _load_json_or_default(path: str, default: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load JSON if valid; otherwise return default.
    Never throws.
    """
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return default


# ---------------------------------------------------------------------------
# Defaults (Hybrid-Standard Era)
# ---------------------------------------------------------------------------

# These defaults match rules.py (new routing rules format)
_DEFAULT_RULES = {
    "version": 1,
    "tag_routes": {
        "web":  {"target": "web"},
        "cli":  {"target": "cli"},
        "docs": {"target": "docs"},
    },
    "default_target": "web",
}

# Classifier defaults (minimal safe configuration)
_DEFAULT_CLASSIFIER = {
    "filetype_weights": {},
    "minimum_confidence": 0.50,
}

# Schema for validating routing_rules.json
_DEFAULT_SCHEMA = {
    "required_keys": [
        "version",
        "tag_routes",
        "default_target",
    ]
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_rules(rules: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate routing_rules.json against a minimal schema.
    Hybrid-Standard guarantees:
        • Soft validation (never hard-fails routing)
        • Developer diagnostics
        • Future-safe expansion
    """
    required = schema.get("required_keys", [])
    missing = [k for k in required if k not in rules]

    if missing:
        return {
            "valid": False,
            "missing": missing,
            "message": f"Missing required rule keys: {', '.join(missing)}",
        }

    return {
        "valid": True,
        "missing": [],
        "message": "OK",
    }


# ---------------------------------------------------------------------------
# Loader Entry Point
# ---------------------------------------------------------------------------

def load_routing_config(paths: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Load routing rules, classifier config, and schema as a unified structure.

    Returned structure:
        {
            "rules": {...},        # normalized routing rules
            "classifier": {...},   # classifier config
            "schema": {...},       # routing schema
            "valid": bool,         # schema validation status
            "missing": [...],      # missing keys
            "message": "OK" | "...error..."
        }

    Notes:
        • All three components always exist.
        • Corruption or absence → safe defaults.
        • Consumers (engine, executor, tasks, blueprint) never fail due to config.
    """

    if paths is None:
        paths = get_thn_paths()

    routing_root = paths["routing_root"]

    rules_path = os.path.join(routing_root, "routing_rules.json")
    classifier_path = os.path.join(routing_root, "classifier_config.json")
    schema_path = os.path.join(routing_root, "routing_schema.json")

    # Load or default
    rules = _load_json_or_default(rules_path, _DEFAULT_RULES)
    classifier = _load_json_or_default(classifier_path, _DEFAULT_CLASSIFIER)
    schema = _load_json_or_default(schema_path, _DEFAULT_SCHEMA)

    # Validate rules
    validation = _validate_rules(rules, schema)

    # Normalize missing fields (guarantee compatibility)
    rules.setdefault("version", 1)
    rules.setdefault("tag_routes", _DEFAULT_RULES["tag_routes"].copy())
    rules.setdefault("default_target", _DEFAULT_RULES["default_target"])

    classifier.setdefault("filetype_weights", {})
    classifier.setdefault("minimum_confidence", 0.50)

    result = {
        "rules": rules,
        "classifier": classifier,
        "schema": schema,
        "valid": validation["valid"],
        "missing": validation["missing"],
        "message": validation["message"],
    }

    return result
