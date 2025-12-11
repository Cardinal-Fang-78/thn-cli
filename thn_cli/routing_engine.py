# thn_cli/routing_engine.py
"""
THN Routing Engine (Legacy Shim, Hybrid-Standard)
-------------------------------------------------

This module exists purely for backward compatibility.

Historical usage:
    from thn_cli.routing_engine import auto_route

Current implementation:
    Delegates directly to thn_cli.routing.engine.auto_route

If you are writing new code, prefer:
    from thn_cli.routing.engine import auto_route
"""

from __future__ import annotations

from thn_cli.routing.engine import auto_route

__all__ = ["auto_route"]
