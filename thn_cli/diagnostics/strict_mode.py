"""
Diagnostic strict-mode activation surface (DX-2.2).

This module defines the *declarative activation interface* for future
diagnostic strict-mode behavior.

DX-2.2 GUARANTEES
-----------------
• No behavior change
• No enforcement
• No branching logic elsewhere
• No exit-code modification
• Safe to import anywhere

This module exists solely to:
• Declare the activation mechanism
• Provide a stable, testable hook
• Avoid future inference or ad-hoc env parsing

All enforcement, downgrade, and escalation behavior is explicitly
deferred to later DX phases.
"""

from __future__ import annotations

import os


def strict_diagnostics_enabled() -> bool:
    """
    Return True if diagnostic strict mode is explicitly enabled.

    Activation mechanism:
        Environment variable only (DX-2.2)

            THN_DIAGNOSTICS_STRICT=1

    IMPORTANT:
        • This function MUST NOT cause side effects
        • Callers MUST NOT enforce behavior in DX-2.2
        • Presence of strict mode does NOT imply failure semantics

    Future DX phases may *observe* this value to opt into
    stricter validation or policy layers.
    """
    return os.getenv("THN_DIAGNOSTICS_STRICT") == "1"
