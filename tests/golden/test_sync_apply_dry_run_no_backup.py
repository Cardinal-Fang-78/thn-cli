import json
import subprocess
import zipfile
from pathlib import Path


def test_sync_apply_dry_run_creates_no_backups(tmp_path: Path) -> None:
    """
    Golden safety test:
    --dry-run MUST NOT create backups or write to disk.
    """

    # ------------------------------------------------------------------
    # Arrange
    # ------------------------------------------------------------------
    dest = tmp_path / "apply_dest"
    dest.mkdir(parents=True)

    marker = dest / "marker.txt"
    marker.write_text("do not modify", encoding="utf-8")

    # Create payload.zip (minimal but valid)
    payload_zip = tmp_path / "payload.zip"
    with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("file.txt", "hello")

    # Create manifest.json
    manifest = {
        "version": 2,
        "mode": "raw-zip",
        "file_count": 1,
        "total_size": 5,
    }

    # Create full envelope ZIP
    envelope = tmp_path / "test.thn-envelope.zip"
    with zipfile.ZipFile(envelope, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.write(payload_zip, arcname="payload.zip")

    # ------------------------------------------------------------------
    # Act
    # ------------------------------------------------------------------
    proc = subprocess.run(
        [
            "thn",
            "sync",
            "apply",
            str(envelope),
            "--dry-run",
            "--json",
            "--dest",
            str(dest),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(proc.stdout)

    # ------------------------------------------------------------------
    # Assert — JSON surface
    # ------------------------------------------------------------------
    assert data["success"] is True
    assert data["operation"] == "dry-run"
    assert data["destination"] == str(dest)
    assert data["scope"] == "authoritative"

    # ------------------------------------------------------------------
    # Assert — destination untouched
    # ------------------------------------------------------------------
    assert marker.exists()
    assert marker.read_text(encoding="utf-8") == "do not modify"

    # ------------------------------------------------------------------
    # Assert — NO backups created
    # ------------------------------------------------------------------
    forbidden = [
        p
        for p in tmp_path.rglob("*")
        if (p.is_dir() and p.name in ("_thn_backups", "_backups"))
        or (p.is_file() and p.name.startswith("backup-"))
    ]

    assert forbidden == [], f"Unexpected backup artifacts found: {forbidden}"
