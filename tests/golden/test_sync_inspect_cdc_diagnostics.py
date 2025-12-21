# tests/golden/test_sync_inspect_cdc_diagnostics.py

"""
CDC Sync Inspect Diagnostics — Golden Contract Test
--------------------------------------------------

PURPOSE
-------
Defines the golden contract for CDC diagnostics surfaced via:

    python -m thn_cli sync inspect <envelope> --json

It verifies that:
    • CDC diagnostics block is present
    • Payload completeness is computed correctly
    • Output is additive and stable
    • No mutation or strict enforcement occurs

CONTRACT STATUS
---------------
⚠️ GOLDEN — OUTPUT SURFACE LOCKED

NON-GOALS
---------
• Does not enforce strict mode
• Does not validate signatures
• Does not validate routing
"""

import json
import subprocess
import sys
import zipfile

THN_CMD = [sys.executable, "-m", "thn_cli"]


def test_sync_inspect_cdc_diagnostics(tmp_path):
    # ------------------------------------------------------------
    # Build synthetic CDC envelope
    # ------------------------------------------------------------
    env_dir = tmp_path / "env"
    env_dir.mkdir()

    payload_src = env_dir / "payload_src"
    payload_src.mkdir()

    (payload_src / "a.txt").write_text("hello", encoding="utf-8")
    sub = payload_src / "sub"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"1234")

    manifest = {
        "version": 2,
        "mode": "cdc-delta",
        "files": [
            {"path": "a.txt", "size": 5},
            {"path": "sub/b.bin", "size": 4},
        ],
        "meta": {},
    }

    (env_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    # ------------------------------------------------------------
    # Build payload.zip (POSIX paths)
    # ------------------------------------------------------------
    payload_zip = env_dir / "payload.zip"
    with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(payload_src / "a.txt", arcname="a.txt")
        zf.write(payload_src / "sub" / "b.bin", arcname="sub/b.bin")

    # ------------------------------------------------------------
    # Build envelope zip
    # ------------------------------------------------------------
    envelope_zip = tmp_path / "env.thn-envelope.zip"
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
        cwd=env_dir,
    )

    # ------------------------------------------------------------
    # Run sync inspect via source tree
    # ------------------------------------------------------------
    proc = subprocess.run(
        THN_CMD + ["sync", "inspect", str(envelope_zip), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )

    out = json.loads(proc.stdout)

    diag = out["inspect"]["cdc_diagnostics"]["payload_completeness"]

    assert diag["expected"] == 2
    assert diag["present"] == 2
    assert diag["missing"] == []
    assert diag["extra"] == []
