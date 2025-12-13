from tests.golden._runner import assert_stdout, run_cli


def test_help_golden(capsys):
    result = run_cli(["--help"], capsys)

    assert result.code == 0
    assert result.err == ""

    assert_stdout("help", result)
