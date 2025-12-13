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

    Notes:
        • Web bundles may include:
              - HTML, JS, CSS
              - Fonts, SVG, images
              - Precompiled SPA/React output
              - Static JSON catalogs / indices
        • postcheck eventually validates:
              - required entrypoints (index.html or main SPA bundle)
              - asset directories
              - integrity of critical resources
    """

    name = "web"

    # Destination for extracted/assembled web assets
    destination_path = r"C:\THN\sync\web" if os.name == "nt" else "/opt/thn/sync/web"

    # Dedicated backup root
    backup_root = r"C:\THN\sync\backups\web" if os.name == "nt" else "/opt/thn/sync/backups\web"

    # --------------------------------------------------------------
    # Pre / Post Validation Hooks
    # --------------------------------------------------------------

    def precheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate environment and prepare folders before apply.

        Hybrid-Standard guarantees:
            • The directory is created if missing.
            • Applies may safely overwrite assets.
        """
        try:
            os.makedirs(self.destination_path, exist_ok=True)
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"Unable to prepare web destination: {exc}",
            }

        return {"ok": True, "reason": None}

    def postcheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the deployed web bundle after apply.

        Future expansions:
            • Ensure index.html exists for SPA.
            • Validate presence of hashed assets.
            • Confirm that the bundle's “entrypoints” file loads.
        """
        if not os.path.isdir(self.destination_path):
            return {
                "ok": False,
                "reason": "Web destination directory missing after apply",
            }

        # Additional Stage 3 validations will be added here.
        return {"ok": True, "reason": None}
