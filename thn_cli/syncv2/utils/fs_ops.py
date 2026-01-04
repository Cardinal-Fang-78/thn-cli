# thn_cli/syncv2/utils/fs_ops.py

"""
Filesystem Utilities (Hybrid-Standard)
=====================================

Purpose
-------
Shared filesystem helpers for THN Sync V2:
    • backup creation
    • backup restoration
    • atomic promotion of temporary directories
    • ZIP extraction utilities
    • SHA-256 hashing utilities
    • canonical temp-root resolution and cleanup

Design Goals:
    • Deterministic behavior across all SyncTarget types (cli, web, docs).
    • Strong guardrails: atomic operations whenever possible.
    • Explicit, typed return values.
    • No ambiguity about temporary directory lifecycle.
    • Suitable for both raw-zip and CDC-delta apply paths.

Temp Directory Policy
---------------------
THN defines a single canonical temp root for *THN-owned* artifacts:

    thn_cli/temp_test/

This directory:
    • Is explicitly excluded from version control
    • Is safe to clean at any time
    • Is used for staging, apply destinations, and test fixtures

The temp root MAY be overridden for testing or tooling purposes via:

    THN_TEMP_ROOT=<path>

OS-managed temp locations (e.g. tempfile, %TEMP%) are intentionally
*out of scope* for cleanup and are never touched by this module.

Safety Guarantees (critical)
----------------------------
    • Backups MUST NOT be created inside the destination tree.
      (Prevents recursive backup amplification and disk exhaustion.)
    • This module does not implement dry-run policy. Dry-run behavior is enforced
      by syncv2.engine (no backup calls in dry-run).
    • If a caller attempts an unsafe backup_dir configuration (backup_dir is a
      subpath of src_path *including equality*), backup creation MUST refuse
      with a clear error.

This module contains *no* global state and is safe for use in:
    • syncv2.engine
    • syncv2.delta.apply
    • syncv2.delta.make_delta
    • syncv2.targets.<...>
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Canonical temp-root resolution
# ---------------------------------------------------------------------------

# Default, repo-local temp root (authoritative)
_DEFAULT_TEMP_ROOT = Path(__file__).resolve().parents[2] / "temp_test"


def resolve_temp_root() -> Path:
    """
    Resolve the canonical THN temp root.

    Resolution order:
        1. THN_TEMP_ROOT environment variable (if set)
        2. Built-in default: thn_cli/temp_test/

    Returns:
        Path:
            Absolute path to the resolved temp root.

    Notes:
        • The directory may or may not exist.
        • Callers are responsible for creating it if needed.
        • This function never creates directories implicitly.
    """
    override = os.environ.get("THN_TEMP_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return _DEFAULT_TEMP_ROOT


def cleanup_temp_root() -> List[str]:
    """
    Delete all contents under the resolved THN temp root.

    Behavior:
        • Deletes files and directories *inside* the temp root
        • Never deletes the temp root directory itself
        • Safe and idempotent
        • Returns a list of deleted paths (absolute, stringified)

    Returns:
        List[str]:
            Absolute paths of filesystem entries that were deleted.

    Raises:
        OSError:
            Only if an unexpected filesystem error occurs
            (e.g., permission issues).
    """
    temp_root = resolve_temp_root()
    deleted: List[str] = []

    if not temp_root.exists():
        return deleted

    for entry in temp_root.iterdir():
        try:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
            deleted.append(str(entry))
        except FileNotFoundError:
            # Ignore races / concurrent cleanup
            continue

    return deleted


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def sha256_of_file(path: str) -> str:
    """
    Compute a SHA-256 digest of the file at `path`.

    Returns:
        str:
            Hexadecimal SHA-256 digest string.

    Raises:
        FileNotFoundError:
            If the file does not exist.
        OSError:
            For underlying filesystem read errors.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Backups
# ---------------------------------------------------------------------------


def _is_subpath(child: Path, parent: Path) -> bool:
    """
    Return True if `child` is the same as, or located under, `parent`.

    This function explicitly treats `child == parent` as a subpath.

    Uses resolved paths when possible. If resolution fails, falls back to a
    conservative False to avoid unsafe assumptions.
    """
    try:
        child_r = child.resolve()
        parent_r = parent.resolve()
        child_r.relative_to(parent_r)
        return True
    except Exception:
        return False


def safe_backup_folder(
    src_path: str,
    backup_dir: str,
    *,
    prefix: str = "backup",
) -> Optional[str]:
    """
    Create a timestamped ZIP archive of `src_path` if it exists.

    Returns:
        str:
            Absolute path to the created backup ZIP.
        None:
            When no backup is created (missing source, non-directory source,
            or empty directory).

    Behavior:
        • backup_dir is created if missing
        • resulting file is named:
              <backup_dir>/<prefix>-YYYYMMDD-HHMMSS.zip
        • directory contents are captured recursively
        • empty directories are skipped (no-op backup avoided)
        • REFUSES if backup_dir is inside src_path (including equality)

    Raises:
        RuntimeError:
            If backup_dir is a subpath of src_path.
        OSError:
            If backup_dir cannot be created or ZIP creation fails.
    """
    src = Path(src_path)
    if not src.exists() or not src.is_dir():
        return None

    # Skip empty directories to avoid noise and cost
    try:
        if not any(src.iterdir()):
            return None
    except Exception:
        # If iteration fails, proceed conservatively with backup attempt
        pass

    backup_root = Path(backup_dir)

    # Guardrail: never allow backups inside the tree being backed up
    if _is_subpath(backup_root, src):
        raise RuntimeError(
            "Refusing to create backup inside destination tree.\n"
            f"Destination: {str(src)}\n"
            f"Backup dir:  {str(backup_root)}"
        )

    os.makedirs(str(backup_root), exist_ok=True)

    # Timestamp precision intentionally limited to seconds for clarity and stability
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = f"{prefix}-{ts}"
    base_path = backup_root / base_name
    backup_zip = str(base_path) + ".zip"

    # shutil.make_archive expects base_path without ".zip"
    shutil.make_archive(
        base_name=str(base_path),
        format="zip",
        root_dir=str(src),
    )
    return backup_zip


def restore_backup_zip(
    backup_zip: str,
    dst_path: str,
) -> None:
    """
    Restore a previously created ZIP backup into `dst_path`.

    Behavior:
        • deletes dst_path if it exists
        • extracts ZIP contents into dst_path
        • errors propagate (ZipFile, OSError)

    This function is used during:
        • failed APPLY operations
        • CDC-delta rollback
        • raw-zip rollback
    """
    if os.path.exists(dst_path):
        shutil.rmtree(dst_path)

    os.makedirs(dst_path, exist_ok=True)

    with zipfile.ZipFile(backup_zip, "r") as z:
        z.extractall(dst_path)


# ---------------------------------------------------------------------------
# ZIP extraction helpers
# ---------------------------------------------------------------------------


def extract_zip_to_temp(zip_path: str, prefix: str) -> str:
    """
    Extract `zip_path` into a newly created OS-managed temporary directory.

    Returns:
        str:
            Absolute path to the new temporary directory.

    Notes:
        • Uses OS-managed temp locations intentionally.
        • The resulting directory is NOT under the THN temp root.
        • Cleanup of this directory is the caller's responsibility.

    Raises:
        zipfile.BadZipFile
        OSError
    """
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(temp_dir)
    return temp_dir


# ---------------------------------------------------------------------------
# Atomic promotion
# ---------------------------------------------------------------------------


def safe_promote(temp_dir: str, dst_path: str) -> None:
    """
    Atomically replace `dst_path` with the contents of `temp_dir`.

    Behavior:
        • If dst_path exists → delete it recursively
        • Move temp_dir → dst_path
        • Never leaves partial state if operations succeed sequentially

    This is the final commit step in both:
        • raw-zip APPLY
        • CDC-delta APPLY

    Errors propagate directly to the caller (engine.apply_envelope_v2).
    """
    if os.path.exists(dst_path):
        shutil.rmtree(dst_path)

    shutil.move(temp_dir, dst_path)
