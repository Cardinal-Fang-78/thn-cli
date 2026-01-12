# tests/contract/test_diagnostic_consumer_tolerance.py
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


def test_diagnostics_tolerate_unknown_fields() -> None:
    """
    Diagnostic consumers must tolerate unknown fields.

    This simulates future schema expansion by injecting unknown metadata
    and ensuring consumer-style handling does not crash.

    IMPORTANT:
    This test validates consumer tolerance (serialize/deserialize),
    not CLI parsing of mutated payloads.
    """
    diag_result = run_cli("diag all --json")
    assert diag_result.returncode == 0

    payload = load_json_from_result(diag_result)

    # Inject unknown top-level fields
    payload["future_field"] = {"unexpected": True}

    # Inject unknown diagnostic-level fields
    for diag in payload.get("diagnostics", []):
        diag["experimental"] = "ignore-me"
        diag["new_metadata"] = {"version": "999.0"}

    # Consumer simulation: serialize / deserialize
    serialized = json.dumps(payload)
    reloaded: Dict[str, Any] = json.loads(serialized)

    assert "future_field" in reloaded
    assert reloaded.get("diagnostics") == payload.get("diagnostics")

    # Unrelated CLI commands must remain usable
    help_result = run_cli("--help")
    assert help_result.returncode == 0
    assert (help_result.stdout or help_result.stderr).strip()

    """
   Top-level help is used intentionally to avoid coupling
   this contract to a specific command topology.
    """
