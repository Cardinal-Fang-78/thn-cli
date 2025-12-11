# thn_cli/syncv2/delta/apply.py

"""
CDC-Delta Apply Engine (Hybrid-Standard)
---------------------------------------

Reconstructs receiver-side files from chunk sequences, as invoked by:

    thn_cli.syncv2.engine.apply_envelope_v2()

This module is intentionally minimal:
    • Writes or deletes files based on manifest entries
    • Reassembles files strictly from chunk IDs via store.load_chunk()
    • Returns a structured, stable result suitable for apply logs,
      UI rendering, status-db entries, and remote responses.

Stage 2 semantics:
    op="write"   → rewrite file from chunk list
    op="delete"  → delete file if present

Future expansion (Stage 3):
    • Partial rehydration
    • Adaptive chunking
    • Chunk-store negotiation
"""

from __future__ import annotations

import os
from typing import Dict, Any, List

from .store import load_chunk


# ---------------------------------------------------------------------------
# CDC-Delta Apply
# ---------------------------------------------------------------------------

def apply_cdc_delta_envelope(
    *,
    envelope: Dict[str, Any],
    payload_zip: Any,   # Reserved for future expansion (metadata bundles)
    dest_root: str,
) -> Dict[str, Any]:
    """
    Apply a CDC-delta envelope to dest_root.

    Envelope shape (as produced by make_delta.py Stage 2):

        {
            "manifest": {
                "version": 2,
                "mode": "cdc-delta",
                "target": "<target>",
                "entries": [
                    {
                        "path": "relative/path.ext",
                        "op": "write" | "delete",
                        "chunks": ["id1", "id2", ...]
                    },
                    ...
                ]
            },
            "payload_zip": None,     (reserved)
            ...
        }

    Returns a stable Hybrid-Standard result shape:

        {
            "success": bool,
            "mode": "cdc-delta",
            "target": str,
            "dest_root": str,
            "file_count": int,
            "written_files": int,
            "written_bytes": int,
            "deleted_files": int,
            "errors": [ ... ]   (only if errors exist)
        }
    """

    manifest = envelope.get("manifest") or {}
    mode = manifest.get("mode", "")

    if mode != "cdc-delta":
        return {
            "success": False,
            "error": f"apply_cdc_delta_envelope called with non-delta mode={mode!r}",
            "mode": mode,
        }

    target_name = manifest.get("target", "unknown")

    entries: List[Dict[str, Any]] = manifest.get("entries", []) or []
    dest_root = os.path.abspath(dest_root)

    written_files = 0
    written_bytes = 0
    deleted_files = 0
    errors: List[str] = []

    for entry in entries:
        op = entry.get("op", "write")
        rel_path = entry.get("path")

        if not rel_path:
            errors.append("Missing 'path' in delta entry.")
            continue

        dest_path = os.path.join(dest_root, rel_path)

        # ----------------------------
        # DELETE OPERATION
        # ----------------------------
        if op == "delete":
            try:
                if os.path.isfile(dest_path):
                    os.remove(dest_path)
                    deleted_files += 1
            except Exception as exc:
                errors.append(f"Failed to delete {rel_path!r}: {exc}")
            continue

        # ----------------------------
        # UNKNOWN OP
        # ----------------------------
        if op != "write":
            errors.append(f"Unknown op={op!r} for path {rel_path!r}")
            continue

        # ----------------------------
        # WRITE OPERATION
        # ----------------------------
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

        except Exception as exc:
            errors.append(f"Failed to write {rel_path!r}: {exc}")

    # -----------------------------------------------------------------------
    # Result assembly
    # -----------------------------------------------------------------------

    success = len(errors) == 0

    result: Dict[str, Any] = {
        "success": success,
        "mode": "cdc-delta",
        "target": target_name,
        "dest_root": dest_root,
        "file_count": len(entries),
        "written_files": written_files,
        "written_bytes": written_bytes,
        "deleted_files": deleted_files,
    }

    if errors:
        result["errors"] = errors

    return result
