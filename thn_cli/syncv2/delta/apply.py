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
import zipfile
from typing import Any, Dict, List, Optional

from .store import load_chunk

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

                # ZIP member names are expected to be POSIX-style.
                zip_name = rel_path.replace("\\", "/")
                if zip_name not in members:
                    errors.append(f"payload.zip missing expected file: {zip_name!r}")
                    continue

                dest_path = os.path.join(dest_root, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                try:
                    with zf.open(zip_name) as src_f, open(dest_path, "wb") as out_f:
                        data = src_f.read()
                        out_f.write(data)
                        written_bytes += len(data)
                    written_files += 1
                    files_out.append(
                        {
                            "logical_path": rel_path,
                            "dest": str(dest_root),
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
        "files": files_out if success else files_out,
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
    """
    written_files = 0
    written_bytes = 0
    deleted_files = 0
    errors: List[str] = []
    files_out: List[Dict[str, Any]] = []

    for entry in entries:
        op = entry.get("op", "write")
        rel_path = entry.get("path")

        if not rel_path:
            errors.append("Missing 'path' in delta entry.")
            continue

        dest_path = os.path.join(dest_root, rel_path)

        # DELETE OPERATION
        if op == "delete":
            try:
                if os.path.isfile(dest_path):
                    os.remove(dest_path)
                    deleted_files += 1
            except Exception as exc:
                errors.append(f"Failed to delete {rel_path!r}: {exc}")
            continue

        # UNKNOWN OP
        if op != "write":
            errors.append(f"Unknown op={op!r} for path {rel_path!r}")
            continue

        chunks = entry.get("chunks", []) or []
        dest_dir = os.path.dirname(dest_path)
        os.makedirs(dest_dir, exist_ok=True)

        try:
            with open(dest_path, "wb") as out_f:
                for chunk_id in chunks:
                    try:
                        data = load_chunk(target_name, chunk_id)
                    except Exception as exc:
                        raise RuntimeError(f"Failed to load chunk {chunk_id!r}: {exc}")

                    out_f.write(data)
                    written_bytes += len(data)

            written_files += 1
            files_out.append({"logical_path": rel_path, "dest": str(dest_root), "size": None})

        except Exception as exc:
            errors.append(f"Failed to write {rel_path!r}: {exc}")

    success = len(errors) == 0
    result: Dict[str, Any] = {
        "success": success,
        "applied_count": written_files if success else 0,
        "files": files_out if success else files_out,
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

    result = {
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
