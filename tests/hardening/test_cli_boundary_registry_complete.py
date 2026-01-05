from __future__ import annotations

import argparse
from types import SimpleNamespace
from typing import List

from thn_cli.cli import build_parser
from thn_cli.contracts.cli_boundaries import resolve_boundary


def _ns(**kwargs: object) -> argparse.Namespace:
    return SimpleNamespace(**kwargs)  # type: ignore[return-value]


def test_all_top_level_commands_have_boundary_classification() -> None:
    """
    Invariant: every top-level argparse command must resolve to a boundary class.

    This is a strict guardrail preventing silent expansion of the CLI surface
    without updating the boundary registry.
    """
    parser = build_parser()

    subparsers_actions = [a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction"]
    assert len(subparsers_actions) == 1
    top = subparsers_actions[0]

    missing: List[str] = []
    for cmd in sorted(top.choices.keys()):
        try:
            resolve_boundary(_ns(command=cmd))
        except Exception:
            missing.append(cmd)

    assert not missing, f"Missing boundary registry entries for: {', '.join(missing)}"
