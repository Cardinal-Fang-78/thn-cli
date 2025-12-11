"""
THN Routing Subsystem (Hybrid-Standard)
--------------------------------------

Provides:
    • Declarative routing rules (rules.py)
    • File-type classifier (classifier.py)
    • Routing engine (engine.py)

Used by:
    • THN Sync ingestion
    • Automation routing
    • Incoming envelope classification
"""

from __future__ import annotations

# Public routing API
from .engine import auto_route
from .rules import load_routing_rules
from .classifier import classify_filetype

__all__ = [
    "auto_route",
    "load_routing_rules",
    "classify_filetype",
]
