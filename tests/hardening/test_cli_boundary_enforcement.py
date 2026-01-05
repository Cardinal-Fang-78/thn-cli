# tests/hardening/test_cli_boundary_enforcement.py
from __future__ import annotations

from types import SimpleNamespace

from thn_cli.cli import build_parser
from thn_cli.contracts.cli_boundaries import (
    BoundaryClass,
    get_known_dual_mode_paths,
    resolve_boundary,
)


def _ns(**kwargs):
    # Minimal Namespace stand-in for boundary resolution.
    return SimpleNamespace(**kwargs)


def test_boundary_resolves_for_known_sync_web_modes() -> None:
    # sync web (default DRY RUN unless --apply)
    args_dry = _ns(command="sync", sync_command="web", apply=False)
    res_dry = resolve_boundary(args_dry)
    assert res_dry.boundary == BoundaryClass.DIAGNOSTIC

    args_apply = _ns(command="sync", sync_command="web", apply=True)
    res_apply = resolve_boundary(args_apply)
    assert res_apply.boundary == BoundaryClass.AUTHORITATIVE


def test_dual_mode_paths_are_explicit() -> None:
    # Ensures dual-mode declarations stay explicit (no silent drift).
    paths = set(get_known_dual_mode_paths())
    assert ("sync", "web") in paths


def test_top_level_fallback_is_deterministic_for_registered_commands() -> None:
    """
    This test enforces the baseline: all registered top-level commands have a
    deterministic boundary classification, even if individual leaf commands
    are not yet fully enumerated in the registry.

    As the audit expands, leaf commands should be added to the explicit
    BOUNDARY_BY_PATH registry and corresponding tests should be added.
    """
    parser = build_parser()

    # Locate the top-level subparsers action and enumerate choices.
    subparsers_actions = [a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction"]
    assert len(subparsers_actions) == 1
    top = subparsers_actions[0]

    for cmd in sorted(top.choices.keys()):
        args = _ns(command=cmd)
        res = resolve_boundary(args)
        assert res.path == (cmd,)
        assert res.boundary in {
            BoundaryClass.AUTHORITATIVE,
            BoundaryClass.DIAGNOSTIC,
            BoundaryClass.PRESENTATION,
        }
