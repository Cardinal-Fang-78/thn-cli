import sys

import pytest

from tests.golden._runner import assert_stdout, run_cli


@pytest.mark.skipif(
    sys.version_info[:2] != (3, 14),
    reason="argparse help output is not stable across Python minor versions",
)
def test_help_golden(capsys):
    result = run_cli(["--help"], capsys)

    assert result.code == 0
    assert result.err == ""

    assert_stdout("help", result)
