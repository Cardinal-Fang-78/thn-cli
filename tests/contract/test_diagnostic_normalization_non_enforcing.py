import subprocess
import sys


def run_cli(args: str):
    return subprocess.run(
        [sys.executable, "-m", "thn_cli.cli", *args.split()],
        capture_output=True,
        text=True,
    )


def test_normalization_does_not_enforce_behavior():
    """
    Diagnostic normalization must not affect unrelated CLI behavior.
    """

    diag_result = run_cli("diag all --json")
    assert diag_result.returncode == 0

    # Top-level help used intentionally to avoid command coupling
    help_result = run_cli("--help")
    assert help_result.returncode == 0
