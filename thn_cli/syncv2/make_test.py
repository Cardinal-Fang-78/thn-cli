# thn_cli/syncv2/make_test.py

"""
Sync V2 test-envelope builder (persistent key + Ed25519 signing).

Primary entrypoint:
    make_test_envelope(raw_zip: str) -> dict

Returns:
    {
        "success": bool,
        "envelope_zip": <path or None>,
        "manifest": { ... } | None,
        "file_count": int | None,
        "error": <str | None>,
    }

Envelope layout:

    envelope.zip
    ├── manifest.json
    └── payload.zip

Manifest fields:
    version         Manifest format version (2 = Sync V2)
    mode            "raw-zip"
    source_zip      Absolute path to the original input ZIP
    file_count      Total number of files
    total_size      Aggregate uncompressed size
    file_hashes     SHA256 per file
    signature       Ed25519 signature of the unsigned manifest
    signature_type  Always "ed25519"
    public_key      Signing key’s public hex
"""

from __future__ import annotations

from typing import Dict, Any
import hashlib
import json
import os
import tempfile
import zipfile

from thn_cli.syncv2.keys import sign_manifest


__all__ = [
    "make_test_envelope",
]


# ---------------------------------------------------------------------------
# Internal: payload builder (raw → payload.zip)
# ---------------------------------------------------------------------------

def _build_payload_zip_from_raw(raw_zip: str, payload_zip_path: str) -> Dict[str, Any]:
    """
    Construct payload.zip by copying all files from the provided raw ZIP.
    Computes:

        file_count
        total_size
        file_hashes[name] = sha256 hex

    Directory entries in the raw ZIP are skipped.
    """
    file_count = 0
    total_size = 0
    file_hashes: Dict[str, str] = {}

    with zipfile.ZipFile(raw_zip, "r") as src_z, \
         zipfile.ZipFile(payload_zip_path, "w", zipfile.ZIP_DEFLATED) as dst_z:

        for info in src_z.infolist():
            name = info.filename
            if not name or name.endswith("/"):
                continue  # skip directories

            data = src_z.read(name)
            dst_z.writestr(name, data)

            file_count += 1
            total_size += len(data)

            h = hashlib.sha256()
            h.update(data)
            file_hashes[name] = h.hexdigest()

    return {
        "file_count": file_count,
        "total_size": total_size,
        "file_hashes": file_hashes,
    }


# ---------------------------------------------------------------------------
# Public API: build a signed Sync V2 test envelope
# ---------------------------------------------------------------------------

def make_test_envelope(raw_zip: str) -> Dict[str, Any]:
    """
    Construct a Sync V2-compliant test envelope from a raw ZIP path.

    Steps:
        1. Validate raw_zip exists
        2. Build envelope workspace (temp dir)
        3. Create payload.zip and compute file metadata
        4. Build unsigned manifest
        5. Sign manifest with persistent Ed25519 key
        6. Write manifest.json + payload.zip → final .thn-envelope.zip

    Returns:
        {
            "success": True,
            "envelope_zip": "<path>",
            "manifest": { ... },
            "file_count": N,
        }

        Or on failure:
        {
            "success": False,
            "envelope_zip": None,
            "manifest": None,
            "file_count": None,
            "error": "...",
        }
    """
    if not os.path.exists(raw_zip):
        return {
            "success": False,
            "envelope_zip": None,
            "manifest": None,
            "file_count": None,
            "error": f"raw_zip does not exist: {raw_zip}",
        }

    # Workspace (not deleted so caller can inspect failures)
    envelope_dir = tempfile.mkdtemp(prefix="thn-envelope-")
    manifest_path = os.path.join(envelope_dir, "manifest.json")
    payload_zip_path = os.path.join(envelope_dir, "payload.zip")

    # Build payload.zip + compute file hashes
    payload_info = _build_payload_zip_from_raw(raw_zip, payload_zip_path)

    # Base unsigned manifest
    unsigned_manifest = {
        "version": 2,
        "mode": "raw-zip",
        "source_zip": os.path.abspath(raw_zip),
        "file_count": payload_info["file_count"],
        "total_size": payload_info["total_size"],
        "file_hashes": payload_info["file_hashes"],
    }

    # Sign manifest
    manifest = sign_manifest(unsigned_manifest)

    # Write manifest.json
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Produce final envelope ZIP
    fd, envelope_zip = tempfile.mkstemp(suffix=".thn-envelope.zip")
    os.close(fd)

    with zipfile.ZipFile(envelope_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(manifest_path, "manifest.json")
        z.write(payload_zip_path, "payload.zip")

    return {
        "success": True,
        "envelope_zip": envelope_zip,
        "manifest": manifest,
        "file_count": manifest["file_count"],
    }
