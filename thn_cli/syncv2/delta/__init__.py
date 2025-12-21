"""
Sync V2 CDC-Delta Subsystem (Hybrid-Standard)
--------------------------------------------

RESPONSIBILITIES
----------------
This package defines the **CDC-delta infrastructure layer** for Sync V2.

It provides:
    • Content-addressed chunk storage primitives
    • Delta-manifest handling utilities
    • Foundations for CDC planning, apply, and diagnostics
    • Shared helpers for future remote negotiation

This package is intentionally modular; most logic lives in
submodules and is not executed at import time.

CONTRACT STATUS
---------------
⚠️ INFRASTRUCTURE PACKAGE — SEMANTICS PARTIALLY LOCKED

Public submodules may be consumed by:
    • Sync V2 apply paths
    • Diagnostics and inspection tooling
    • Future GUI and CI integrations

Behavioral guarantees are defined at the **module level**
(e.g., store.py), not by this package initializer.

NON-GOALS
---------
• This package does NOT perform CDC computation at import time
• This package does NOT execute I/O on import
• This package does NOT enforce policy or routing
• This package does NOT imply the presence of optional tooling

Importing this package is always side-effect free.
"""
