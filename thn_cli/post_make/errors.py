from __future__ import annotations

"""
Post-Make Error Contracts (Hybrid-Standard)
===========================================

RESPONSIBILITIES
----------------
Defines the **canonical exception types** used by the post-make subsystem.

These errors represent:
    • Failures during post-make verification
    • Hook execution failures
    • Snapshot, policy, or invariant violations
    • Migration and recovery pre/post conditions

They are intentionally minimal and semantic, allowing higher layers
(CLI, GUI, tests) to handle formatting and reporting consistently.

CONTRACT STATUS
---------------
⚠️ STABLE ERROR SURFACE

Rules:
    • These exception classes must remain lightweight
    • No side effects
    • No embedded formatting or logging
    • Meaning is conveyed by type, not message shape

PostMakeVerificationError MUST be used for:
    • Invariant violations
    • Manifest/schema mismatches
    • Migration or recovery safety failures

NON-GOALS
---------
• This module does NOT perform error rendering
• This module does NOT log or print
• This module does NOT wrap exceptions implicitly

Formatting and user-facing output belong to the CLI layer.
"""


class PostMakeError(RuntimeError):
    """
    Base class for all post-make related errors.

    Raised when a post-make operation fails in a way that
    should abort the current command.
    """

    pass


class PostMakeVerificationError(PostMakeError):
    """
    Raised when post-make verification or safety checks fail.

    Indicates that the filesystem state, manifest, or migration
    result does not satisfy required invariants.
    """

    pass
