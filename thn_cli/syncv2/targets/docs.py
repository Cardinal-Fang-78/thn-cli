"""
THN Sync V2 – Docs Target (Hybrid-Standard)
==========================================

Defines the SyncTarget used for distributing and updating documentation assets.

Responsibilities:
    • Establish cross-platform destination and backup roots.
    • Provide pre/post validation for doc-package deployments.
    • Support raw-zip and CDC-delta envelopes.
    • Remain forward-compatible with Snapshot/Delta Stage 3:
          - rollback points
          - doc-index regeneration
          - multi-tenant routing
"""

from __future__ import annotations

import os
from typing import Any, Dict

from .base import SyncTarget


class DocsSyncTarget(SyncTarget):
    """
    Sync target for THN documentation bundles.

    Hybrid-Standard Notes:
        • The docs directory may contain HTML, PDF, Markdown,
          bundle metadata, or generated UI manuals.
        • postcheck is the extension point for:
              - link-map validation
              - doc-index presence
              - optional content hashing
    """

    name = "docs"

    # OS-aware default roots (overridable via constructor)
    destination_path = r"C:\THN\sync\docs" if os.name == "nt" else "/opt/thn/sync/docs"

    backup_root = (
        r"C:\THN\sync\backups\docs" if os.name == "nt" else "/opt/thn/sync/backups/docs"
    )

    # --------------------------------------------------------------
    # Pre / Post Validation Hooks
    # --------------------------------------------------------------

    def precheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure docs destination exists and is writable.
        Future expansion:
            • Validate manifest-level metadata for documentation builds.
            • Confirm docs rebuild pipeline compatibility.
        """
        try:
            os.makedirs(self.destination_path, exist_ok=True)
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"Unable to create docs destination: {exc}",
            }

        return {"ok": True, "reason": None}

    def postcheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate documentation installation after apply.

        Future expansion:
            • Verify presence of index.html or markdown root.
            • Validate integrity of doc bundles.
            • Ensure doc viewer / UI components can bind successfully.
        """
        if not os.path.isdir(self.destination_path):
            return {
                "ok": False,
                "reason": "Docs destination directory missing after apply",
            }

        return {"ok": True, "reason": None}
