import os

import pytest

from thn_cli.__main__ import main


def run(argv, capsys):
    try:
        main(argv)
    except SystemExit:
        pass
    return capsys.readouterr()


def test_no_traceback_without_debug(capsys, monkeypatch):
    monkeypatch.delenv("THN_CLI_DEBUG", raising=False)

    out = run(["not-a-real-command"], capsys)
    assert "Traceback" not in out.err


def test_traceback_present_with_debug(capsys, monkeypatch):
    monkeypatch.setenv("THN_CLI_DEBUG", "1")

    out = run(["not-a-real-command"], capsys)
    assert "Traceback" in out.err
