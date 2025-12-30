from tests.golden._runner import assert_stdout, run_cli


def test_unified_history_strict_diagnostics(capsys):
    result = run_cli(
        ["sync", "history", "--unified", "--strict", "--json"],
        capsys,
    )

    assert result.code == 0
    assert '"strict"' in result.out
