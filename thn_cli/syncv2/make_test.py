# thn_cli/syncv2/make_test.py

"""
Sync V2 Test Envelope Builder (Hybrid-Standard)
-----------------------------------------------

RESPONSIBILITIES
----------------
This module provides a **development and diagnostics-only helper** for
constructing valid Sync V2 envelopes from local filesystem input.

It is responsible for:
    • Building payload.zip from:
        - directories (recursive)
        - single files
        - legacy raw ZIP inputs
    • Computing per-file SHA-256 hashes
    • Producing a valid Sync V2 manifest (raw-zip mode)
    • Applying cryptographic signing to the manifest
    • Emitting a fully-formed envelope ZIP for testing

This helper exists to support:
    • CLI development
    • Golden tests
    • Manual envelope inspection
    • Developer experimentation

CONTRACT STATUS
---------------
⚠️ DEVELOPMENT / DIAGNOSTIC UTILITY

Outputs produced by this module:
    • Are NOT considered stable CLI contracts
    • May evolve without version bumps
    • Must remain compatible with:
        - syncv2.envelope.load_envelope_from_file()
        - syncv2.engine.validate_envelope()

NON-GOALS
---------
• This module does NOT perform routing
• This module does NOT apply envelopes
• This module does NOT generate CDC-delta manifests
• This module does NOT mutate user state outside temp directories

IMPORTANT
---------
The payload MUST NOT include ZIP files to prevent recursive hashing
and ambiguous envelope semantics.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from typing import Any, Dict

from thn_cli.syncv2.keys import sign_manifest

__all__ = ["make_test_envelope"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _hash_and_write_file(
    z: zipfile.ZipFile,
    abs_path: str,
    rel_path: str,
    file_hashes: Dict[str, str],
) -> int:
    """
    Read a file, write it into payload.zip, and record its SHA-256 hash.

    CONTRACT
    --------
    • Deterministic hashing
    • Full-file read (test utility only)
    • rel_path is used verbatim inside payload.zip
    """
    with open(abs_path, "rb") as f:
        data = f.read()

    z.writestr(rel_path, data)

    h = hashlib.sha256()
    h.update(data)
    file_hashes[rel_path] = h.hexdigest()

    return len(data)


def _build_payload_from_directory(
    root: str,
    payload_zip_path: str,
) -> Dict[str, Any]:
    """
    Build payload.zip from a directory tree.

    Guarantees:
        • Recursive traversal
        • Deterministic file inclusion
        • ZIP files are excluded
    """
    file_count = 0
    total_size = 0
    file_hashes: Dict[str, str] = {}

    with zipfile.ZipFile(payload_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(root):
            for name in files:
                if name.lower().endswith(".zip"):
                    continue

                abs_path = os.path.join(base, name)
                rel_path = os.path.relpath(abs_path, root)

                size = _hash_and_write_file(z, abs_path, rel_path, file_hashes)
                file_count += 1
                total_size += size

    return {
        "file_count": file_count,
        "total_size": total_size,
        "file_hashes": file_hashes,
    }


def _build_payload_from_file(
    path: str,
    payload_zip_path: str,
) -> Dict[str, Any]:
    """
    Build payload.zip from a single file.

    CONTRACT
    --------
    • ZIP files are explicitly rejected
    • Payload will contain exactly one entry
    """
    file_hashes: Dict[str, str] = {}
    name = os.path.basename(path)

    if name.lower().endswith(".zip"):
        raise ValueError("ZIP files are not allowed as direct payload entries")

    with zipfile.ZipFile(payload_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        size = _hash_and_write_file(z, path, name, file_hashes)

    return {
        "file_count": 1,
        "total_size": size,
        "file_hashes": file_hashes,
    }


def _build_payload_from_zip(
    raw_zip: str,
    payload_zip_path: str,
) -> Dict[str, Any]:
    """
    Repackage a legacy ZIP into payload.zip.

    CONTRACT
    --------
    • ZIP entries are flattened verbatim
    • Nested ZIP files are excluded
    • Hashes are recomputed
    """
    file_count = 0
    total_size = 0
    file_hashes: Dict[str, str] = {}

    with (
        zipfile.ZipFile(raw_zip, "r") as src,
        zipfile.ZipFile(payload_zip_path, "w", zipfile.ZIP_DEFLATED) as dst,
    ):
        for info in src.infolist():
            name = info.filename
            if not name or name.endswith("/") or name.lower().endswith(".zip"):
                continue

            data = src.read(name)
            dst.writestr(name, data)

            h = hashlib.sha256()
            h.update(data)
            file_hashes[name] = h.hexdigest()

            file_count += 1
            total_size += len(data)

    return {
        "file_count": file_count,
        "total_size": total_size,
        "file_hashes": file_hashes,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def make_test_envelope(input_path: str) -> Dict[str, Any]:
    """
    Build a signed Sync V2 test envelope from a local input path.

    CONTRACT
    --------
    • Input may be a directory, file, or ZIP
    • Output is a valid raw-zip Sync V2 envelope
    • All artifacts are written to temporary locations
    • Caller owns lifecycle of returned envelope_zip
    """
    if not os.path.exists(input_path):
        return {
            "success": False,
            "envelope_zip": None,
            "manifest": None,
            "file_count": None,
            "error": f"Input does not exist: {input_path}",
        }

    envelope_dir = tempfile.mkdtemp(prefix="thn-envelope-")
    manifest_path = os.path.join(envelope_dir, "manifest.json")
    payload_zip_path = os.path.join(envelope_dir, "payload.zip")

    # ------------------------------------------------------------------
    # Build payload
    # ------------------------------------------------------------------

    if os.path.isdir(input_path):
        payload_info = _build_payload_from_directory(input_path, payload_zip_path)
    elif zipfile.is_zipfile(input_path):
        payload_info = _build_payload_from_zip(input_path, payload_zip_path)
    else:
        payload_info = _build_payload_from_file(input_path, payload_zip_path)

    # ------------------------------------------------------------------
    # Manifest (raw-zip mode)
    # ------------------------------------------------------------------

    unsigned_manifest = {
        "version": 2,
        "mode": "raw-zip",
        "source": os.path.abspath(input_path),
        "file_count": payload_info["file_count"],
        "total_size": payload_info["total_size"],
        "file_hashes": payload_info["file_hashes"],
    }

    manifest = sign_manifest(unsigned_manifest)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

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
