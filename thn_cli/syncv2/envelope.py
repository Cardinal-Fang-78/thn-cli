# thn_cli/syncv2/envelope.py

"""
Sync V2 Envelope Loader & Inspector (Hybrid-Standard)
----------------------------------------------------

RESPONSIBILITIES
----------------
This module defines the **canonical envelope-loading boundary** for Sync V2.

It is responsible for:
    • Loading Sync V2 envelope ZIPs from disk or memory
    • Extracting envelope contents into an isolated working directory
    • Parsing manifest.json
    • Providing a normalized, in-memory envelope object
    • Surfacing minimal, deterministic inspection metadata

The envelope object produced here is the **only supported input** for:
    • syncv2.engine.validate_envelope
    • syncv2.engine.apply_envelope_v2
    • syncv2.executor execution planning
    • CLI / GUI / test inspection flows

CONTRACT STATUS
---------------
⚠️ CORE IO BOUNDARY — SEMANTICS LOCKED

Any change to this file may:
    • Break envelope compatibility
    • Invalidate golden tests
    • Affect payload isolation guarantees
    • Leak filesystem state

Changes must preserve:
    • Directory isolation
    • Deterministic extraction
    • Strict required-file enforcement

LIFECYCLE OWNERSHIP
-------------------
The caller owns the lifecycle of the returned envelope object,
including responsibility for cleanup of the extracted work_dir
if retained beyond the current process or inspection flow.

NON-GOALS
---------
• This module does NOT validate manifest semantics
• This module does NOT apply payload contents
• This module does NOT compute routing
• This module does NOT mutate user files

All higher-level behavior belongs to engine, executor, or commands.
"""

from __future__ import annotations

import json
import os
import tempfile
import zipfile
from typing import Any, Dict


def load_envelope_from_file(envelope_zip: str) -> Dict[str, Any]:
    """
    Load a Sync V2 envelope ZIP into a normalized in-memory envelope object.

    NORMALIZED ENVELOPE SHAPE
    -------------------------
    {
        "manifest": dict,          # Parsed manifest.json
        "payload_zip": str,        # Path to extracted payload.zip
        "source_path": str,        # Original envelope zip path
        "work_dir": str,           # Temporary extraction directory
    }

    CONTRACT
    --------
    • Extraction is isolated per-call
    • Caller owns lifecycle of returned object
    • Missing required files is fatal

    NOTE
    ----
    The temporary work_dir created during extraction is NOT
    automatically cleaned up. Callers that retain envelope
    objects beyond immediate inspection or execution are
    responsible for cleanup.
    """
    if not os.path.exists(envelope_zip):
        raise FileNotFoundError(envelope_zip)

    work_dir = tempfile.mkdtemp(prefix="thn-envelope-load-")

    with zipfile.ZipFile(envelope_zip, "r") as z:
        z.extractall(work_dir)

    manifest_path = os.path.join(work_dir, "manifest.json")
    payload_zip_path = os.path.join(work_dir, "payload.zip")

    if not os.path.exists(manifest_path):
        raise ValueError("Envelope missing manifest.json")

    if not os.path.exists(payload_zip_path):
        raise ValueError("Envelope missing payload.zip")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    return {
        "manifest": manifest,
        "payload_zip": payload_zip_path,
        "source_path": envelope_zip,
        "work_dir": work_dir,
    }


def load_envelope_from_bytes(data: bytes) -> Dict[str, Any]:
    """
    Load a Sync V2 envelope from raw ZIP bytes.

    USE CASES
    ---------
    • Future API ingestion
    • GUI drag-and-drop
    • In-memory test harnesses

    CONTRACT
    --------
    • Bytes are written to a temporary file
    • Delegates to load_envelope_from_file()
    """
    fd, path = tempfile.mkstemp(suffix=".thn-envelope.zip")
    os.close(fd)

    with open(path, "wb") as f:
        f.write(data)

    return load_envelope_from_file(path)


def inspect_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inspect a normalized envelope object (NOT a filesystem path).

    RETURNS
    -------
    Deterministic, presentation-safe structure:
        {
            "manifest": dict,
            "has_payload": bool,
            "payload_zip": str | None,
            "source_path": str | None,
            "work_dir": str | None,
        }

    NOTE
    ----
    This function does NOT validate the envelope.
    Validation is handled by syncv2.engine.validate_envelope().
    """
    payload_zip = envelope.get("payload_zip")

    return {
        "manifest": envelope.get("manifest", {}) or {},
        "has_payload": bool(payload_zip and os.path.exists(payload_zip)),
        "payload_zip": payload_zip,
        "source_path": envelope.get("source_path"),
        "work_dir": envelope.get("work_dir"),
    }
