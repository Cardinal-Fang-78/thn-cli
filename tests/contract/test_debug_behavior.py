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
    """
    Invalid user input should never emit a traceback
    when debug mode is disabled.
    """
    monkeypatch.delenv("THN_CLI_DEBUG", raising=False)

    out = run(["not-a-real-command"], capsys)

    assert "Traceback" not in out.err
    assert "ERROR" in out.err
    assert "USER" in out.err


def test_no_traceback_with_debug_for_user_errors(capsys, monkeypatch):
    """
    Debug mode does NOT imply tracebacks for argparse / user-input errors.

    Rationale:
        - argparse does not raise real exceptions
        - invalid commands are USER errors, not SYSTEM faults
        - emitting tracebacks here would be misleading and noisy
    """
    monkeypatch.setenv("THN_CLI_DEBUG", "1")

    out = run(["not-a-real-command"], capsys)

    assert "Traceback" not in out.err
    assert "ERROR" in out.err
    assert "USER" in out.err
