# thn_cli/pathing.py

"""
THN Pathing Subsystem (Hybrid-Standard)

Provides a single authoritative map of filesystem locations used by:

    • Sync V2 (local + remote)
    • Diagnostics
    • Blueprint engine
    • Routing engine
    • Task scheduler
    • UI launcher
    • Plugin system
    • Registry / state

Design goals:
    • All paths are absolute and ensured (directories created on demand).
    • Callers may safely assume that every returned directory exists.
    • Backward-compatible keys are preserved for legacy callers.
"""

from __future__ import annotations

import os
from typing import Dict


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_dir(path: str) -> str:
    """
    Create the directory if missing and return the normalized absolute path.
    """
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def _user_root() -> str:
    """
    Return the THN root within the user's home directory.

    Example:
        C:/Users/<user>/THN
    """
    return os.path.join(os.path.expanduser("~"), "THN")


def _core_cli_root() -> str:
    """
    Determine the installed location of the THN CLI core tree.

    In development:
        C:/THN/core/cli
    In an installed environment:
        <site-packages>/thn_cli/..
    """
    here = os.path.abspath(__file__)          # .../thn_cli/pathing.py
    pkg_root = os.path.dirname(here)          # .../thn_cli
    return os.path.dirname(pkg_root)          # parent of thn_cli


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_thn_paths() -> Dict[str, str]:
    """
    Resolve and return all THN-standard directories.

    The returned dictionary contains ONLY normalized, ensured directories
    (for directories) plus a small number of file paths for known JSON
    state/config files.

    Known keys (directories unless noted otherwise):
        root              → user-level THN root
        base              → alias to root (backward compatible)
        core_cli          → installation root of this CLI project

        projects          → user projects root
        projects_active   → active project tree (routing destinations)

        sync_root         → Sync subsystem root
        sync_extract      → temporary extract area for envelopes
        sync_status_db    → directory for Sync status DB files

        delta_root        → CDC-delta root
        delta_chunks      → chunk store root
        delta_cache       → snapshot/cache state

        routing_root      → routing JSON + classifier configs
        routing_rules     → routing_rules.json path (file)

        blueprints_root   → user-level blueprint root
        plugins_root      → user-level plugin root
        hub_root          → Hub-related local state
        tasks_root        → task registry root
        ui_root           → UI-related state

        state_root        → generic state/registry root
        registry_file     → main registry JSON path (file)
    """
    root = _user_root()
    core_cli = _core_cli_root()

    # Directories
    dir_map = {
        # Global user root
        "root": root,
        "base": root,  # backward-compatible alias

        # Development / installation root of this CLI
        "core_cli": core_cli,

        # Projects
        "projects":        os.path.join(root, "projects"),
        "projects_active": os.path.join(root, "projects", "active"),

        # Sync V2 (local)
        "sync_root":      os.path.join(root, "sync"),
        "sync_extract":   os.path.join(root, "sync", "extract"),
        "sync_status_db": os.path.join(root, "sync", "status_db"),

        # Delta / CDC store
        "delta_root":   os.path.join(root, "delta"),
        "delta_chunks": os.path.join(root, "delta", "chunks"),
        "delta_cache":  os.path.join(root, "delta", "cache"),

        # Routing
        "routing_root": os.path.join(root, "routing"),

        # Blueprints (user editable)
        "blueprints_root": os.path.join(root, "blueprints"),

        # Plugins
        "plugins_root": os.path.join(root, "plugins"),

        # Hub
        "hub_root": os.path.join(root, "hub"),

        # Tasks
        "tasks_root": os.path.join(root, "tasks"),

        # UI
        "ui_root": os.path.join(root, "ui"),

        # Generic state/registry
        "state_root": os.path.join(root, "state"),
    }

    # Ensure all directories exist
    ensured_dirs = {key: _ensure_dir(path) for key, path in dir_map.items()}

    # File paths that are not auto-created as dirs
    file_map = {
        # Routing rules file (used by thn_cli.routing.rules)
        "routing_rules": os.path.join(ensured_dirs["routing_root"], "routing_rules.json"),

        # Registry file (used by thn_cli.registry)
        "registry_file": os.path.join(ensured_dirs["state_root"], "registry.json"),
    }

    paths: Dict[str, str] = {}
    paths.update(ensured_dirs)
    paths.update(file_map)

    return paths
