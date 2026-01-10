"""
THN Diagnostics Subsystem (Hybrid-Standard)
-------------------------------------------

Provides structured, composable diagnostics for all THN CLI components:

    • Environment validation
    • Registry and plugin checks
    • Routing and pathing diagnostics
    • UI and hub connectivity tests
    • Indentation and formatting verification
    • Aggregate diagnostic suite runner

Each diagnostic returns a DiagnosticResult object that is stable,
JSON-safe, and consistent across all diagnostic modules.
"""

from __future__ import annotations

from .diagnostic_result import DiagnosticResult
from .suite import run_full_suite

__all__ = [
    "DiagnosticResult",
    "run_full_suite",
]
