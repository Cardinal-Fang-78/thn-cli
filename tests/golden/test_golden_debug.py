from tests.golden._runner import assert_stderr, run_cli


def test_debug_traceback_golden(capsys):
    result = run_cli(["not-a-real-command"], capsys, debug=True)

    assert result.code == 1

    # NOTE:
    # argparse errors do not raise exceptions yet,
    # so debug mode still emits a user error.
    assert "ERROR [1: USER]:" in result.err

    assert_stderr("debug_traceback", result)
