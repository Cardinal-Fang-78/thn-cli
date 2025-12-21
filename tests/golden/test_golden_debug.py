from ._runner import assert_stderr, run_cli


def test_debug_traceback_golden(capsys):
    result = run_cli(["not-a-real-command"], capsys, debug=True)

    assert result.code == 1

    # argparse errors still surface as USER errors, even in debug mode
    assert "ERROR [1: USER]:" in result.err

    assert_stderr("debug_traceback", result)
