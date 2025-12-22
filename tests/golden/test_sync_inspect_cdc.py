# tests/golden/test_sync_inspect_cdc.py

"""
CDC-Delta Sync Inspect — Golden Contract Test
--------------------------------------------

PURPOSE
-------
Authoritative golden contract for inspecting CDC-delta Sync V2 envelopes via:

    python -m thn_cli sync inspect <envelope> --json

This test verifies:
    • CDC-delta manifests are summarized correctly
    • File counts and total sizes are stable
    • CDC file listings are deterministic
    • Payload completeness diagnostics are exposed (read-only)

CONTRACT STATUS
---------------
⚠️ GOLDEN — OUTPUT SURFACE LOCKED
"""

import json
import subprocess
import sys
import zipfile

import pytest

# ---------------------------------------------------------------------------
# CRITICAL: Disable pytest output capture for this module
#
# Rationale:
#   • Prevents Windows deadlock with subprocess pipes
#   • Required for CDC inspect tests
#   • Safe for CI and local runs
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.no_capture

THN_CMD = [sys.executable, "-m", "thn_cli"]
SUBPROCESS_TIMEOUT = 30


def test_sync_inspect_cdc_delta(tmp_path):
    """
    Golden test: sync inspect on a CDC-delta envelope.
    """

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

    proc = subprocess.run(
        THN_CMD + ["sync", "inspect", str(envelope_zip), "--json"],
        capture_output=True,
        text=True,
        check=True,
        timeout=SUBPROCESS_TIMEOUT,
    )

    out = json.loads(proc.stdout)

    summary = out["inspect"]["manifest_summary"]
    assert summary["mode"] == "cdc-delta"
    assert summary["file_count"] == 2
    assert summary["total_size"] == 15

    cdc = out["inspect"]["cdc_files"]
    assert cdc["present"] is True
    assert cdc["count"] == 2
    assert cdc["truncated"] is False

    paths = [f["name"] for f in cdc["files"]]
    assert paths == ["alpha.txt", "nested/bravo.bin"]

    diag = out["inspect"]["cdc_diagnostics"]["payload_completeness"]
    assert diag["expected"] == 2
    assert diag["present"] == 2
    assert diag["missing"] == []
    assert diag["extra"] == []
