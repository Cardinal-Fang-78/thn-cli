# thn_cli/__main__.py
"""
THN CLI Entrypoint (Hybrid-Standard)
===================================

RESPONSIBILITIES
----------------
Defines the canonical executable entrypoint for the THN CLI.

This file is responsible for:
    • Normalizing argv across invocation styles
    • Bootstrapping argparse construction
    • Dispatching commands to registered handlers
    • Enforcing stable exit-code and error-reporting semantics
    • Acting as the single source of truth for CLI startup behavior

SUPPORTED INVOCATION MODES
--------------------------
    • thn <command> [...]
    • thn.exe <command> [...]
    • python -m thn_cli <command> [...]
    • Subprocess-driven test execution

INVARIANTS
----------
    • No command logic lives here
    • No filesystem mutation
    • All errors are surfaced via CommandError or INTERNAL error fallback
    • Exit codes MUST remain stable and contract-driven
    • argv normalization MUST be deterministic and idempotent

NON-GOALS
---------
    • Argument parsing logic
    • Command registration
    • Business logic execution
    • Output formatting beyond fatal error fallback

CONTRACT STATUS
---------------
LOCKED CORE ENTRYPOINT

Changes to this file affect:
    • All CLI executions
    • All golden tests
    • All subprocess invocations
    • GUI / CI / automation consumers

Modify only with extreme care.
"""

from __future__ import annotations

import os
import sys

from thn_cli.cli import build_parser, dispatch
from thn_cli.contracts.errors import INTERNAL_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.contracts.formatting import emit_error


def _debug_enabled() -> bool:
    """
    Determine whether CLI debug/trace mode is enabled.

    Canonical environment variable:
        • THN_CLI_DEBUG=1

    Supported aliases (legacy or engine-wide):
        • THN_CLI_TRACE=1
        • THN_TRACE=1
    """
    return (
        os.getenv("THN_CLI_DEBUG") == "1"
        or os.getenv("THN_CLI_TRACE") == "1"
        or os.getenv("THN_TRACE") == "1"
    )


def _normalize_argv(argv: list[str]) -> list[str]:
    """
    Normalize argv across all invocation styles.

    This strips legacy or wrapper-injected program tokens such as:
        • "thn"
        • "thn.exe"

    Ensures consistent behavior for:
        • thn <command>
        • python -m thn_cli <command>
        • test subprocess invocation
    """
    if not argv:
        return argv

    first = argv[0].lower()

    if first == "thn" or first.endswith("thn.exe"):
        return argv[1:]

    return argv


def main(argv: list[str] | None = None) -> int:
    """
    CLI entrypoint.

    Returns an integer exit code compatible with:
        • Shell execution
        • Subprocess invocation
        • CI pipelines
    """
    if argv is None:
        argv = sys.argv[1:]

    argv = _normalize_argv(argv)

    debug = _debug_enabled()

    try:
        parser = build_parser()
        return dispatch(argv, parser=parser)

    except CommandError as exc:
        emit_error(exc, debug=debug)
        return exc.contract.error.code

    except Exception as exc:
        if debug:
            raise

        # INTERNAL fallback — contract-driven, stable exit code
        emit_error(
            CommandError(
                contract=INTERNAL_CONTRACT,
                message="Internal error",
            ),
            debug=False,
        )
        return INTERNAL_CONTRACT.error.code


# Explicit re-exports for test contracts
__all__ = [
    "main",
    "build_parser",
]


if __name__ == "__main__":
    raise SystemExit(main())
