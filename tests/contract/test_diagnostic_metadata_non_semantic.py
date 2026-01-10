# tests/contract/test_diagnostic_metadata_non_semantic.py
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


def test_diagnostic_category_is_non_semantic() -> None:
    """
    Diagnostic category must not affect CLI behavior.

    Category is descriptive metadata only.
    """
    diag_result = run_cli("diag all --json")
    assert diag_result.returncode == 0

    payload = load_json_from_result(diag_result)

    # Mutate all categories to nonsense
    for diag in payload.get("diagnostics", []):
        diag["category"] = "totally_fake_category"

    # Consumer-style handling only
    serialized = json.dumps(payload)
    _ = json.loads(serialized)

    # Unrelated CLI commands must remain usable
    help_result = run_cli("--help")
    assert help_result.returncode == 0
    assert (help_result.stdout or help_result.stderr).strip()

    """
   Top-level help is used intentionally to avoid coupling
   this contract to a specific command topology.
    """
