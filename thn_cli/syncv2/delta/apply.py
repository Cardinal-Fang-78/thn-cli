# thn_cli/syncv2/delta/apply.py

"""
CDC-Delta Apply Engine (Hybrid-Standard)
---------------------------------------

Reconstructs receiver-side files for CDC-delta mode.

Supported manifest shapes
-------------------------
Stage 1 (payload-based, single-file CDC envelope used by current goldens):
    manifest["files"] = [{"path": "...", "size": ...}, ...]
    payload_zip points to payload.zip containing those paths.

Stage 2 (chunk-based, future / optional expansion):
    manifest["entries"] = [{"path": "...", "op": "write|delete", "chunks": [...]}, ...]
    payload_zip reserved (metadata bundles)

Contract
--------
Returns a stable Hybrid-Standard result shape:

    {
        "success": bool,
        "mode": "cdc-delta",
        "target": str,
        "dest_root": str,
        "applied_count": int,
        "files": [
            {"logical_path": str, "dest": str, "size": int|None},
            ...
        ],
        "written_files": int,
        "written_bytes": int,
        "deleted_files": int,
        "errors": [ ... ]   (only if errors exist)
    }
"""

from __future__ import annotations

import os
import uuid
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from .store import load_chunk

# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _resolve_dest_path(dest_root_abs: str, rel_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve a manifest-declared relative path to an absolute destination path,
    rejecting traversal/absolute paths that escape dest_root.

    Returns:
        (dest_path_abs, error_message)
    """
    if not isinstance(rel_path, str) or not rel_path:
        return None, "Missing or invalid path (expected non-empty string)."

    # Reject absolute paths, drive-qualified paths, UNC paths.
    if os.path.isabs(rel_path):
        return None, f"Absolute paths are not allowed: {rel_path!r}"
    drive, _ = os.path.splitdrive(rel_path)
    if drive:
        return None, f"Drive-qualified paths are not allowed: {rel_path!r}"

    # Normalize and ensure it stays within dest_root_abs.
    # Note: use normpath so "a/../b" collapses deterministically.
    normalized = os.path.normpath(rel_path)

    # Reject traversal that results in parent refs.
    # normpath can return ".." or start with "..\\" for traversal.
    parts = normalized.split(os.sep)
    if normalized == ".." or (parts and parts[0] == ".."):
        return None, f"Path traversal is not allowed: {rel_path!r}"

    dest_path_abs = os.path.abspath(os.path.join(dest_root_abs, normalized))
    dest_root_abs_norm = os.path.abspath(dest_root_abs)

    try:
        common = os.path.commonpath([dest_root_abs_norm, dest_path_abs])
    except Exception:
        return None, f"Failed to validate destination path: {rel_path!r}"

    if common != dest_root_abs_norm:
        return None, f"Path escapes destination root: {rel_path!r}"

    return dest_path_abs, None


def _write_bytes_atomic(
    dest_path_abs: str, data_iter, *, errors: List[str], rel_path: str
) -> Tuple[bool, int]:
    """
    Write bytes to dest_path_abs via a temp file + atomic replace.

    Returns:
        (ok, bytes_written)
    """
    dest_dir = os.path.dirname(dest_path_abs)
    os.makedirs(dest_dir, exist_ok=True)

    tmp_path = f"{dest_path_abs}.tmp-{uuid.uuid4().hex}"
    bytes_written = 0

    try:
        with open(tmp_path, "wb") as out_f:
            for chunk in data_iter:
                out_f.write(chunk)
                bytes_written += len(chunk)

        os.replace(tmp_path, dest_path_abs)
        return True, bytes_written

    except Exception as exc:
        errors.append(f"Failed to write {rel_path!r}: {exc}")
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            # Best-effort cleanup only
            pass
        return False, 0


# ---------------------------------------------------------------------------
# CDC-Delta Apply
# ---------------------------------------------------------------------------


def _apply_stage1_payload_files(
    *,
    dest_root: str,
    payload_zip: Optional[str],
    declared_files: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Stage 1: apply by extracting declared files from payload.zip.

    This is the current golden-covered behavior for CDC-delta envelopes produced
    by test fixtures and early tooling.
    """
    errors: List[str] = []
    written_files = 0
    written_bytes = 0

    dest_root_abs = os.path.abspath(dest_root)

    if not payload_zip or not os.path.isfile(payload_zip):
        return {
            "success": False,
            "error": "Missing payload_zip for Stage 1 CDC apply",
            "errors": [f"payload_zip not found: {payload_zip!r}"],
        }

    files_out: List[Dict[str, Any]] = []

    try:
        with zipfile.ZipFile(payload_zip, "r") as zf:
            members = set(zf.namelist())
            for f in declared_files:
                rel_path = f.get("path")
                if not rel_path or not isinstance(rel_path, str):
                    errors.append("Missing or invalid 'path' in manifest['files'] entry.")
                    continue

                dest_path_abs, err = _resolve_dest_path(dest_root_abs, rel_path)
                if err:
                    errors.append(err)
                    continue

                # ZIP member names are expected to be POSIX-style.
                zip_name = rel_path.replace("\\", "/")
                if zip_name not in members:
                    errors.append(f"payload.zip missing expected file: {zip_name!r}")
                    continue

                try:
                    # Stream copy rather than read-all to keep memory bounded.
                    os.makedirs(os.path.dirname(dest_path_abs), exist_ok=True)
                    with zf.open(zip_name) as src_f, open(dest_path_abs, "wb") as out_f:
                        while True:
                            buf = src_f.read(1024 * 1024)
                            if not buf:
                                break
                            out_f.write(buf)
                            written_bytes += len(buf)

                    written_files += 1
                    files_out.append(
                        {
                            "logical_path": rel_path,
                            "dest": str(dest_root_abs),
                            "size": f.get("size"),
                        }
                    )
                except Exception as exc:
                    errors.append(f"Failed to write {rel_path!r} from payload: {exc}")

    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to read payload_zip: {exc}",
            "errors": [str(exc)],
        }

    success = len(errors) == 0
    result: Dict[str, Any] = {
        "success": success,
        "applied_count": written_files if success else 0,
        "files": files_out,
        "written_files": written_files,
        "written_bytes": written_bytes,
        "deleted_files": 0,
    }
    if errors:
        result["errors"] = errors
    return result


def _apply_stage2_chunk_entries(
    *,
    target_name: str,
    dest_root: str,
    entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Stage 2: apply by reconstructing files from chunk IDs via store.load_chunk().

    Safety/robustness guarantees:
    • Only touches manifest-declared entry paths
    • Rejects traversal / absolute paths
    • Uses atomic writes to avoid partial destination files on chunk failure
    """
    written_files = 0
    written_bytes = 0
    deleted_files = 0
    errors: List[str] = []
    files_out: List[Dict[str, Any]] = []

    dest_root_abs = os.path.abspath(dest_root)

    for entry in entries:
        op = entry.get("op", "write")
        rel_path = entry.get("path")

        if not rel_path or not isinstance(rel_path, str):
            errors.append("Missing or invalid 'path' in delta entry.")
            continue

        dest_path_abs, err = _resolve_dest_path(dest_root_abs, rel_path)
        if err:
            errors.append(err)
            continue

        # DELETE OPERATION
        if op == "delete":
            try:
                if os.path.isfile(dest_path_abs):
                    os.remove(dest_path_abs)
                    deleted_files += 1
            except Exception as exc:
                errors.append(f"Failed to delete {rel_path!r}: {exc}")
            continue

        # UNKNOWN OP
        if op != "write":
            errors.append(f"Unknown op={op!r} for path {rel_path!r}")
            continue

        chunks = entry.get("chunks", []) or []
        if not isinstance(chunks, list):
            chunks = []

        def _iter_chunks():
            for chunk_id in chunks:
                if not isinstance(chunk_id, str) or not chunk_id:
                    raise RuntimeError(f"Invalid chunk id: {chunk_id!r}")
                data = load_chunk(target_name, chunk_id)
                if not isinstance(data, (bytes, bytearray)):
                    raise RuntimeError(f"Chunk {chunk_id!r} returned non-bytes payload.")
                yield bytes(data)

        try:
            ok, wrote = _write_bytes_atomic(
                dest_path_abs, _iter_chunks(), errors=errors, rel_path=rel_path
            )
            if not ok:
                continue

            written_bytes += wrote
            written_files += 1
            files_out.append({"logical_path": rel_path, "dest": str(dest_root_abs), "size": None})

        except Exception as exc:
            errors.append(f"Failed to write {rel_path!r}: {exc}")

    success = len(errors) == 0
    result: Dict[str, Any] = {
        "success": success,
        "applied_count": written_files if success else 0,
        "files": files_out,
        "written_files": written_files,
        "written_bytes": written_bytes,
        "deleted_files": deleted_files,
    }
    if errors:
        result["errors"] = errors
    return result


def apply_cdc_delta_envelope(
    *,
    envelope: Dict[str, Any],
    payload_zip: Any,  # Stage 1 uses this (payload.zip). Stage 2 reserves it.
    dest_root: str,
) -> Dict[str, Any]:
    manifest = envelope.get("manifest") or {}
    mode = manifest.get("mode", "")

    if mode != "cdc-delta":
        return {
            "success": False,
            "error": f"apply_cdc_delta_envelope called with non-delta mode={mode!r}",
            "mode": mode,
        }

    target_name = manifest.get("target", "unknown")
    dest_root_abs = os.path.abspath(dest_root)

    # Stage selection:
    #   - If manifest["files"] exists: Stage 1 payload apply (current goldens)
    #   - Else if manifest["entries"] exists: Stage 2 chunk apply
    declared_files = manifest.get("files")
    if isinstance(declared_files, list) and declared_files:
        stage1 = _apply_stage1_payload_files(
            dest_root=dest_root_abs,
            payload_zip=str(payload_zip) if payload_zip is not None else None,
            declared_files=[f for f in declared_files if isinstance(f, dict)],
        )
        result: Dict[str, Any] = {
            "success": bool(stage1.get("success")),
            "mode": "cdc-delta",
            "target": target_name,
            "dest_root": dest_root_abs,
            "applied_count": int(stage1.get("applied_count", 0)),
            "files": stage1.get("files", []),
            "written_files": int(stage1.get("written_files", 0)),
            "written_bytes": int(stage1.get("written_bytes", 0)),
            "deleted_files": int(stage1.get("deleted_files", 0)),
        }
        if stage1.get("errors"):
            result["errors"] = list(stage1.get("errors"))
        if stage1.get("error"):
            result["error"] = stage1.get("error")
        return result

    entries: List[Dict[str, Any]] = manifest.get("entries", []) or []
    stage2 = _apply_stage2_chunk_entries(
        target_name=target_name,
        dest_root=dest_root_abs,
        entries=[e for e in entries if isinstance(e, dict)],
    )

    result: Dict[str, Any] = {
        "success": bool(stage2.get("success")),
        "mode": "cdc-delta",
        "target": target_name,
        "dest_root": dest_root_abs,
        "applied_count": int(stage2.get("applied_count", 0)),
        "files": stage2.get("files", []),
        "written_files": int(stage2.get("written_files", 0)),
        "written_bytes": int(stage2.get("written_bytes", 0)),
        "deleted_files": int(stage2.get("deleted_files", 0)),
    }
    if stage2.get("errors"):
        result["errors"] = list(stage2.get("errors"))
    if stage2.get("error"):
        result["error"] = stage2.get("error")

    # If neither files nor entries exist, this is a malformed delta manifest.
    if not declared_files and not entries:
        result["success"] = False
        result["error"] = "CDC-delta manifest contains neither 'files' nor 'entries'"
        result["errors"] = [
            "Expected manifest['files'] (Stage 1) or manifest['entries'] (Stage 2)."
        ]

    return result
