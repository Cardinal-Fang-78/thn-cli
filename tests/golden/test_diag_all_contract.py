# tests/golden/test_diag_all_contract.py
"""
Golden contract test for `thn diag all`.

This test enforces DX-1.3 diagnostic guarantees:

• The diagnostic suite executes successfully
• All expected diagnostic components are present
• Output shape remains non-enforcing and non-inferential
• Placeholder diagnostics remain explicit and safe
• No legacy aggregation or inferred correctness is reintroduced

This test intentionally does NOT assert:
• System correctness
• Subsystem readiness
• Absence of warnings or errors

It only asserts structural and semantic stability.
"""

from __future__ import annotations

from typing import Dict, List

from thn_cli.__main__ import main

EXPECTED_COMPONENTS = {
    "environment",
    "paths",
    "registry",
    "routing",
    "plugins",
    "tasks",
    "ui",
    "hub",
}


def _run_diag_all() -> Dict[str, object]:
    """
    Invoke `thn diag all` and capture JSON output.

    We rely on main() return code and printed JSON contract.
    """
    import io
    import json
    import sys

    buf = io.StringIO()
    stdout = sys.stdout
    try:
        sys.stdout = buf
        rc = main(["diag", "all"])
    finally:
        sys.stdout = stdout

    assert rc == 0, "thn diag all must exit with code 0"

    try:
        return json.loads(buf.getvalue())
    except Exception as exc:
        raise AssertionError("Output of `thn diag all` is not valid JSON") from exc


def test_diag_all_contract_shape() -> None:
    result = _run_diag_all()

    # Top-level contract
    assert isinstance(result, dict)
    assert "ok" in result
    assert "diagnostics" in result
    assert "errors" in result
    assert "warnings" in result

    assert isinstance(result["ok"], bool)
    assert isinstance(result["diagnostics"], list)
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)


def test_diag_all_contains_expected_components() -> None:
    result = _run_diag_all()
    diagnostics: List[Dict[str, object]] = result["diagnostics"]

    components = set()
    for entry in diagnostics:
        assert isinstance(entry, dict)
        assert "component" in entry
        components.add(entry["component"])

    missing = EXPECTED_COMPONENTS - components
    assert not missing, f"Missing diagnostics: {sorted(missing)}"


def test_diag_entries_are_normalized() -> None:
    result = _run_diag_all()

    for entry in result["diagnostics"]:
        assert "ok" in entry
        assert "component" in entry
        assert "details" in entry
        assert "errors" in entry
        assert "warnings" in entry
        assert "category" in entry

        assert isinstance(entry["ok"], bool)
        assert isinstance(entry["details"], dict)
        assert isinstance(entry["errors"], list)
        assert isinstance(entry["warnings"], list)
        assert isinstance(entry["category"], str)


def test_no_legacy_aggregation_fields_present() -> None:
    """
    Guard against regression to legacy or inferred aggregation.
    """
    result = _run_diag_all()

    forbidden_fields = {
        "summary",
        "passed",
        "failed",
        "total",
        "timestamp",
        "version",
        "health",
        "status_summary",
    }

    for key in forbidden_fields:
        assert key not in result, f"Legacy aggregation field '{key}' must not exist"


def test_placeholder_diagnostics_are_explicit() -> None:
    """
    Placeholder diagnostics must be explicit and non-crashing.
    """
    result = _run_diag_all()

    for entry in result["diagnostics"]:
        if entry["ok"] is False:
            # Must still be structurally valid
            assert isinstance(entry["component"], str)
            assert isinstance(entry["details"], dict)
            assert isinstance(entry["errors"], list)
            assert isinstance(entry["warnings"], list)
