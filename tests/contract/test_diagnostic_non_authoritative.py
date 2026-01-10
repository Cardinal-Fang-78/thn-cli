import json
import subprocess
import sys


def run_cli(cmd: str):
    proc = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc


def test_diag_all_does_not_fail_cli():
    """
    Diagnostics may report failures, but must NOT cause
    the CLI to exit non-zero.
    """
    result = run_cli("thn diag all")

    assert result.returncode == 0, "Diagnostics must never control CLI exit codes"
