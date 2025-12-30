import json
import subprocess
import sys


def test_sync_status_read_stub_json():
    cmd = [
        sys.executable,
        "-m",
        "thn_cli",
        "sync",
        "status",
        "--json",
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0

    data = json.loads(proc.stdout)

    assert data == {
        "status": "not_implemented",
        "scope": "diagnostic",
        "authority": "status_db",
        "message": "Status DB read surface stub placeholder",
    }
