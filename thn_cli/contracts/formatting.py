# thn_cli/contracts/formatting.py
from __future__ import annotations

"""
THN CLI Error Formatting & Emission (Hybrid-Standard)
----------------------------------------------------

RESPONSIBILITIES
----------------
This module provides the **authoritative error emission path** for the THN CLI.

It is responsible for:
    • Rendering errors using ErrorContract definitions
    • Enforcing traceback visibility rules
    • Writing output exclusively to stderr
    • Preserving stable, golden-testable formatting

This module is the final step in the error lifecycle:
    detection → classification → rendering → emission

CONTRACT STATUS
---------------
⚠️ USER-FACING OUTPUT CONTRACT — SEMANTICS LOCKED

The output produced by this module is:
    • relied upon by golden tests
    • consumed by automation and CI
    • expected to remain stable across releases

Any change to:
    • ordering
    • wording
    • newline behavior
    • traceback rules

MUST be accompanied by:
    • explicit contract review
    • golden test updates
    • or a versioned surface change

TRACEBACK POLICY
----------------
• USER errors NEVER emit tracebacks
• SYSTEM errors emit tracebacks ONLY when debug=True
• INTERNAL errors follow SYSTEM behavior
• Output is ALWAYS written to stderr

NON-GOALS
---------
• This module does NOT decide exit codes
• This module does NOT classify errors
• This module does NOT log to files
• This module does NOT format JSON output

Those responsibilities belong to:
    • thn_cli.contracts.errors
    • CLI entrypoints / dispatchers
"""

import sys
import traceback

from thn_cli.contracts.errors import ErrorContract, render_error
from thn_cli.contracts.exceptions import CommandError


def emit_error(exc: CommandError, *, debug: bool = False) -> None:
    """
    Emit a contract-formatted error message.

    Guarantees:
    - USER errors never emit tracebacks
    - SYSTEM errors emit tracebacks ONLY when debug is enabled
    - Writes ONLY to stderr
    - Stable golden-testable format
    """
    contract: ErrorContract = exc.contract

    # SYSTEM traceback only when debugging
    if debug and contract.error.kind == "SYSTEM":
        traceback.print_exc(file=sys.stderr)
        return

    sys.stderr.write(
        render_error(
            contract,
            exc.message,
            extra_suggestions=list(getattr(exc, "extra_suggestions", []) or []),
        )
    )
