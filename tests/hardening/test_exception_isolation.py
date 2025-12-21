import argparse

from thn_cli.__main__ import build_parser, main


class Boom(Exception):
    pass


def test_internal_exception_returns_internal_error(monkeypatch):
    def explode(_args):
        raise Boom("kaboom")

    # Build a real parser
    parser = build_parser()

    # Find subparsers
    subparsers = None
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparsers = action
            break

    assert subparsers is not None

    # Inject a real command
    boom = subparsers.add_parser("boom")
    boom.set_defaults(func=explode)

    # Force main() to use our modified parser
    monkeypatch.setattr(
        "thn_cli.__main__.build_parser",
        lambda: parser,
    )

    code = main(["boom"])
    assert code == 2
