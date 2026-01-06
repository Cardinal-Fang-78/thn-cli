# thn_cli/contracts/diagnostics.py
"""
THN Diagnostic Taxonomy (Contract)
=================================

Defines the canonical vocabulary used to describe diagnostics across
the THN CLI surface.

This module establishes shared meaning only. It does not:
  • Emit diagnostics
  • Enforce behavior
  • Affect exit codes
  • Alter runtime semantics

All fields defined here are descriptive, not authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiagnosticCategory(str, Enum):
    GOVERNANCE = "governance"
    ENVIRONMENT = "environment"
    ROUTING = "routing"
    PLUGINS = "plugins"
    UI = "ui"
    SANITY = "sanity"
    CDC = "cdc"
    HISTORY = "history"


class DiagnosticScope(str, Enum):
    CLI = "cli"
    ENGINE = "engine"
    LOADER = "loader"
    TOOLING = "tooling"
    TESTS = "tests"


class DiagnosticSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    NOTICE = "notice"


@dataclass(frozen=True)
class DiagnosticDescriptor:
    """
    Describes the classification of a diagnostic.

    This structure is intentionally lightweight and immutable.
    """

    category: DiagnosticCategory
    scope: DiagnosticScope
    severity: DiagnosticSeverity
