from __future__ import annotations

"""
Post-Make Hook Runner (Hybrid-Standard)
======================================

RESPONSIBILITIES
----------------
This module provides the **authoritative execution loop** for post-make hooks.

It is responsible for:
    • Executing post-make hooks in deterministic order
    • Enforcing critical vs non-critical hook semantics
    • Aggregating non-critical failures
    • Raising structured PostMakeError failures when required

This is the **only module** that should invoke hook functions directly.

CONTRACT STATUS
---------------
⚠️ AUTHORITATIVE CONTROL FLOW — SEMANTICS LOCKED

Behavioral guarantees:
    • Hooks are executed in the order provided
    • Critical hook failure aborts immediately
    • Non-critical failures are collected and reported together
    • No failures are silently swallowed
    • Errors propagate as PostMakeError only

Any change to:
    • failure semantics
    • hook ordering
    • error aggregation behavior

MUST be reviewed for downstream impact on:
    • make commands
    • migration flows
    • recovery / inspection tooling

NON-GOALS
---------
• This module does NOT define hooks
• This module does NOT decide which hooks exist
• This module does NOT perform verification itself
• This module does NOT mutate filesystem state

Hook definitions live in hooks.py.
Verification logic lives in verifier.py and accept.py.
"""

from typing import List

from .context import PostMakeContext
from .errors import PostMakeError
from .hooks import Hook, default_hooks


def run_post_make(ctx: PostMakeContext, hooks: List[Hook] | None = None) -> None:
    """
    Execute post-make hooks for a completed make operation.

    CONTRACT
    --------
    • Hooks run sequentially in deterministic order
    • Critical hook failure aborts immediately
    • Non-critical failures are collected and raised after completion
    • All failures surface as PostMakeError
    """
    hook_list = hooks if hooks is not None else default_hooks()

    noncritical_failures: list[tuple[str, Exception]] = []

    for hook in hook_list:
        try:
            hook.fn(ctx)
        except Exception as exc:
            if hook.critical:
                raise PostMakeError(
                    f"Post-make hook failed (critical): {hook.name}: {exc}"
                ) from exc
            noncritical_failures.append((hook.name, exc))

    if noncritical_failures:
        msg_lines = ["Post-make completed with non-critical failures:"]
        for name, exc in noncritical_failures:
            msg_lines.append(f"- {name}: {exc}")
        raise PostMakeError("\n".join(msg_lines))
