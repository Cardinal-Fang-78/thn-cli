# tests/contract/test_diagnostic_aggregation_non_enforcing.py
import json
import subprocess
from typing import Any, Dict


def run_cli(args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["thn", *args.split()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def load_json_from_result(result: subprocess.CompletedProcess[str]) -> Dict[str, Any]:
    raw = result.stdout.strip() or result.stderr.strip()
    assert raw, "Expected JSON diagnostic output on stdout or stderr"
    return json.loads(raw)


def test_aggregated_errors_do_not_enforce_behavior() -> None:
    """
    Aggregated diagnostic errors must not enforce behavior.

    Diagnostics are observational only and must not
    block or alter unrelated CLI commands.
    """
    diag_result = run_cli("diag all --json")
    assert diag_result.returncode == 0

    payload = load_json_from_result(diag_result)

    # Even if errors are present, diagnostics remain non-authoritative
    assert isinstance(payload.get("errors", []), list)

    # Unrelated CLI commands must remain usable
    help_result = run_cli("--help")
    assert help_result.returncode == 0
    assert (help_result.stdout or help_result.stderr).strip()

    """
   Top-level help is used intentionally to avoid coupling
   this contract to a specific command topology.
    """
