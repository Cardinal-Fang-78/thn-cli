# tests/golden/test_inspect_cdc.py

"""
CDC Inspect Command - Golden Contract Test
-----------------------------------------

PURPOSE
-------
Defines the golden contract for:

    thn inspect cdc <envelope> --json

It verifies that:
    - Payload completeness diagnostics are surfaced and correct for CDC-delta
    - Snapshot and chunk-health diagnostics are surfaced deterministically
    - The output surface is stable for CLI, CI, and future GUI consumers

CONTRACT STATUS
---------------
GOLDEN - OUTPUT SURFACE LOCKED

Any changes to:
    - keys
    - nesting
    - count semantics
    - completeness semantics

MUST be accompanied by updated golden expectations or a versioned change.

NON-GOALS
---------
- Does not validate signature enforcement
- Does not validate routing correctness
- Does not validate CDC chunking internals
"""

import json
import subprocess
import zipfile


def test_inspect_cdc_delta_payload_completeness(tmp_path):
    # ------------------------------------------------------------------
    # Build synthetic CDC envelope
    # ------------------------------------------------------------------
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
        # Use a very specific target name to avoid colliding with any real snapshots.
        "meta": {"target": "golden_test__inspect_cdc__target"},
    }

    (envelope_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Build payload.zip with POSIX arcnames (CRITICAL)
    # ------------------------------------------------------------------
    payload_zip = envelope_dir / "payload.zip"
    with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(payload_src / "alpha.txt", arcname="alpha.txt")
        zf.write(payload_src / "nested" / "bravo.bin", arcname="nested/bravo.bin")

    # ------------------------------------------------------------------
    # Build final envelope zip
    # ------------------------------------------------------------------
    envelope_zip = tmp_path / "cdc.thn-envelope.zip"
    subprocess.check_call(
        ["python", "-m", "zipfile", "-c", str(envelope_zip), "manifest.json", "payload.zip"],
        cwd=envelope_dir,
    )

    # ------------------------------------------------------------------
    # Run inspect cdc
    # ------------------------------------------------------------------
    proc = subprocess.run(
        ["thn", "inspect", "cdc", str(envelope_zip), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )

    out = json.loads(proc.stdout)
    assert out["status"] == "OK"

    insp = out["inspect"]
    assert insp["mode"] == "cdc-delta"

    diag = insp["cdc_diagnostics"]["payload_completeness"]
    assert diag["expected"] == 2
    assert diag["present"] == 2
    assert diag["missing"] == []
    assert diag["extra"] == []

    # Snapshot diagnostics are surfaced; we only assert the stable shape.
    snap = insp["cdc_diagnostics"]["snapshot"]
    assert "target" in snap
    assert snap["has_snapshot"] in (True, False)

    chunk = insp["cdc_diagnostics"]["chunk_health"]
    assert "target" in chunk
    assert chunk["has_snapshot"] in (True, False)
    assert isinstance(chunk["missing_chunks"], list)
