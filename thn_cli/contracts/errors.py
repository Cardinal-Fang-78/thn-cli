# thn_cli/contracts/errors.py
from __future__ import annotations

"""
THN CLI Error Contracts (Hybrid-Standard)
----------------------------------------

RESPONSIBILITIES
----------------
This module defines the **canonical error taxonomy, contracts, and rendering
surfaces** for the THN CLI.

It is the single source of truth for:
    • Error codes and their meanings
    • User vs system vs internal fault classification
    • Retry and user-actionability semantics
    • Human-readable error rendering
    • Machine-readable (JSON) error payloads
    • Command suggestion scoring for invalid input

All CLI-facing error behavior MUST conform to the definitions in this file.

CONTRACT STATUS
---------------
⚠️ EXTERNALLY VISIBLE CONTRACT — SEMANTICS LOCKED

The following are considered **stable, versioned surfaces**:
    • Error codes
    • Error kinds
    • Meaning strings
    • JSON error payload keys
    • Retryable / user_actionable semantics

Once released:
    • Error codes MUST NOT be renumbered
    • Error kinds MUST NOT be repurposed
    • Meaning strings MUST NOT change semantics
    • Output keys MUST NOT be removed or renamed

Additive changes (new error types or new suggestion text) are permitted.

NON-GOALS
---------
• This module does NOT raise exceptions directly
• This module does NOT determine *where* errors occur
• This module does NOT perform logging or telemetry
• This module does NOT exit the process

Those responsibilities belong to command dispatch, engine layers,
or CLI entrypoints.
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable, Sequence

# ---------------------------------------------------------------------
# Atomic error definitions
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CliError:
    """
    Atomic error descriptor.

    This represents a **stable error identity**, independent of context.
    """

    code: int
    kind: str
    meaning: str


USER_ERROR = CliError(
    code=1,
    kind="USER",
    meaning="User input is syntactically or semantically invalid.",
)

INTERNAL_ERROR = CliError(
    code=2,
    kind="INTERNAL",
    meaning="The CLI encountered an unexpected internal error.",
)

SYSTEM_ERROR = CliError(
    code=3,
    kind="SYSTEM",
    meaning="An external dependency or environment condition prevented completion.",
)

ENVIRONMENT_ERROR = CliError(
    code=4,
    kind="ENVIRONMENT",
    meaning="The execution environment is misconfigured or unsupported.",
)

NETWORK_ERROR = CliError(
    code=5,
    kind="NETWORK",
    meaning="A network operation failed or a remote service was unreachable.",
)

PERMISSION_ERROR = CliError(
    code=6,
    kind="PERMISSION",
    meaning="The operation failed due to insufficient permissions.",
)

# ---------------------------------------------------------------------
# Error contracts (policy layer)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ErrorContract:
    """
    Policy wrapper around an atomic error.

    Defines:
        • Suggested user actions
        • Retry semantics
        • Whether the user can reasonably resolve the issue
    """

    error: CliError
    suggestions: Sequence[str] = ()
    retryable: bool = False
    user_actionable: bool = True


USER_CONTRACT = ErrorContract(
    error=USER_ERROR,
    suggestions=(
        "Run `thn --help` to see available commands.",
        "Run `thn <command> --help` for command-specific usage.",
        "Check for typos in the command name.",
    ),
    retryable=False,
    user_actionable=True,
)

INTERNAL_CONTRACT = ErrorContract(
    error=INTERNAL_ERROR,
    retryable=False,
    user_actionable=False,
)

SYSTEM_CONTRACT = ErrorContract(
    error=SYSTEM_ERROR,
    retryable=True,
    user_actionable=True,
)

ENVIRONMENT_CONTRACT = ErrorContract(
    error=ENVIRONMENT_ERROR,
    suggestions=[
        "Verify environment variables and configuration files.",
        "Check Python version compatibility.",
        "Ensure required tools are installed.",
    ],
    retryable=False,
    user_actionable=True,
)

NETWORK_CONTRACT = ErrorContract(
    error=NETWORK_ERROR,
    suggestions=[
        "Check network connectivity.",
        "Verify the remote endpoint is reachable.",
        "Retry the operation.",
    ],
    retryable=True,
    user_actionable=True,
)

PERMISSION_CONTRACT = ErrorContract(
    error=PERMISSION_ERROR,
    suggestions=[
        "Check file and directory permissions.",
        "Re-run with elevated privileges if appropriate.",
    ],
    retryable=False,
    user_actionable=True,
)

# ---------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------


def format_error_header(err: CliError, message: str) -> str:
    """
    Format the canonical single-line error header.
    """
    return f"ERROR [{err.code}: {err.kind}]: {message}"


def render_error(
    contract: ErrorContract,
    message: str,
    *,
    extra_suggestions: list[str] | None = None,
) -> str:
    """
    Render a human-readable error message suitable for terminal output.
    """
    lines: list[str] = []

    err = contract.error
    lines.append(format_error_header(err, message))
    lines.append(f"Meaning: {err.meaning}")

    suggestions = list(contract.suggestions)
    if extra_suggestions:
        suggestions.extend(extra_suggestions)

    if suggestions:
        lines.append("")
        for s in suggestions:
            lines.append(s)

    return "\n".join(lines) + "\n"


def render_error_json(
    contract: ErrorContract,
    message: str,
    *,
    extra_suggestions: list[str] | None = None,
) -> dict:
    """
    Render a machine-readable error payload.

    This surface is consumed by:
        • CLI JSON output modes
        • GUI frontends
        • CI / automation tooling
    """
    suggestions = list(contract.suggestions)
    if extra_suggestions:
        suggestions.extend(extra_suggestions)

    return {
        "status": "ERROR",
        "code": contract.error.code,
        "kind": contract.error.kind,
        "message": message,
        "meaning": contract.error.meaning,
        "suggestions": suggestions,
        "retryable": contract.retryable,
        "user_actionable": contract.user_actionable,
    }


def render_debug_hints(contract: ErrorContract) -> str:
    """
    Emit developer-oriented diagnostics hints.

    Intended for debug / trace modes only.
    """
    lines: list[str] = []

    lines.append("")
    lines.append("Debug recovery hints:")
    lines.append(f"  retryable        : {'yes' if contract.retryable else 'no'}")
    lines.append(f"  user_actionable  : {'yes' if contract.user_actionable else 'no'}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------
# Suggestion engine
# ---------------------------------------------------------------------


def _score(a: str, b: str) -> float:
    return SequenceMatcher(a=a, b=b).ratio()


def _norm(s: str) -> str:
    return s.strip().lower().replace("_", "-").replace(" ", "-")


def suggest(
    bad_token: str,
    candidates: Iterable[str],
    *,
    max_suggestions: int = 5,
    min_score: float = 0.55,
) -> list[str]:
    """
    Suggest close matches for an invalid token.

    Used primarily for command and subcommand name recovery.
    """
    bad = _norm(bad_token)
    scored: list[tuple[float, str]] = []

    for c in candidates:
        cand = str(c)
        cn = _norm(cand)

        base = _score(bad, cn)

        if cn.startswith(bad) or bad.startswith(cn):
            base += 0.10
        if bad in cn or cn in bad:
            base += 0.05

        if base >= min_score:
            scored.append((base, cand))

    scored.sort(key=lambda t: (-t[0], t[1]))
    return [c for _, c in scored[:max_suggestions]]
