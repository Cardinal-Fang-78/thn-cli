"""
THN CLI Package Initialization (Hybrid-Standard)

This module defines:
    • Package-level metadata (version, name, feature flags)
    • Safe, side-effect-free initialization
    • Minimal diagnostics for verbose mode

It does NOT:
    • Allocate resources
    • Perform filesystem writes
    • Load plugins or commands
    • Modify environment variables

All heavy initialization is delayed until invoked by:
    - thn_cli.__main__.main()
    - specific subsystems (syncv2, routing, tasks, ui, hub, plugins)
"""

from __future__ import annotations

import os
from typing import Dict

# ---------------------------------------------------------------------------
# Version (exported for PyPI packaging)
# ---------------------------------------------------------------------------

# NOTE:
# This must always match the version you intend to publish.
# GitHub workflows or manual PyPI releases rely on this field.
__version__ = "2.0.0"


# ---------------------------------------------------------------------------
# Package Metadata
# ---------------------------------------------------------------------------

THN_CLI_VERSION: str = __version__
THN_CLI_NAME: str = "THN Master Control / THN CLI"

# Feature flags for advanced systems (future-safe)
FEATURES: Dict[str, bool] = {
    "sync_v2": True,
    "routing_engine": True,
    "blueprint_engine": True,
    "task_scheduler": True,
    "ui_bridge": True,
    "plugin_system": True,
    "delta_sync": True,
}


# ---------------------------------------------------------------------------
# Verbose Diagnostics (opts-in with THN_CLI_VERBOSE=1)
# ---------------------------------------------------------------------------

_VERBOSE = bool(os.environ.get("THN_CLI_VERBOSE", "").strip())


def _log(msg: str) -> None:
    if _VERBOSE:
        print(f"[thn-cli:init] {msg}")


_log(f"Package loaded: {THN_CLI_NAME} v{THN_CLI_VERSION}")
_log(f"Features enabled: {', '.join([k for k, v in FEATURES.items() if v])}")


# ---------------------------------------------------------------------------
# Public Re-Exports (lightweight only)
# ---------------------------------------------------------------------------

__all__ = [
    "__version__",
    "THN_CLI_VERSION",
    "THN_CLI_NAME",
    "FEATURES",
]
