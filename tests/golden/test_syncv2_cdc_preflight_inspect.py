from __future__ import annotations

from typing import Any, Dict

from thn_cli.syncv2.delta.inspectors import inspect_cdc_preflight


def test_cdc_preflight_basic_manifest_only():
    """
    Golden: CDC preflight inspection (manifest-only)

    Verifies:
    • Deterministic mutation intent
    • No payload inference
    • No receiver assumptions
    • Diagnostic-only output
    """

    manifest: Dict[str, Any] = {
        "version": 2,
        "mode": "cdc-delta",
        "files": [
            {"path": "a.txt", "size": 5},
            {"path": "b.txt", "size": 5},
        ],
    }

    result = inspect_cdc_preflight(
        manifest=manifest,
        payload_zip=None,
        target_name=None,
    )

    assert result["mode"] == "cdc-delta"

    # Mutation intent
    assert result["mutation_plan"]["writes"] == ["a.txt", "b.txt"]
    assert result["mutation_plan"]["deletes"] == []
    assert result["mutation_plan"]["total_writes"] == 2
    assert result["mutation_plan"]["total_deletes"] == 0

    # Payload
    assert result["payload"]["expected"] == 0
    assert result["payload"]["present"] == 0
    assert result["payload"]["missing"] == []
    assert result["payload"]["extra"] == []

    # Receiver state (absent)
    assert result["receiver_state"]["has_snapshot"] is False
    assert result["receiver_state"]["entries"] == 0

    # Summary
    assert result["summary"]["mutation_paths"] == 2
    assert result["summary"]["payload_coverage"] == "unknown"
    assert result["summary"]["receiver_ready"] is True


def test_cdc_preflight_invalid_manifest_reports_error():
    """
    Golden: malformed CDC manifest surfaces error in-band
    """

    manifest: Dict[str, Any] = {
        "version": 2,
        "mode": "cdc-delta",
        # missing both files and entries
    }

    result = inspect_cdc_preflight(
        manifest=manifest,
        payload_zip=None,
        target_name=None,
    )

    mutation = result["mutation_plan"]

    assert mutation["writes"] == []
    assert mutation["deletes"] == []
    assert mutation["total_writes"] == 0
    assert mutation["total_deletes"] == 0
    assert "error" in mutation
