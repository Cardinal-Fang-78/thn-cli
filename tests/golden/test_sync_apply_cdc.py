# tests/golden/test_sync_apply_cdc.py

"""
CDC-Delta Sync Apply — Golden Contract Test
------------------------------------------

PURPOSE
-------
Authoritative golden contract for applying CDC-delta Sync V2 envelopes via:

    python -m thn_cli sync apply <envelope> --json

CONTRACT STATUS
---------------
⚠️ GOLDEN — OUTPUT SURFACE LOCKED
"""

import json
import subprocess
import sys
import zipfile

THN_CMD = [sys.executable, "-m", "thn_cli"]


def test_sync_apply_cdc_delta(tmp_path):
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
        THN_CMD + ["sync", "apply", str(envelope_zip), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )

    out = json.loads(proc.stdout)

    assert out["status"] == "OK"

    apply = out["apply"]
    assert apply["success"] is True
    assert apply["mode"] == "cdc-delta"
    assert apply["applied_count"] == 2

    paths = [f["logical_path"] for f in apply["files"]]
    assert paths == ["alpha.txt", "nested/bravo.bin"]

    diag = apply["cdc_diagnostics"]["payload_completeness"]
    assert diag["expected"] == 2
    assert diag["present"] == 2
    assert diag["missing"] == []
    assert diag["extra"] == []
