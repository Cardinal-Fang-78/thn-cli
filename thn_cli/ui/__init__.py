"""
THN UI Subsystem

This package provides the minimal scaffolding for:
- Launching a future THN Desktop UI
- Querying UI status
- Providing an API surface for UI <-> CLI interaction

All functions are currently placeholders designed to be safe and stable.
"""

from .history_api import get_unified_history
from .ui_api import get_ui_status
from .ui_launcher import launch_ui

__all__ = [
    "get_ui_status",
    "launch_ui",
    "get_unified_history",
]
