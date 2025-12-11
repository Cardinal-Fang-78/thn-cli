"""
THN Sync V2 – Target Base Classes (Hybrid-Standard)
==================================================

This module defines the abstract foundation for all Sync V2 targets.

A SyncTarget provides:
    • name                – unique identifier ("cli", "web", "docs", ...)
    • destination_path    – filesystem root where files are applied
    • backup_root         – optional path for pre-apply backups
    • precheck()          – (optional) validation before apply
    • postcheck()         – (optional) validation after apply

Hybrid-Standard Guarantees:
    • All methods must return structured dictionaries.
    • No method may raise errors for conditions that can be described
      in a structured error object.
    • Engine-level apply() always calls:
           precheck → apply → postcheck
      unless precheck fails, in which case apply/postcheck are skipped.

This base class intentionally contains zero I/O logic and introduces
no filesystem dependencies. Concrete targets supply real paths.
"""

from __future__ import annotations

from abc import ABC
from typing import Dict, Any, Optional


class SyncTarget(ABC):
    """
    Abstract base class for all Sync V2 targets.

    Subclasses override:
        - name (str)
        - destination_path (str)
        - backup_root (str, optional)
        - precheck()
        - postcheck()

    Target Interface (Engine Contract)
    ----------------------------------
    • name: str
        Unique lowercase identifier used in:
            - envelope["manifest"]["target"]
            - remote sync headers
            - state snapshots
            - chunk store partitioning

    • destination_path: str
        Absolute filesystem path to apply files into.
        The apply engine resolves:
            dest_root = os.path.abspath(target.destination_path)

    • backup_root: str
        Directory where pre-apply backups are optionally stored.
        Not used by raw-delta stage; reserved for Stage 3 protection.

    • precheck(envelope) -> dict
        Return:
            { "ok": True }                   → proceed
            { "ok": False, "reason": <str> } → abort apply

    • postcheck(envelope) -> dict
        Same contract as precheck. Called after successful apply.
    """

    # ------------------------------------------------------------------
    # Default target metadata (overridden by subclasses)
    # ------------------------------------------------------------------
    name: str = "base"
    destination_path: str = ""
    backup_root: str = ""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        destination_path: Optional[str] = None,
        backup_root: Optional[str] = None,
    ) -> None:
        """
        Instances may override default paths.
        This allows command-line overrides and test harness injection.

        Example:
            WebSyncTarget(destination_path="C:/override/webroot")
        """
        if destination_path is not None:
            self.destination_path = destination_path
        if backup_root is not None:
            self.backup_root = backup_root

    # ------------------------------------------------------------------
    # Pre-apply validation hook
    # ------------------------------------------------------------------
    def precheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optional validation hook before apply.

        Must return:
            { "ok": True }                           → proceed
            { "ok": False, "reason": "<text>" }      → abort

        Defaults to permitting all operations. Subclasses override
        this to perform filesystem validations, free-space checks,
        or policy-based restrictions.
        """
        return {
            "ok": True,
            "reason": None,
        }

    # ------------------------------------------------------------------
    # Post-apply validation hook
    # ------------------------------------------------------------------
    def postcheck(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optional validation hook executed after a successful apply.

        Typical uses:
            • ensure critical files exist
            • sanity-check version files
            • validate routing metadata
            • run service reload handlers (future Stage 3)

        Must return the same structure as precheck().
        """
        return {
            "ok": True,
            "reason": None,
        }
