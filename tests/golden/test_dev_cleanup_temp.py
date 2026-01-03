from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_dev_cleanup_temp_is_idempotent(tmp_path: Path) -> None:
    """
    Golden safety test:

    thn dev cleanup temp
    - Must emit valid JSON
    - Must delete contents under temp_test
    - Must be safe to run repeatedly
    """

    # ------------------------------------------------------------------
    # Arrange
    # ------------------------------------------------------------------
    temp_root = tmp_path / "temp_test"
    temp_root.mkdir(parents=True)

    # Seed temp root with files and directories
    f1 = temp_root / "file.txt"
    f1.write_text("test", encoding="utf-8")

    sub = temp_root / "subdir"
    sub.mkdir()
    (sub / "inner.txt").write_text("inner", encoding="utf-8")

    # Point THN temp root to this location
    env = dict(**subprocess.os.environ)
    env["THN_TEMP_ROOT"] = str(temp_root)

    # ------------------------------------------------------------------
    # Act (first run)
    # ------------------------------------------------------------------
    proc1 = subprocess.run(
        ["thn", "dev", "cleanup", "temp"],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )

    out1 = json.loads(proc1.stdout)

    # ------------------------------------------------------------------
    # Assert (first run)
    # ------------------------------------------------------------------
    assert out1["success"] is True
    assert out1["message"] == "Temp root cleaned"
    assert isinstance(out1["deleted_paths"], list)

    # Temp root must still exist
    assert temp_root.exists()
    assert temp_root.is_dir()

    # Temp root must be empty after cleanup
    assert list(temp_root.iterdir()) == []

    # ------------------------------------------------------------------
    # Act (second run – idempotency)
    # ------------------------------------------------------------------
    proc2 = subprocess.run(
        ["thn", "dev", "cleanup", "temp"],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )

    out2 = json.loads(proc2.stdout)

    # ------------------------------------------------------------------
    # Assert (second run)
    # ------------------------------------------------------------------
    assert out2["success"] is True
    assert out2["message"] == "Temp root cleaned"
    assert isinstance(out2["deleted_paths"], list)

    # Still empty
    assert list(temp_root.iterdir()) == []
