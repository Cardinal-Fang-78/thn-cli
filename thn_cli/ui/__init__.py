"""
THN UI Subsystem

This package provides the minimal scaffolding for:
- Launching a future THN Desktop UI
- Querying UI status
- Providing an API surface for UI <-> CLI interaction

All functions are currently placeholders designed to be safe and stable.
"""

from .ui_api import get_ui_status
from .ui_launcher import launch_ui
