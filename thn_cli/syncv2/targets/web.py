"""
THN Sync V2 – Web Target (Hybrid-Standard)
=========================================

Defines the SyncTarget for THN Web asset bundles.

Responsibilities:
    • Provide a consistent destination and backup root for all web assets.
    • Validate before/after apply to prevent corrupt web deployments.
    • Support raw-zip and CDC-delta envelopes.
    • Prepare for Stage 3:
          - chunk-aware HTML rebuilds
          - asset fingerprinting
          - SPA bundle verification
"""

from __future__ import annotations

import os
from typing import Any, Dict

from .base import SyncTarget


class WebSyncTarget(SyncTarget):
    """
    Sync target for THN Web UI assets.
    """

    name = "web"

    destination_path = r"C:\THN\sync\web" if os.name == "nt" else "/opt/thn/sync/web"
    backup_root = r"C:\THN\sync\backups\web" if os.name == "nt" else "/opt/thn/sync/backups/web"

    def precheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        try:
            os.makedirs(self.destination_path, exist_ok=True)
        except Exception as exc:
            return {"ok": False, "reason": f"Unable to prepare web destination: {exc}"}

        return {"ok": True, "reason": None}

    def postcheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        if not os.path.isdir(self.destination_path):
            return {"ok": False, "reason": "Web destination directory missing after apply"}

        return {"ok": True, "reason": None}
