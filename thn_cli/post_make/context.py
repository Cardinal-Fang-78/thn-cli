from __future__ import annotations

"""
Post-Make Context Object (Hybrid-Standard)
=========================================

RESPONSIBILITIES
----------------
This module defines the **immutable context container** passed to all
post-make verification, inspection, and hook logic.

It is responsible for:
    • Capturing authoritative metadata about a completed `make` operation
    • Providing a stable, explicit interface for post-make hooks
    • Acting as the single shared context object across:
          - post_make.runner
          - post_make.accept
          - post_make.verifier
          - post_make.hooks
          - snapshot / audit tooling

This object is intentionally **small, explicit, and frozen**.

CONTRACT STATUS
---------------
⚠️ STABLE DATA CONTRACT — ADDITIVE CHANGES ONLY

This class is consumed by:
    • Internal post-make logic
    • Optional third-party or tenant hooks
    • Future GUI / audit surfaces

Rules:
    • Fields must not be removed or renamed
    • New fields may be added only if optional
    • Defaults must preserve backward compatibility
    • Immutability must be preserved

NON-GOALS
---------
• This module does NOT perform validation
• This module does NOT execute hooks
• This module does NOT mutate filesystem state
• This module does NOT load policy

All behavior belongs in runner, verifier, or hook modules.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .policy import AcceptancePolicy


@dataclass(frozen=True)
class PostMakeContext:
    """
    Immutable context passed to post-make hooks and verifiers.

    Keep this class minimal and explicit.
    If new data is required, add optional fields only.
    """

    # ------------------------------------------------------------------
    # Invocation identity
    # ------------------------------------------------------------------

    command: str  # e.g., "make module"
    project: str  # e.g., "DemoProj"
    target_kind: str  # e.g., "project" | "module"
    target_name: str  # e.g., "core"
    blueprint_id: str  # e.g., "module_default"

    # ------------------------------------------------------------------
    # Paths & outputs
    # ------------------------------------------------------------------

    # Single source of truth for THN filesystem roots.
    # Must originate from get_thn_paths().
    thn_paths: Dict[str, str]

    # Concrete filesystem path created or modified by make.
    output_path: str

    # ------------------------------------------------------------------
    # Registry & blueprint resolution
    # ------------------------------------------------------------------

    # Registry record written or updated by make.
    registry_record: Dict[str, Any] = field(default_factory=dict)

    # Resolved blueprint variables (useful for audit / diagnostics).
    vars_resolved: Dict[str, Any] = field(default_factory=dict)

    # Structured result payload returned by the make engine, if any.
    make_result: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Acceptance policy (optional, inert by default)
    # ------------------------------------------------------------------

    acceptance_policy: Optional[AcceptancePolicy] = None
