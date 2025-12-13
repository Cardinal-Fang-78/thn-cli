from tests.golden._runner import assert_stderr, run_cli


def test_invalid_command_golden(capsys):
    result = run_cli(["not-a-real-command"], capsys)

    assert result.code == 1
    assert result.out == ""

    assert_stderr("invalid_command", result)
