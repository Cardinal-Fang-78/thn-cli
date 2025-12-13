import pytest

from thn_cli.__main__ import main


def run(argv):
    try:
        return main(argv)
    except SystemExit as exc:
        return exc.code


def test_invalid_command_exits_user_error():
    code = run(["not-a-real-command"])
    assert code == 1


def test_help_exits_zero():
    code = run(["--help"])
    assert code == 0


def test_version_exits_zero():
    code = run(["--version"])
    assert code == 0
