from tests.golden._runner import assert_stdout, run_cli


def test_version_golden(capsys):
    result = run_cli(["--version"], capsys)

    assert result.code == 0
    assert result.err == ""

    assert_stdout("version", result)
