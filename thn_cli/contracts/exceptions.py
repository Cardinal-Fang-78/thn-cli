# thn_cli/contracts/exceptions.py
from __future__ import annotations

"""
THN CLI Exception Types (Hybrid-Standard)
----------------------------------------

RESPONSIBILITIES
----------------
This module defines **lightweight exception wrappers** used by the THN CLI
to bind raised errors to a specific ErrorContract.

It provides a clean separation between:
    • Error *detection* (command / engine layers)
    • Error *classification* (contracts layer)
    • Error *rendering* (errors.py)

The primary role of these exceptions is to:
    • Carry an ErrorContract alongside a message
    • Preserve optional recovery suggestions
    • Avoid embedding rendering logic in raise sites

CONTRACT STATUS
---------------
⚠️ STABLE INTERNAL CONTRACT — SEMANTICS LOCKED

While this module is not directly user-facing, it is relied upon by:
    • CLI dispatch and entrypoint logic
    • JSON output modes
    • Future GUI and automation layers

The following behaviors MUST remain stable:
    • Attribute names (contract, message, extra_suggestions)
    • Exception inheritance hierarchy
    • Construction semantics

NON-GOALS
---------
• This module does NOT render errors
• This module does NOT assign exit codes
• This module does NOT decide retry behavior
• This module does NOT log or print anything

Those responsibilities belong to:
    • thn_cli.contracts.errors
    • CLI entrypoints / dispatchers
"""

from typing import Sequence


class CommandError(Exception):
    """
    Canonical CLI exception carrying an ErrorContract.

    This exception should be raised by command handlers and core logic
    whenever a failure maps cleanly to a known error contract.
    """

    def __init__(
        self,
        *,
        contract,
        message: str,
        extra_suggestions: Sequence[str] | None = None,
    ):
        super().__init__(message)
        self.contract = contract
        self.message = message
        self.extra_suggestions = list(extra_suggestions or [])
