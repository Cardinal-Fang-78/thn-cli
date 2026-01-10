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


def test_diag_all_contains_expected_components():
    """
    The diagnostics suite must not drop or filter
    individual diagnostic entries.
    """
    data = run_cli_json("thn diag all")

    components = {d["component"] for d in data["diagnostics"]}

    # These are intentionally broad and stable
    assert "paths" in components
    assert "routing" in components
    assert "registry" in components
    assert "tasks" in components
    assert "plugins" in components
    assert "ui" in components
    assert "hub" in components
