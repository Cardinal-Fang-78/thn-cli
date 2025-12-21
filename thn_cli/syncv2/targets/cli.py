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

Hybrid-Standard Enforcement:
    • The CLI layer is authoritative over destination selection.
    • Targets MUST NOT guess writable locations.
    • If no explicit destination is provided, a safe temp directory
      MUST be used.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, Optional

from .base import SyncTarget


class CLISyncTarget(SyncTarget):
    """
    Sync target for THN CLI assets.

    Hybrid-Standard Rules:
        • Windows and Linux paths must be supported.
        • destination_path and backup_root must be absolute.
        • Target MUST honor explicitly provided destinations.
        • Target MUST NOT default to system locations implicitly.
    """

    name = "cli"

    def __init__(
        self,
        *,
        dest_root: Optional[str] = None,
        backup_root: Optional[str] = None,
    ) -> None:
        """
        Initialize the CLI sync target.

        Resolution rules (locked):
            1. If dest_root is provided → use it
            2. Else → create a safe, writable temp directory
        """

        if dest_root:
            self.destination_path = os.path.abspath(dest_root)
        else:
            self.destination_path = tempfile.mkdtemp(prefix="thn-sync-apply-")

        if backup_root:
            self.backup_root = os.path.abspath(backup_root)
        else:
            self.backup_root = os.path.join(
                self.destination_path,
                "_backups",
            )

    # --------------------------------------------------------------
    # Optional Target Hooks
    # --------------------------------------------------------------
    def precheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate destination before apply.
        """
        try:
            os.makedirs(self.destination_path, exist_ok=True)
            os.makedirs(self.backup_root, exist_ok=True)
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"Unable to prepare destination paths: {exc}",
            }

        return {"ok": True, "reason": None}

    def postcheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate CLI deployment after apply.
        """
        if not os.path.isdir(self.destination_path):
            return {
                "ok": False,
                "reason": "Destination directory missing after apply",
            }

        return {"ok": True, "reason": None}
