"""
THN Pathing Subsystem (Hybrid-Standard)
--------------------------------------

RESPONSIBILITIES
----------------
This module defines the **single authoritative filesystem path map** for THN.

It is responsible for:
    • Resolving all THN-standard filesystem locations
    • Ensuring required directories exist before use
    • Providing stable, absolute paths for all subsystems
    • Preserving backward-compatible keys for legacy callers

The path map produced here is used by:
    • Sync V2 (local + remote)
    • Routing engine
    • Diagnostics and inspection tooling
    • Blueprint and migration engines
    • Registry and persistent state
    • Task scheduler
    • UI launcher
    • Plugin system

CONTRACT STATUS
---------------
⚠️ CORE INFRASTRUCTURE — SEMANTICS LOCKED

Changes to this module may:
    • Break routing and destination computation
    • Affect Sync apply behavior
    • Alter where user data is stored
    • Break assumptions across CLI, GUI, and CI

Any modification MUST preserve:
    • Absolute, normalized paths
    • Directory auto-creation guarantees
    • Stable key names for existing consumers

NON-GOALS
---------
• This module does NOT perform configuration validation
• This module does NOT read or write registry data
• This module does NOT infer environment-specific behavior
• This module does NOT mutate files (directories only)

All callers must treat returned paths as authoritative.
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
    here = os.path.abspath(__file__)  # .../thn_cli/pathing.py
    pkg_root = os.path.dirname(here)  # .../thn_cli
    return os.path.dirname(pkg_root)  # parent of thn_cli


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_thn_paths() -> Dict[str, str]:
    """
    Resolve and return all THN-standard filesystem paths.

    CONTRACT
    --------
    • All directory paths are absolute
    • All directory paths are ensured to exist
    • File paths are returned but NOT created
    • Returned keys are stable and backward-compatible

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

    # Directory map
    dir_map = {
        # Global user root
        "root": root,
        "base": root,  # backward-compatible alias
        # Development / installation root of this CLI
        "core_cli": core_cli,
        # Projects
        "projects": os.path.join(root, "projects"),
        "projects_active": os.path.join(root, "projects", "active"),
        # Sync V2
        "sync_root": os.path.join(root, "sync"),
        "sync_extract": os.path.join(root, "sync", "extract"),
        "sync_status_db": os.path.join(root, "sync", "status_db"),
        # Delta / CDC
        "delta_root": os.path.join(root, "delta"),
        "delta_chunks": os.path.join(root, "delta", "chunks"),
        "delta_cache": os.path.join(root, "delta", "cache"),
        # Routing
        "routing_root": os.path.join(root, "routing"),
        # Blueprints
        "blueprints_root": os.path.join(root, "blueprints"),
        # Plugins
        "plugins_root": os.path.join(root, "plugins"),
        # Hub
        "hub_root": os.path.join(root, "hub"),
        # Tasks
        "tasks_root": os.path.join(root, "tasks"),
        # UI
        "ui_root": os.path.join(root, "ui"),
        # Generic state
        "state_root": os.path.join(root, "state"),
    }

    # Ensure directories
    ensured_dirs = {k: _ensure_dir(v) for k, v in dir_map.items()}

    # File paths (not auto-created)
    file_map = {
        "routing_rules": os.path.join(ensured_dirs["routing_root"], "routing_rules.json"),
        "registry_file": os.path.join(ensured_dirs["state_root"], "registry.json"),
    }

    paths: Dict[str, str] = {}
    paths.update(ensured_dirs)
    paths.update(file_map)

    return paths
