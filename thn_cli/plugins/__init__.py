# thn_cli/plugins/__init__.py

"""
Plugin subsystem public API for THN CLI.

This module provides a stable facade over the underlying plugin_loader
implementation, including backwards-compatible aliases for older names.
"""

from __future__ import annotations

from .plugin_loader import (
    get_plugin_info,
    list_plugins,
    load_plugin,
    load_plugin_registry,
    save_plugin_registry,
)

# Backwards-compatible aliases (old names used in some legacy code)
load_registry = load_plugin_registry
save_registry = save_plugin_registry

__all__ = [
    "list_plugins",
    "load_plugin",
    "load_plugin_registry",
    "save_plugin_registry",
    "get_plugin_info",
    "load_registry",
    "save_registry",
]
