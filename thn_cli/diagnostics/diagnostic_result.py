"""
THN Diagnostic Result Model
---------------------------

Provides a unified, stable container for all diagnostic output.

Every diagnostic module should return a dict that follows this schema:

    {
        "ok": bool,
        "component": "<name>",
        "details": { ... },
        "errors": [ ... ],
        "warnings": [ ... ]
    }

This wrapper class enforces structure, normalizes fields, and guarantees
Hybrid-Standard compatibility for all consumers (suite, UI, CLI, logs).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class DiagnosticResult:
    """
    Immutable container for a single diagnostic entry.
    Ensures schema consistency across all modules.
    """

    component: str
    ok: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Normalization Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def from_raw(raw: Dict[str, Any]) -> "DiagnosticResult":
        """
        Build a DiagnosticResult from an arbitrary dict.
        Missing fields are safely normalized.
        """
        if not isinstance(raw, dict):
            raise TypeError("DiagnosticResult.from_raw expects a dict")

        return DiagnosticResult(
            component=raw.get("component", "unknown"),
            ok=bool(raw.get("ok", False)),
            details=raw.get("details", {}) or {},
            errors=list(raw.get("errors", []) or []),
            warnings=list(raw.get("warnings", []) or []),
        )

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def as_dict(self) -> Dict[str, Any]:
        """
        Export as Hybrid-Standard diagnostic dict.
        """
        return {
            "ok": self.ok,
            "component": self.component,
            "details": self.details,
            "errors": self.errors,
            "warnings": self.warnings,
        }
