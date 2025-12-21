from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from .accept import accept_drift
from .context import PostMakeContext
from .errors import PostMakeError
from .verifier import verify_make_output

HookFn = Callable[[PostMakeContext], None]


@dataclass(frozen=True)
class Hook:
    name: str
    fn: HookFn
    critical: bool = True  # critical hooks fail the overall post-make if they raise


# ---------------------------------------------------------------------------
# Hook implementations
# ---------------------------------------------------------------------------


def _verify_and_maybe_accept(ctx: PostMakeContext) -> None:
    """
    Verify scaffold output.

    If verification fails due to drift:
      - Apply acceptance policy if present
      - Accept drift deterministically
      - Re-run verification
    """
    try:
        verify_make_output(ctx)
        return
    except Exception as exc:
        # No policy => strict behavior (original semantics)
        if ctx.acceptance_policy is None:
            raise

        # Attempt policy-governed acceptance
        try:
            accept_drift(
                root=ctx.output_path,
                policy=ctx.acceptance_policy,
                note=f"post-make auto-accept ({ctx.command})",
            )
        except Exception:
            # Acceptance failed or blocked by policy
            raise

        # Re-verify after acceptance (must pass)
        verify_make_output(ctx)


# ---------------------------------------------------------------------------
# Default hook chain
# ---------------------------------------------------------------------------


def default_hooks() -> List[Hook]:
    """
    The default post-make hook chain.

    Verification is authoritative.
    Acceptance is only applied when an explicit policy exists.
    """
    return [
        Hook(
            name="verify_make_output",
            fn=_verify_and_maybe_accept,
            critical=True,
        ),
    ]
