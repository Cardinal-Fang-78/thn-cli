# tests/golden/test_syncv2_cdc_inspect_mutation_plan.py

from thn_cli.syncv2.delta.inspectors import inspect_cdc_mutation_plan
from thn_cli.syncv2.delta.mutation_plan import derive_cdc_mutation_plan


def test_inspect_cdc_mutation_plan_stage1_files_only():
    manifest = {
        "version": 2,
        "mode": "cdc-delta",
        "files": [
            {"path": "a.txt", "size": 1},
            {"path": "nested/b.bin", "size": 2},
        ],
    }

    result = inspect_cdc_mutation_plan(manifest)

    assert result == {
        "writes": ["a.txt", "nested/b.bin"],
        "deletes": [],
        "total_writes": 2,
        "total_deletes": 0,
        "mutation_plan": {
            "writes": ["a.txt", "nested/b.bin"],
            "deletes": [],
        },
    }


def test_inspect_cdc_mutation_plan_stage2_entries_write_and_delete():
    manifest = {
        "version": 2,
        "mode": "cdc-delta",
        "entries": [
            {"path": "keep.txt", "op": "write"},
            {"path": "remove.txt", "op": "delete"},
        ],
    }

    result = inspect_cdc_mutation_plan(manifest)

    assert result == {
        "writes": ["keep.txt"],
        "deletes": ["remove.txt"],
        "total_writes": 1,
        "total_deletes": 1,
        "mutation_plan": {
            "writes": ["keep.txt"],
            "deletes": ["remove.txt"],
        },
    }


def test_inspect_cdc_mutation_plan_invalid_manifest_reports_error():
    manifest = {
        "version": 2,
        "mode": "cdc-delta",
    }

    result = inspect_cdc_mutation_plan(manifest)

    assert result["writes"] == []
    assert result["deletes"] == []
    assert result["total_writes"] == 0
    assert result["total_deletes"] == 0
    assert "error" in result
    assert "error" in result["mutation_plan"]


# NOTE: This test intentionally couples inspectors to engine derivation.
def test_cdc_mutation_plan_inspector_matches_engine_derivation():
    """
    Golden: Inspector mutation plan must match engine derivation exactly.

    This test locks parity between:
    - Engine-consumed mutation plan derivation
    - Diagnostic inspection surfaces

    Any divergence here is a contract violation.
    """

    manifest = {
        "version": 2,
        "mode": "cdc-delta",
        "entries": [
            {"path": "write.txt", "op": "write"},
            {"path": "delete.bin", "op": "delete"},
        ],
    }

    engine_writes, engine_deletes = derive_cdc_mutation_plan(manifest)
    inspect_result = inspect_cdc_mutation_plan(manifest)

    assert inspect_result["mutation_plan"]["writes"] == sorted(engine_writes)
    assert inspect_result["mutation_plan"]["deletes"] == sorted(engine_deletes)
