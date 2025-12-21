# thn_cli/contracts/suggestions.py
from __future__ import annotations

import argparse
from typing import List, Optional

from thn_cli.contracts.errors import ErrorContract, suggest


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for s in items:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _extract_flag_tokens(argv: list[str]) -> list[str]:
    return [a for a in argv if a.startswith("-")]


def resolve_suggestions(
    *,
    contract: ErrorContract,
    argv: Optional[List[str]],
    parser: argparse.ArgumentParser,
    exception: Exception | None = None,
) -> List[str]:
    """
    Resolve human-readable suggestions for an error.

    This function:
      • Is pure and deterministic
      • Never prints
      • Never raises
      • Never mutates inputs
    """

    suggestions_out: List[str] = []

    # ------------------------------------------------------------------
    # Layer 1 — Contract baseline (always first)
    # ------------------------------------------------------------------
    suggestions_out.extend(contract.suggestions)

    # ------------------------------------------------------------------
    # Layer 2 — Top-level command suggestions (USER errors only)
    # ------------------------------------------------------------------
    if contract.error.kind == "USER" and argv:
        first = argv[0]
        if isinstance(first, str) and first and not first.startswith("-"):
            valid = getattr(parser, "_defaults", {}).get("_thn_valid_commands", []) or []
            suggestions_out.extend(suggest(first, valid))

    # ------------------------------------------------------------------
    # Layer 3 — Flag-level suggestions (scoped, USER errors only)
    # ------------------------------------------------------------------
    if contract.error.kind == "USER" and argv:
        flag_tokens = _extract_flag_tokens(argv)

        if flag_tokens:
            known_flags: list[str] = []

            for action in parser._actions:
                for opt in action.option_strings:
                    known_flags.append(opt)

            for bad_flag in flag_tokens:
                suggestions_out.extend(suggest(bad_flag, known_flags))

    # Layer 4 — Internal/System hints
    # (Already covered by contract baseline)

    return _dedupe_preserve_order(suggestions_out)
