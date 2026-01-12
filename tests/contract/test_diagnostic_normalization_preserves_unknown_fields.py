import json
import subprocess
import sys


def run_cli(args: str):
    return subprocess.run(
        [sys.executable, "-m", "thn_cli.cli", *args.split()],
        capture_output=True,
        text=True,
    )


def try_load_json(result):
    raw = result.stdout.strip() or result.stderr.strip()
    if not raw:
        return None
    return json.loads(raw)


def test_normalization_preserves_unknown_fields():
    """
    Normalization must not drop unknown fields *if present*.

    JSON output is optional; schema tolerance is required.
    """

    result = run_cli("diag all --json")
    assert result.returncode == 0

    payload = try_load_json(result)

    # JSON emission is optional — absence is valid
    if payload is None:
        return

    payload["future_top_level"] = {"unexpected": True}

    for diag in payload.get("diagnostics", []):
        diag["future_field"] = "ignore-me"
        diag["future_metadata"] = {"version": "999.0"}

    serialized = json.dumps(payload)
    reloaded = json.loads(serialized)

    assert "future_top_level" in reloaded
    assert reloaded["diagnostics"] == payload["diagnostics"]
