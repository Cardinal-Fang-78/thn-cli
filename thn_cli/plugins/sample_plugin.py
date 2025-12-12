"""
Sample Plugin (Hybrid-Standard)
-------------------------------

This plugin demonstrates the minimal required interface for THN CLI plugins.

Contract:
    • PLUGIN_NAME: str
    • PLUGIN_DESCRIPTION: str
    • register(): Optional[dict]

The `register()` function may return metadata that is merged into
the plugin registry during introspection. It must not perform any
side effects (no file writes, no CLI calls, no configuration changes).

This file is safe to keep as-is or modify for custom plugin demos.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Required Public Metadata
# ---------------------------------------------------------------------------

PLUGIN_NAME = "sample_plugin"

PLUGIN_DESCRIPTION = (
    "A reference example plugin for the THN CLI. "
    "Demonstrates the Hybrid-Standard plugin contract."
)


# ---------------------------------------------------------------------------
# Optional: Plugin Metadata
# ---------------------------------------------------------------------------


def register() -> dict:
    """
    Return structured metadata describing this plugin.
    Must be safe, deterministic, side-effect-free.

    All fields are optional, but recommended:
        • version
        • capabilities
        • author
        • notes
    """
    return {
        "version": "1.0.0",
        "capabilities": [
            "demo-introspection",
            "registry-metadata",
        ],
        "author": "THN System",
        "notes": (
            "This plugin does not modify CLI behavior. "
            "It exists only for discoverability and testing."
        ),
    }
