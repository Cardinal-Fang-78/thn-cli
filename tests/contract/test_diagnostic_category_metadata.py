import json
import subprocess


def run_cli_json(cmd: str):
    proc = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.returncode == 0
    return json.loads(proc.stdout)


def test_diagnostic_category_is_metadata_only():
    """
    Category must exist and be a string,
    but must not imply severity or behavior.
    """
    data = run_cli_json("thn diag all")

    for diag in data["diagnostics"]:
        assert "category" in diag
        assert isinstance(diag["category"], str)
