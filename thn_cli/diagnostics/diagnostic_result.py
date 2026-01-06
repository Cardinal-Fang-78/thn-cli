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
from enum import Enum
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Diagnostic Taxonomy (LOCKED BASELINE)
# ---------------------------------------------------------------------------


class DiagnosticCategory(str, Enum):
    """
    Stable classification for diagnostics.

    Categories are metadata only:
      • Non-enforcing
      • Non-filtering
      • Non-behavioral

    They exist to support audits, tooling, and future presentation layers.
    """

    ENVIRONMENT = "environment"
    FILESYSTEM = "filesystem"
    REGISTRY = "registry"
    ROUTING = "routing"
    PLUGINS = "plugins"
    TASKS = "tasks"
    UI = "ui"
    HUB = "hub"
    SANITY = "sanity"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Diagnostic Result Container
# ---------------------------------------------------------------------------


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

    # Optional, non-enforcing metadata
    category: DiagnosticCategory = DiagnosticCategory.OTHER

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

        category = raw.get("category", DiagnosticCategory.OTHER)
        if not isinstance(category, DiagnosticCategory):
            try:
                category = DiagnosticCategory(str(category))
            except Exception:
                category = DiagnosticCategory.OTHER

        return DiagnosticResult(
            component=raw.get("component", "unknown"),
            ok=bool(raw.get("ok", False)),
            details=raw.get("details", {}) or {},
            errors=list(raw.get("errors", []) or []),
            warnings=list(raw.get("warnings", []) or []),
            category=category,
        )

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def as_dict(self) -> Dict[str, Any]:
        """
        Export as Hybrid-Standard diagnostic dict.

        Category is additive metadata and does not affect existing consumers.
        """
        return {
            "ok": self.ok,
            "component": self.component,
            "details": self.details,
            "errors": self.errors,
            "warnings": self.warnings,
            "category": self.category.value,
        }
