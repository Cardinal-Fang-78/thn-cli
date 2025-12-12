"""
Legacy Shim: commands_make_project (Hybrid-Standard)
----------------------------------------------------

Purpose:
    Preserve backward compatibility for THN CLI versions that previously
    referenced this module directly.

Canonical Behavior:
    • Provides *no* commands.
    • Registers *nothing* with argparse.
    • Has *zero* execution side effects.
    • Exists only so older code does not fail on import.
    • Is never used by modern THN CLI routing or command discovery.

Hybrid-Standard Guarantees:
    • Deterministic behavior on import.
    • Safe inert module with predictable metadata.
    • Explicitly non-functional on purpose.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Module Metadata (for diagnostics / module inspection)
# ---------------------------------------------------------------------------

SHIM_INFO = {
    "module": "commands_make_project",
    "type": "legacy_shim",
    "active": False,
    "reason": (
        "Project creation is now handled exclusively by "
        "thn_cli.commands.commands_make. This shim prevents import errors "
        "from older tooling without providing commands."
    ),
    "commands_exposed": [],
}


# ---------------------------------------------------------------------------
# Public API Contract (empty)
# ---------------------------------------------------------------------------


def get_shim_info() -> dict:
    """
    Return structured metadata describing why this module exists.
    Useful for diagnostics or introspection tools.
    """
    return SHIM_INFO


# Explicitly export nothing command-related.
__all__ = ["get_shim_info", "SHIM_INFO"]
