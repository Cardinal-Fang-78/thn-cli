# thn_cli/syncv2/remote_client.py

"""
Sync V2 Remote Client (Hybrid-Standard)
--------------------------------------

Responsibilities:
    • Send a fully-formed Sync V2 envelope ZIP to a remote HTTP endpoint.
    • Provide strict, predictable error handling (never raise outward).
    • Normalize response handling:
          - Always return a dict with `success: bool`.
          - Attempt JSON decode; fall back to raw text.
          - Surface HTTP and URL errors in stable form.
    • Maintain compatibility with Sync V2 engine outputs.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Public API — real remote-send implementation
# ---------------------------------------------------------------------------


def send_envelope_to_remote(
    envelope_zip: str,
    target_name: str,
    url: str,
    dry_run: bool,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    if not os.path.exists(envelope_zip):
        return {
            "success": False,
            "error": "Envelope ZIP does not exist",
            "details": {"path": envelope_zip},
        }

    try:
        with open(envelope_zip, "rb") as f:
            data = f.read()
    except Exception as exc:
        return {
            "success": False,
            "error": "Failed to read envelope ZIP",
            "details": {"exception": str(exc)},
        }

    headers = {
        "Content-Type": "application/octet-stream",
        "X-THN-Target": target_name,
        "X-THN-Dry-Run": "1" if dry_run else "0",
    }

    req = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")

            try:
                payload = json.loads(text)
                if isinstance(payload, dict):
                    payload.setdefault("success", True)
                    return payload
            except Exception:
                pass

            return {
                "success": False,
                "error": "Remote returned non-JSON response",
                "details": {
                    "raw_response": text[:2000],
                    "status": resp.status,
                },
            }

    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(body)
                if isinstance(payload, dict):
                    payload.setdefault("success", False)
                    payload.setdefault("error", "Remote HTTP error")
                    payload.setdefault("status", exc.code)
                    return payload
            except Exception:
                pass

            return {
                "success": False,
                "error": "Remote HTTP error",
                "details": {
                    "status": exc.code,
                    "reason": str(exc),
                    "raw_response": body[:2000],
                },
            }

        except Exception as sub_exc:
            return {
                "success": False,
                "error": "HTTP error with unreadable body",
                "details": {"exception": str(sub_exc), "status": exc.code},
            }

    except urllib.error.URLError as exc:
        return {
            "success": False,
            "error": "Failed to reach remote endpoint",
            "details": {"reason": str(exc)},
        }

    except Exception as exc:
        return {
            "success": False,
            "error": "Unexpected error during remote sync",
            "details": {"exception": str(exc)},
        }


# ---------------------------------------------------------------------------
# Compatibility Shims (prevent ImportErrors in commands_sync_remote)
# ---------------------------------------------------------------------------


def negotiate_remote_cdc(remote_url: str, capabilities: dict | None = None) -> dict:
    return {
        "status": "ok",
        "url": remote_url,
        "capabilities": capabilities or {},
        "message": "CDC negotiation not implemented",
    }


def upload_missing_chunk(remote_url: str, chunk_id: str, data: bytes) -> dict:
    return {
        "status": "ok",
        "chunk_id": chunk_id,
        "size": len(data),
        "message": "Remote chunk upload not implemented",
    }


def remote_apply_envelope(remote_url: str, envelope_bytes: bytes) -> dict:
    return {
        "status": "ok",
        "bytes_received": len(envelope_bytes),
        "message": "Remote envelope apply not implemented",
    }
