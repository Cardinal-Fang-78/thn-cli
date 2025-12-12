# thn_cli/syncv2/validation.py

"""
Hybrid-Standard Envelope Validation (Sync V2)
---------------------------------------------

Responsibilities:
    • Validate a Sync V2 manifest + payload ZIP.
    • Verify Ed25519 signatures.
    • Verify per-file SHA256 (raw-zip mode only).
    • Compute overall payload hash.
    • Provide a consistent return structure:

        {
            "valid": bool,
            "errors": [str, ...],
            "hash": "<sha256-of-payload>" | None
        }

This module performs *static* validation only:
    - No filesystem writes.
    - No target inspection.
    - No delta application.

Engine-level dispatch is performed in:
    thn_cli.syncv2.engine.validate_envelope
"""

from __future__ import annotations

import hashlib
import zipfile
from typing import Any, Dict, List, Optional

from thn_cli.syncv2.keys import verify_manifest_signature

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_raw_zip_manifest(manifest: Dict[str, Any], payload_zip: str) -> List[str]:
    """
    Validate per-file SHA256 for raw-zip mode, if file_hashes exist.
    Returns list of error strings.
    """
    errors: List[str] = []
    expected = manifest.get("file_hashes", {})

    if not expected:
        return errors  # nothing further to check

    try:
        with zipfile.ZipFile(payload_zip, "r") as zf:
            computed = {}
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                with zf.open(name) as f:
                    h = hashlib.sha256()
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                    computed[name] = h.hexdigest()

        for name, exp_hash in expected.items():
            act = computed.get(name)
            if act != exp_hash:
                errors.append(f"File hash mismatch: {name}")
    except Exception as exc:
        errors.append(f"Failed to verify per-file hashes: {exc}")

    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_envelope(manifest: Dict[str, Any], payload_path: str) -> Dict[str, Any]:
    """
    Validate a Sync V2 envelope (manifest + payload.zip).

    Returns:
        {
            "valid": bool,
            "errors": [...],
            "hash": "<sha256>" | None
        }
    """
    errors: List[str] = []

    # --- Signature verification --------------------------------------------
    sig_errors = verify_manifest_signature(manifest)
    errors.extend(sig_errors)

    # --- Payload hash -------------------------------------------------------
    try:
        payload_hash = _sha256_of_file(payload_path)
    except Exception as exc:
        errors.append(f"Failed to compute payload SHA-256: {exc}")
        return {
            "valid": False,
            "errors": errors,
            "hash": None,
        }

    # --- Mode-specific validation ------------------------------------------
    mode = manifest.get("mode", "raw-zip")

    if mode == "raw-zip":
        errors.extend(_validate_raw_zip_manifest(manifest, payload_path))

    elif mode == "cdc-delta":
        # CDC manifests validated mostly during apply; only signature required here.
        pass

    else:
        # Unknown modes are *allowed* but produce a warning.
        errors.append(f"Unknown manifest mode: {mode}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "hash": payload_hash,
    }
