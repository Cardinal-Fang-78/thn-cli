# thn_cli/plugins/__init__.py
"""
THN Plugin System (Hybrid-Standard)

Exports the stable plugin loader API.
"""

from .plugin_loader import (
    load_registry,
    save_registry,
    list_plugins,
    load_plugin,
)
