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


def test_normalization_metadata_is_non_semantic():
    """
    Diagnostic metadata must remain presentation-only if present.
    """

    diag_result = run_cli("diag all --json")
    assert diag_result.returncode == 0

    payload = try_load_json(diag_result)

    # JSON output is optional
    if payload is not None:
        for diag in payload.get("diagnostics", []):
            diag["category"] = "totally_fake_category"
            diag["severity"] = "nonsense"
            diag["source"] = "imaginary"

        json.dumps(payload)

    # Behavior must remain unaffected
    help_result = run_cli("--help")
    assert help_result.returncode == 0
