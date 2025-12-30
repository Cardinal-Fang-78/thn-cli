# tests/golden/test_sync_apply_dry_run.py

"""
Sync V2 Apply — Dry-Run (Golden Contract Test)
----------------------------------------------

PURPOSE
-------
Golden contract for Sync V2 apply dry-run via:

    python -m thn_cli sync apply <envelope> --dry-run --json

This test binds ONLY to the engine-level apply contract as defined in:

    docs/THN_CLI_Golden_Master_Spec.md

CONTRACT STATUS
---------------
⚠️ GOLDEN — OUTPUT SURFACE LOCKED
"""

import json
import subprocess
import sys
import zipfile

import pytest

# ------------------------------------------------------------------
# CRITICAL: Disable pytest output capture for this module
#
# Rationale:
#   • Prevents Windows deadlock with subprocess pipes
#   • Matches existing CDC apply golden posture
# ------------------------------------------------------------------
pytestmark = pytest.mark.no_capture

THN_CMD = [sys.executable, "-m", "thn_cli"]


def test_sync_apply_dry_run_cdc_delta(tmp_path):
    # ------------------------------------------------------------
    # Build a minimal CDC-delta envelope
    # ------------------------------------------------------------
    envelope_dir = tmp_path / "cdc_env"
    envelope_dir.mkdir()

    payload_src = envelope_dir / "payload_src"
    payload_src.mkdir()

    (payload_src / "alpha.txt").write_text("hello", encoding="utf-8")
    nested = payload_src / "nested"
    nested.mkdir()
    (nested / "bravo.bin").write_bytes(b"1234567890")

    manifest = {
        "version": 2,
        "mode": "cdc-delta",
        "files": [
            {"path": "alpha.txt", "size": 5},
            {"path": "nested/bravo.bin", "size": 10},
        ],
        "meta": {},
    }

    (envelope_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    payload_zip = envelope_dir / "payload.zip"
    with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(payload_src / "alpha.txt", arcname="alpha.txt")
        zf.write(payload_src / "nested" / "bravo.bin", arcname="nested/bravo.bin")

    envelope_zip = tmp_path / "cdc.thn-envelope.zip"
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "zipfile",
            "-c",
            str(envelope_zip),
            "manifest.json",
            "payload.zip",
        ],
        cwd=envelope_dir,
    )

    # ------------------------------------------------------------
    # Invoke CLI apply dry-run (authoritative engine path)
    # ------------------------------------------------------------
    proc = subprocess.run(
        THN_CMD + ["sync", "apply", str(envelope_zip), "--dry-run", "--json"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,  # REQUIRED safety net
    )

    result = json.loads(proc.stdout)

    # ------------------------------------------------------------
    # Golden assertions — engine dry-run contract only
    # ------------------------------------------------------------
    assert result["success"] is True
    assert result["operation"] == "dry-run"
    assert result["mode"] == "cdc-delta"

    # Required identity fields
    assert isinstance(result.get("target"), str) and result["target"].strip()
    assert isinstance(result.get("destination"), str) and result["destination"].strip()

    # Routing must be present and be a dict; field values are not asserted here
    routing = result.get("routing")
    assert isinstance(routing, dict)
    assert "category" in routing
    assert "confidence" in routing

    # Dry-run must not claim apply results
    assert "applied_count" not in result
    assert "files" not in result
    assert "backup_created" not in result
    assert "backup_zip" not in result
    assert "restored_previous_state" not in result
