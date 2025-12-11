"""
THN Plugin Loader (Hybrid-Standard)
-----------------------------------

Responsibilities:
    • Discover plugin modules under thn_cli.plugins.*
    • Load plugin registry (JSON)
    • Enable/disable plugins
    • Provide introspection metadata to CLI tools

Conventions:
    • Each plugin module must expose:
          PLUGIN_NAME: str
          PLUGIN_DESCRIPTION: str
          register(): Optional[dict]
      register() may return metadata to store in the registry.

    • The registry is the authoritative source for enabled/disabled state.
    • All output is normalized for CLI & diagnostic tools.
"""

from __future__ import annotations

import importlib
import json
import os
import pkgutil
from typing import Dict, Any, List, Optional

from thn_cli.pathing import get_thn_paths


# ---------------------------------------------------------------------------
# Registry Helpers
# ---------------------------------------------------------------------------

def _registry_path(paths: Dict[str, str]) -> str:
    return os.path.join(paths["plugins_root"], "plugin_registry.json")


def _load_registry(paths: Dict[str, str]) -> Dict[str, Any]:
    fp = _registry_path(paths)
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {"plugins": {}, "version": 1}


def _save_registry(paths: Dict[str, str], reg: Dict[str, Any]) -> None:
    os.makedirs(paths["plugins_root"], exist_ok=True)
    fp = _registry_path(paths)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=4)


def ensure_registry_seeded() -> None:
    """
    Ensure the registry exists and incorporates all discovered plugins.
    Newly found plugins default to disabled unless they explicitly request enable=true.
    """
    paths = get_thn_paths()
    reg = _load_registry(paths)
    known = reg.setdefault("plugins", {})

    # Discover actual plugin Python modules
    discovered = _discover_plugin_modules()

    for modname in discovered:
        if modname not in known:
            known[modname] = {
                "enabled": False,
                "module": modname,
                "description": "",
                "meta": {},
            }

    _save_registry(paths, reg)


# ---------------------------------------------------------------------------
# Plugin Discovery
# ---------------------------------------------------------------------------

def _discover_plugin_modules() -> List[str]:
    """
    Enumerate all importable plugin modules under thn_cli.plugins.*
    ignoring __init__ and private modules.
    """
    import thn_cli.plugins as pkg

    plugin_list = []
    for info in pkgutil.iter_modules(pkg.__path__):
        name = info.name
        if name.startswith("_"):
            continue
        plugin_list.append(f"thn_cli.plugins.{name}")
    return plugin_list


def _load_plugin_module(fullname: str):
    return importlib.import_module(fullname)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_plugins() -> List[Dict[str, Any]]:
    ensure_registry_seeded()
    paths = get_thn_paths()
    reg = _load_registry(paths)

    results = []

    for name, entry in reg["plugins"].items():
        mod = None
        try:
            mod = _load_plugin_module(entry["module"])
        except Exception:
            pass

        desc = getattr(mod, "PLUGIN_DESCRIPTION", "") if mod else entry.get("description", "")
        meta = getattr(mod, "register", None)
        if callable(meta):
            try:
                merged = meta() or {}
            except Exception:
                merged = {}
        else:
            merged = {}

        results.append({
            "name": name,
            "enabled": entry["enabled"],
            "module": entry["module"],
            "description": desc,
            "meta": merged,
        })

    return results


def get_plugin_info(name: str) -> Optional[Dict[str, Any]]:
    ensure_registry_seeded()
    paths = get_thn_paths()
    reg = _load_registry(paths)

    entry = reg["plugins"].get(name)
    if not entry:
        return None

    # Load module for description + metadata
    try:
        mod = _load_plugin_module(entry["module"])
    except Exception:
        mod = None

    desc = getattr(mod, "PLUGIN_DESCRIPTION", "") if mod else entry.get("description", "")
    meta_fn = getattr(mod, "register", None)
    meta = {}

    if callable(meta_fn):
        try:
            meta = meta_fn() or {}
        except Exception:
            meta = {}

    result = {
        "name": name,
        "enabled": entry["enabled"],
        "module": entry["module"],
        "description": desc,
        "meta": meta,
    }

    return result


def set_plugin_enabled(name: str, enabled: bool) -> bool:
    ensure_registry_seeded()
    paths = get_thn_paths()
    reg = _load_registry(paths)

    if name not in reg["plugins"]:
        return False

    reg["plugins"][name]["enabled"] = bool(enabled)
    _save_registry(paths, reg)
    return True
