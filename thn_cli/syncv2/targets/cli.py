"""
THN Sync V2 – CLI Target (Hybrid-Standard)
==========================================

Defines the SyncTarget used for distributing and updating the THN CLI.

Responsibilities:
    • Establish destination and backup roots for CLI deployment.
    • Allow pre/post validation hooks for binary/script updates.
    • Integrate cleanly with:
          - raw-zip envelopes
          - CDC-delta apply
          - remote sync
          - rollback layers (Stage 3)
"""

from __future__ import annotations

import os
from typing import Dict, Any

from .base import SyncTarget


class CLISyncTarget(SyncTarget):
    """
    Sync target for THN CLI assets.

    Hybrid-Standard Rules:
        • Windows and Linux paths must be supported.
        • destination_path and backup_root must be absolute.
        • precheck may validate:
              - enough disk space
              - destination directory exists or can be created
              - version guard (future)
        • postcheck may validate:
              - CLI entrypoint exists
              - permissions/exec bit correct on Linux
              - integrity marker (future)
    """

    name = "cli"

    # Default roots (may be overridden via constructor or env vars)
    destination_path = (
        r"C:\THN\sync\cli"
        if os.name == "nt"
        else "/opt/thn/sync/cli"
    )

    backup_root = (
        r"C:\THN\sync\backups\cli"
        if os.name == "nt"
        else "/opt/thn/sync/backups/cli"
    )

    # --------------------------------------------------------------
    # Optional Target Hooks
    # --------------------------------------------------------------
    def precheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate destination before apply.

        Future expansions:
            • Check disk space
            • Verify no conflicting deployment lock
            • Gate apply based on CLI version constraints
        """
        try:
            os.makedirs(self.destination_path, exist_ok=True)
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"Unable to create destination directory: {exc}",
            }

        return {"ok": True, "reason": None}

    def postcheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate CLI deployment after apply.

        Future expansions:
            • Ensure expected files exist
            • Validate permissions on Unix systems
            • Trigger a 'thn --version' sanity call (optional)
        """
        # Example minimal check: ensure destination directory exists.
        if not os.path.isdir(self.destination_path):
            return {
                "ok": False,
                "reason": "Destination directory missing after apply",
            }

        return {"ok": True, "reason": None}
