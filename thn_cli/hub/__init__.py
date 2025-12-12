"""
THN Hub Package

Provides:
    • Hub synchronization helpers (see hub_sync.py)
    • Hub status utilities       (see hub_status.py)
    • Future extension points for:
          - THN Nexus integration
          - Tenant-aware routing
          - Remote HubSync protocol (paired with Sync Delta)

This package exports only the stable public entry points.
Internal helpers remain module-local.
"""

from __future__ import annotations

from .hub_status import get_hub_status
from .hub_sync import sync_hub, sync_hub_from_source

__all__ = [
    "sync_hub",
    "sync_hub_from_source",
    "get_hub_status",
]
