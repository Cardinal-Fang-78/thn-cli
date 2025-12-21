"""
THN Snapshot Utilities (Hybrid-Standard)
========================================

This package provides **read-only snapshot utilities** used for
structural comparison, drift diagnostics, and historical inspection.

RESPONSIBILITIES
----------------
This package is responsible for:
    • Snapshot structural comparison (diffing)
    • Deterministic change analysis
    • Translation of snapshot diffs into drift-compatible operations
    • Supporting historical inspection and tooling

This package is used by:
    • drift history views
    • diagnostic commands
    • migration analysis
    • future replay and recovery tooling

CONTRACT STATUS
---------------
⚠️ DIAGNOSTIC & HISTORICAL — NON-AUTHORITATIVE

This package:
    • MUST NOT mutate snapshots
    • MUST NOT write filesystem state
    • MUST NOT enforce policy
    • MUST NOT apply changes

Snapshot creation, acceptance, and enforcement are handled elsewhere.

AUTHORITATIVE BOUNDARIES
------------------------
Authoritative snapshot lifecycle management occurs in:
    • post_make.snapshot
    • drift accept / migrate logic
    • recovery and apply engines

This package exists solely to **observe and compare** snapshot state.

NON-GOALS
---------
• This package does NOT apply diffs
• This package does NOT infer intent
• This package does NOT guarantee correctness
• This package does NOT manage persistence

Future expansion MAY include:
    • snapshot replay tooling
    • recovery simulation
    • GUI timeline helpers

Such additions must remain read-only unless explicitly versioned.
"""
