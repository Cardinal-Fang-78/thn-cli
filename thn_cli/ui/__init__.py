"""
THN UI Subsystem
----------------

This package exposes UI-facing entry points for THN.

Stability tiers:

LOCKED (GUI contract):
    - get_unified_history
        Read-only, shape-stable, policy-agnostic API.
        This surface must not change without versioning.

EVOLVING (UI scaffolding):
    - launch_ui
    - get_ui_status
        Placeholder and bootstrap helpers for future GUI shells.
        These APIs may evolve as the UI matures.

Rules:
    - No business logic
    - No policy enforcement
    - No rendering
    - No mutation of core data
"""

from .history_api import get_unified_history
from .ui_api import get_ui_status
from .ui_launcher import launch_ui

__all__ = [
    "get_unified_history",  # LOCKED GUI contract
    "get_ui_status",  # evolving UI scaffold
    "launch_ui",  # evolving UI scaffold
]
