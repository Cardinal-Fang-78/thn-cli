# tests/test_entrypoint.py

import thn_cli
from thn_cli.__main__ import build_parser, main


def test_package_imports():
    # Basic sanity: the package must import without error.
    assert thn_cli is not None


def test_build_parser():
    parser = build_parser()
    assert parser is not None


def test_help_exits_zero(capsys):
    # `thn --help` should return 0 and print usage.
    code = main(["--help"])
    captured = capsys.readouterr()
    assert code == 0
    assert "THN Master Control / THN CLI" in captured.out
