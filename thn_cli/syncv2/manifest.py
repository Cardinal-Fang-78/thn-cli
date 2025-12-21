"""
Sync V2 Manifest Helpers (Hybrid-Standard)
-----------------------------------------

RESPONSIBILITIES
----------------
This module provides **presentation-safe helpers** for Sync V2 manifests.

It is responsible for:
    • Producing consistent, minimal, deterministic summaries for CLI/UI
    • Normalizing CDC file metadata into stable shapes
    • Providing bounded, non-throwing projections for diagnostics
    • Ensuring future-safe manifest behavior across:
          - raw-zip envelopes
          - CDC-delta envelopes
          - mixed / legacy manifests
          - future multi-module routing

This module intentionally operates on **already-parsed manifest dictionaries**
and never performs I/O.

AUTHORITY BOUNDARY
------------------
This module is **non-authoritative**.

It must NOT:
    • Validate schema correctness
    • Enforce routing rules
    • Verify signatures
    • Perform size or hash validation
    • Raise on malformed input

Authoritative enforcement is handled by:
    thn_cli.syncv2.engine.validate_envelope()

CONTRACT STATUS
---------------
⚠️ LOCKED OUTPUT SURFACE (CLI / GOLDEN / GUI CONTRACT)

The outputs produced by:
    • summarize_manifest()
    • summarize_cdc_files()

are considered **externally visible contracts**.

Any change to:
    • returned keys
    • key names
    • value semantics
    • default or fallback behavior

MUST be accompanied by:
    • updated golden tests
    • OR an explicit versioned surface change

NON-GOALS
---------
• This module does NOT validate signatures or schema compliance.
• This module does NOT perform I/O.
• This module does NOT enforce routing policy.
• This module does NOT compute execution plans.

It exists purely as a **safe projection layer** for higher-level tooling.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Summary Helpers
# ---------------------------------------------------------------------------


def summarize_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a normalized summary of a Sync V2 manifest.

    CONTRACT
    --------
    ⚠️ LOCKED SUMMARY SURFACE

    Returned keys and semantics are golden-tested and relied upon by:
        • thn sync inspect
        • downstream CLI tooling
        • future GUI consumers

    Behavior:
        • Never throws
        • Tolerates missing or malformed fields
        • Uses conservative defaults

    Works for:
        • raw-zip manifests (files not listed explicitly)
        • CDC-delta manifests (files listed with sizes)
        • legacy manifests (partial fields)

    Keys returned:
        version: int | None
        mode: str
        file_count: int
        total_size: int
        meta: dict
    """
    mode = manifest.get("mode", "raw-zip")

    # CDC-delta manifests explicitly list files under manifest["files"]
    if mode == "cdc-delta":
        files = manifest.get("files", []) or []
        total_size = 0
        for f in files:
            try:
                total_size += int((f or {}).get("size", 0))
            except Exception:
                # Size errors are tolerated and treated as zero
                total_size += 0

        return {
            "version": manifest.get("version"),
            "mode": mode,
            "file_count": len(files),
            "total_size": total_size,
            "meta": manifest.get("meta", {}) or {},
        }

    # raw-zip (and unknown modes): rely on aggregate fields if present
    file_count = manifest.get("file_count")
    total_size = manifest.get("total_size")

    return {
        "version": manifest.get("version"),
        "mode": mode,
        "file_count": int(file_count) if file_count is not None else 0,
        "total_size": int(total_size) if total_size is not None else 0,
        "meta": manifest.get("meta", {}) or {},
    }


# ---------------------------------------------------------------------------
# CDC File Listing Helpers
# ---------------------------------------------------------------------------


def _normalize_file_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single CDC file entry into a stable presentation shape.

    CONTRACT
    --------
    • Presentation-only
    • MUST NOT throw
    • MUST NOT validate schema
    • MUST tolerate malformed input

    This function exists to provide a **safe UI/CLI-facing projection**
    even when manifests are partially invalid.
    """
    name = entry.get("name") or entry.get("path") or entry.get("relpath")
    size = entry.get("size")
    sha256 = entry.get("sha256") or entry.get("hash") or entry.get("content_sha256")

    try:
        size_i: Optional[int] = int(size) if size is not None else None
    except Exception:
        size_i = None

    return {
        "name": str(name) if name is not None else None,
        "size": size_i,
        "sha256": str(sha256) if sha256 is not None else None,
    }


def summarize_cdc_files(
    manifest: Dict[str, Any],
    *,
    max_items: int = 200,
) -> Dict[str, Any]:
    """
    If the manifest is CDC-delta, return a safe, bounded file listing summary.

    CONTRACT
    --------
    ⚠️ LOCKED CDC FILE LISTING SURFACE

    This output is:
        • Golden-tested
        • CLI-consumed
        • GUI-ready
        • Deterministic

    Guarantees:
        • Deterministic ordering (manifest order)
        • Bounded output size
        • No exceptions on malformed entries

    Returns:
        {
            "present": bool,
            "count": int,
            "truncated": bool,
            "files": [
                { "name": str|None, "size": int|None, "sha256": str|None },
                ...
            ],
        }
    """
    mode = manifest.get("mode", "raw-zip")
    if mode != "cdc-delta":
        return {
            "present": False,
            "count": 0,
            "truncated": False,
            "files": [],
        }

    files = manifest.get("files", []) or []
    normalized: List[Dict[str, Any]] = []

    for entry in files[:max_items]:
        if isinstance(entry, dict):
            normalized.append(_normalize_file_entry(entry))
        else:
            # Preserve odd shapes without throwing
            normalized.append({"name": None, "size": None, "sha256": None})

    return {
        "present": True,
        "count": len(files),
        "truncated": len(files) > max_items,
        "files": normalized,
    }


# ---------------------------------------------------------------------------
# Per-File Metadata Normalization (Routing Tags)
# ---------------------------------------------------------------------------


def derive_tags_for_file(file_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize per-file routing metadata into a guaranteed shape.

    CONTRACT
    --------
    Ensures these keys ALWAYS exist for downstream consumers:
        project: str | None
        module: str | None
        category: str | None
        tags: list[str]

    Notes:
        • CDC-delta manifests typically do NOT include per-file routing
        • Routing is computed at envelope level and applied uniformly
        • This function must never throw
    """
    return {
        "project": file_entry.get("project"),
        "module": file_entry.get("module"),
        "category": file_entry.get("category"),
        "tags": list(file_entry.get("tags", [])),
    }
