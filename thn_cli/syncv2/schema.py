"""
Sync V2 Manifest Schema + Validation (Hybrid-Standard)
-----------------------------------------------------

This module provides minimal but *correct* structural validation for
Sync V2 manifests across ALL envelope types:

    • raw-zip envelopes       (no per-file list)
    • cdc-delta envelopes     (explicit file list + sizes)
    • future structured modes (extensible field set)

This validation layer intentionally does NOT:
    • verify signatures (handled by engine.validate_envelope)
    • validate routing metadata
    • enforce file hashes or chunk integrity

It ONLY ensures the manifest is structurally valid for downstream
engine operations.
"""

from __future__ import annotations

from typing import Any, Dict, List


class ManifestValidationError(Exception):
    """Raised when a manifest fails minimal structural validation."""

    pass


# ---------------------------------------------------------------------------
# Accepted manifest modes
# ---------------------------------------------------------------------------

VALID_MODES = {
    "raw-zip",  # default for envelopes created by make_test_envelope
    "cdc-delta",  # chunked CDC delta manifests
}


# ---------------------------------------------------------------------------
# Validation entry point
# ---------------------------------------------------------------------------


def validate_manifest(manifest: Dict[str, Any]) -> None:
    """
    Validate minimum structural correctness of a Sync V2 manifest.

    Rules (Hybrid-Standard):

        version:
            • MUST equal 2.

        mode:
            • MUST be one of VALID_MODES.
            • If missing, default assumed by engine is "raw-zip"
              but schema requires it to be present.

        raw-zip manifests:
            • MUST include file_count and total_size
            • MUST NOT be required to include "files"

        cdc-delta manifests:
            • MUST include a list under "files"
            • EACH entry MUST contain:
                  path: str
                  size: int >= 0
            • Additional keys allowed (e.g., chunk metadata)

    This validation intentionally does NOT reject extra or unknown fields.
    """

    # ---------------------------------------------------------------
    # 1. Required top-level type
    # ---------------------------------------------------------------
    if not isinstance(manifest, dict):
        raise ManifestValidationError("Manifest must be a dictionary")

    # ---------------------------------------------------------------
    # 2. Version check
    # ---------------------------------------------------------------
    version = manifest.get("version")
    if version != 2:
        raise ManifestValidationError(f"Unsupported manifest version: {version!r} (expected 2)")

    # ---------------------------------------------------------------
    # 3. Mode check
    # ---------------------------------------------------------------
    mode = manifest.get("mode")
    if mode not in VALID_MODES:
        raise ManifestValidationError(
            f"Unsupported manifest mode: {mode!r}. " f"Valid modes: {sorted(VALID_MODES)}"
        )

    # ---------------------------------------------------------------
    # 4. Mode-specific schema
    # ---------------------------------------------------------------
    if mode == "raw-zip":
        _validate_raw_zip_manifest(manifest)
    elif mode == "cdc-delta":
        _validate_cdc_delta_manifest(manifest)

    # All good
    return None


# ---------------------------------------------------------------------------
# RAW-ZIP MANIFEST VALIDATION
# ---------------------------------------------------------------------------


def _validate_raw_zip_manifest(manifest: Dict[str, Any]) -> None:
    """
    raw-zip manifest rules:

        REQUIRED:
            • file_count: int
            • total_size: int

        OPTIONAL:
            • file_hashes: dict[path -> sha256]
            • source_zip: str

        FORBIDDEN:
            • files list is NOT required and often not present
    """

    if "file_count" not in manifest:
        raise ManifestValidationError("raw-zip manifest missing 'file_count'")

    if "total_size" not in manifest:
        raise ManifestValidationError("raw-zip manifest missing 'total_size'")

    fc = manifest["file_count"]
    ts = manifest["total_size"]

    if not isinstance(fc, int) or fc < 0:
        raise ManifestValidationError(f"Invalid file_count: {fc!r}")

    if not isinstance(ts, int) or ts < 0:
        raise ManifestValidationError(f"Invalid total_size: {ts!r}")

    # file_hashes, if present, must be dict[str, str]
    fh = manifest.get("file_hashes", {})
    if fh and not isinstance(fh, dict):
        raise ManifestValidationError("'file_hashes' must be a dict")

    return None


# ---------------------------------------------------------------------------
# CDC-DELTA MANIFEST VALIDATION
# ---------------------------------------------------------------------------


def _validate_cdc_delta_manifest(manifest: Dict[str, Any]) -> None:
    """
    cdc-delta manifest rules:

        REQUIRED:
            • files: list of file entries
              each entry must contain:
                  path: str
                  size: int >= 0

        OPTIONAL:
            • chunk metadata (chunk_ids, sizes, fingerprints, etc.)
            • total_size precomputed (not required)
    """

    files = manifest.get("files")

    if not isinstance(files, list):
        raise ManifestValidationError("cdc-delta manifest must contain 'files' as a list")

    for entry in files:
        if not isinstance(entry, dict):
            raise ManifestValidationError("Each file entry must be a dict")

        path = entry.get("path")
        size = entry.get("size", None)

        if not isinstance(path, str) or not path:
            raise ManifestValidationError(
                "Each file entry must contain 'path' as a non-empty string"
            )

        if not isinstance(size, int) or size < 0:
            raise ManifestValidationError(
                f"File entry for path {path!r} has invalid size: {size!r}"
            )

    return None
