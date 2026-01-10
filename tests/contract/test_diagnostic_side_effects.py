import subprocess
import sys


def run_cli(args: str):
    return subprocess.run(
        [sys.executable, "-m", "thn_cli.cli", *args.split()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_diag_all_does_not_affect_other_commands():
    """
    Diagnostics must not mutate global state
    or affect unrelated commands.
    """
    run_cli("diag all")

    result = run_cli("version")
    assert result.returncode == 0
