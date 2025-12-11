"""
Sync V2 Manifest Helpers (Hybrid-Standard)
-----------------------------------------

Responsibilities:
    • Provide consistent, minimal, and predictable summaries for CLI/UI.
    • Normalize per-file metadata (tags, project/module/category).
    • Guarantee future-safe manifest behavior across:
          - raw-zip envelopes
          - CDC-delta envelopes
          - multi-module routing
    • Avoid assumptions about the presence of advanced fields.

This module does NOT validate signatures or schema compliance.
Validation is handled by:
    thn_cli.syncv2.engine.validate_envelope
"""

from __future__ import annotations

from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Summary Helpers
# ---------------------------------------------------------------------------

def summarize_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a normalized summary of a Sync V2 manifest.

    Works for:
        • raw-zip manifests (files not listed explicitly)
        • CDC-delta manifests (files listed with sizes)
        • legacy manifests (fallbacks)

    Keys returned:
        version: int
        mode: str
        file_count: int
        total_size: int
        meta: dict
    """

    mode = manifest.get("mode", "raw-zip")

    # CDC manifests explicitly list files under manifest["files"].
    if mode == "cdc-delta":
        files = manifest.get("files", [])
        total_size = sum(int(f.get("size", 0)) for f in files)
        return {
            "version": manifest.get("version"),
            "mode": mode,
            "file_count": len(files),
            "total_size": total_size,
            "meta": manifest.get("meta", {}),
        }

    # raw-zip manifests store a file_count + total_size summary directly
    file_count = manifest.get("file_count")
    total_size = manifest.get("total_size")

    return {
        "version": manifest.get("version"),
        "mode": mode,
        "file_count": int(file_count) if file_count is not None else 0,
        "total_size": int(total_size) if total_size is not None else 0,
        "meta": manifest.get("meta", {}),
    }


# ---------------------------------------------------------------------------
# Per-File Metadata Normalization
# ---------------------------------------------------------------------------

def derive_tags_for_file(file_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize per-file metadata.

    Ensures these keys ALWAYS exist for downstream routing:
        project: str | None
        module: str | None
        category: str | None
        tags: list[str]

    CDC-delta manifests may not provide routing metadata per file;
    routing is computed at envelope level and applied uniformly.
    """

    return {
        "project": file_entry.get("project"),
        "module": file_entry.get("module"),
        "category": file_entry.get("category"),
        "tags": list(file_entry.get("tags", [])),
    }
