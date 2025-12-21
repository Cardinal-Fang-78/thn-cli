import argparse

from thn_cli.__main__ import build_parser


def test_all_commands_register_callable():
    parser = build_parser()
    subparsers = None

    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparsers = action
            break

    assert subparsers is not None, "No subparsers registered"

    for name, subparser in subparsers.choices.items():
        assert hasattr(subparser, "_defaults"), f"{name} missing defaults"
        assert "func" in subparser._defaults, f"{name} missing func handler"
        assert callable(subparser._defaults["func"]), f"{name} func not callable"
