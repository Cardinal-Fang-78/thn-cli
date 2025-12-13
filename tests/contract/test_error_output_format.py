import re

import pytest

from thn_cli.__main__ import main


def capture(argv, capsys):
    try:
        main(argv)
    except SystemExit:
        pass
    return capsys.readouterr()


def test_user_error_message_format(capsys):
    out = capture(["not-a-real-command"], capsys)

    assert out.out == ""
    assert out.err.startswith("ERROR [1: USER]:")


def test_error_message_contains_human_text(capsys):
    out = capture(["not-a-real-command"], capsys)

    # Must not be empty or cryptic
    assert len(out.err.strip()) > 20
