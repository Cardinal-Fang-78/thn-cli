"""
Plugin Loader (Modernized)
--------------------------

Provides a stable API for:

    • load_plugin_registry()
    • save_plugin_registry()
    • list_plugins()
    • load_plugin(name)
    • enable_plugin(name)
    • disable_plugin(name)

Plugins live in:   thn_cli/plugins/
Registry file:     plugin_registry.json
"""

from __future__ import annotations

import importlib
import json
import os
from typing import Any, Dict, List

REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "plugin_registry.json")


# ---------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------


def load_plugin_registry() -> Dict[str, Any]:
    """Load plugin registry JSON with safe fallback."""
    if not os.path.exists(REGISTRY_FILE):
        return {"plugins": {}}

    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"plugins": {}}


def save_plugin_registry(reg: Dict[str, Any]) -> None:
    """Persist plugin registry."""
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=4)


# ---------------------------------------------------------
# Plugin Listing
# ---------------------------------------------------------


def list_plugins() -> List[Dict[str, Any]]:
    """
    Return a list of plugin entries from the registry, each like:
        { "name": "sample_plugin", "enabled": true }
    """
    reg = load_plugin_registry()
    return [{"name": name, **meta} for name, meta in reg.get("plugins", {}).items()]


# ---------------------------------------------------------
# Load / Enable / Disable Plugins
# ---------------------------------------------------------


def load_plugin(name: str):
    """
    Dynamically import a plugin module:

        thn_cli.plugins.<name>

    Returns the module OR raises ImportError.
    """
    module_name = f"thn_cli.plugins.{name}"
    return importlib.import_module(module_name)


def enable_plugin(name: str) -> bool:
    reg = load_plugin_registry()
    plugins = reg.setdefault("plugins", {})

    if name not in plugins:
        plugins[name] = {"enabled": True}
    else:
        plugins[name]["enabled"] = True

    save_plugin_registry(reg)
    return True


def disable_plugin(name: str) -> bool:
    reg = load_plugin_registry()
    plugins = reg.setdefault("plugins", {})

    if name not in plugins:
        return False

    plugins[name]["enabled"] = False
    save_plugin_registry(reg)
    return True


# ---------------------------------------------------------------------------
# Compatibility Stub: get_plugin_info
# ---------------------------------------------------------------------------


def get_plugin_info(name: str) -> dict:
    """
    Temporary compatibility stub for plugin metadata lookup.

    Returns a minimal dictionary describing the plugin.
    The real plugin metadata system can extend this later.
    """
    registry = load_plugin_registry()

    entry = registry.get(name, {})
    return {
        "name": name,
        "module": entry.get("module", None),
        "active": entry.get("active", False),
        "config": entry.get("config", {}),
    }
