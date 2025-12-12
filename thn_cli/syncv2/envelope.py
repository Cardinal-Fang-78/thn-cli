"""
Envelope Loader & Inspector (Hybrid-Standard)
=============================================

Responsibilities:

    • Load envelope ZIPs from bytes or file paths.
    • Parse manifest.json.
    • Extract in-memory payload files.
    • Provide a structured inspection report.

This module does *not* apply envelopes.  All application logic belongs
exclusively to `syncv2.engine.apply_envelope_v2()`.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_manifest_from_zip(zf: zipfile.ZipFile) -> Dict[str, Any]:
    """Load and decode manifest.json from an opened ZIP."""
    try:
        raw = zf.read("manifest.json")
    except KeyError:
        raise ValueError("Envelope ZIP missing required 'manifest.json'")

    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to decode manifest.json: {exc}") from exc


def _extract_payload_files(zf: zipfile.ZipFile) -> Dict[str, bytes]:
    """
    Extract in-memory payload files from ZIP:

        payload/<relative-path>

    Returns: { "relative/path.ext": b"<bytes>" }
    """
    files: Dict[str, bytes] = {}
    for name in zf.namelist():
        if name.startswith("payload/") and not name.endswith("/"):
            rel = name[len("payload/") :]
            try:
                files[rel] = zf.read(name)
            except Exception as exc:
                raise ValueError(f"Failed to read payload entry '{name}': {exc}")
    return files


# ---------------------------------------------------------------------------
# Envelope Loading
# ---------------------------------------------------------------------------


def load_envelope_from_bytes(data: bytes) -> Dict[str, Any]:
    """
    Load an envelope from a serialized ZIP (bytes).

    Returns:
        {
            "manifest": {...},
            "files": {...},
            "source_zip": None,
            "payload_zip": None      # Provided by callers when needed
        }
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(data), "r")
    except Exception as exc:
        raise ValueError(f"Failed to open envelope ZIP bytes: {exc}")

    manifest = _load_manifest_from_zip(zf)
    files = _extract_payload_files(zf)

    return {
        "manifest": manifest,
        "files": files,
        "source_zip": None,
        "payload_zip": None,
    }


def load_envelope_from_file(zip_path: str) -> Dict[str, Any]:
    """
    Load an envelope from a ZIP file on disk.

    Returns:
        {
            "manifest": {...},
            "files": {...},
            "source_zip": <zip_path>,
            "payload_zip": <zip_path>
        }
    """
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Envelope file not found: {zip_path}")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            manifest = _load_manifest_from_zip(zf)
            files = _extract_payload_files(zf)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Invalid ZIP file: {zip_path} ({exc})")
    except Exception:
        raise

    return {
        "manifest": manifest,
        "files": files,
        "source_zip": zip_path,
        "payload_zip": zip_path,  # used by apply engine
    }


# ---------------------------------------------------------------------------
# Envelope Inspection (Non-Mutating)
# ---------------------------------------------------------------------------


def inspect_envelope(env: Dict[str, Any]) -> str:
    """
    Return a JSON-formatted diagnostic describing the envelope contents.

    Suitable for CLI output.

    Includes:
        • source_zip
        • manifest fields
        • count of payload files
        • sorted list of payload paths
    """
    manifest = env.get("manifest", {})

    info = {
        "source_zip": env.get("source_zip"),
        "manifest": manifest,
        "file_count": len(env.get("files", {})),
        "files": sorted(env.get("files", {}).keys()),
    }

    return json.dumps(info, indent=4)
