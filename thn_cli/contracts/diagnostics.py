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
    """
    Canonical diagnostic categories used across THN.

    Categories are descriptive only and optional.
    Absence of category is the canonical fallback.
    """

    # Core environment & platform
    ENVIRONMENT = "environment"

    # Core subsystems
    REGISTRY = "registry"
    ROUTING = "routing"
    PLUGINS = "plugins"
    TASKS = "tasks"
    UI = "ui"

    # Governance / lifecycle / policy
    GOVERNANCE = "governance"
    HUB = "governance"
    HISTORY = "history"
    CDC = "cdc"

    # Diagnostic aggregators
    SANITY = "sanity"


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


# Contract invariants:
#
# • Diagnostics may emit ONLY categories declared in DiagnosticCategory
# • Category is OPTIONAL metadata
# • Absence of category is the canonical fallback
# • Categories MUST NOT affect exit codes or control flow


@dataclass(frozen=True)
class DiagnosticDescriptor:
    """
    Describes the classification of a diagnostic.

    This structure is intentionally lightweight and immutable.
    """

    category: DiagnosticCategory
    scope: DiagnosticScope
    severity: DiagnosticSeverity
