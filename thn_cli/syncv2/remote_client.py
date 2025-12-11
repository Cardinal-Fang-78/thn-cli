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
    • Maintain compatibility with existing Sync V2 engine outputs.

Protocol (THN Remote Sync Standard):
    Request:
        POST <url>
        Headers:
            Content-Type: application/octet-stream
            X-THN-Target: <target_name>
            X-THN-Dry-Run: "1" | "0"
        Body:
            Raw bytes of the envelope ZIP.

    Success Response (HTTP 200):
        JSON body identical to engine.apply_envelope_v2 return.

    Failure Response:
        - JSON error (preferred)
        - non-JSON text → wrapped synthetic error object
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import urllib.request
import urllib.error


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_envelope_to_remote(
    envelope_zip: str,
    target_name: str,
    url: str,
    dry_run: bool,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Send the given envelope ZIP to a remote Sync endpoint.

    Always returns a dict:
        {
            "success": bool,
            "error": <str | None>,
            "details": <dict | None>,
            ...
        }

    • No exceptions propagate outward.
    • Fully Hybrid-Standard normalized return structure.
    """

    # -------------------------------------------------------------------
    # Validate input
    # -------------------------------------------------------------------
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

    # -------------------------------------------------------------------
    # Prepare HTTP request
    # -------------------------------------------------------------------
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

    # -------------------------------------------------------------------
    # Perform request
    # -------------------------------------------------------------------
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")

            # Try JSON
            try:
                payload = json.loads(text)
                if not isinstance(payload, dict):
                    raise ValueError
                payload.setdefault("success", True)
                return payload
            except Exception:
                # Non-JSON response
                return {
                    "success": False,
                    "error": "Remote returned non-JSON response",
                    "details": {
                        "raw_response": text[:2000],
                        "status": resp.status,
                    },
                }

    # -------------------------------------------------------------------
    # HTTP error
    # -------------------------------------------------------------------
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

            # JSON failed → plain-text error fallback
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

    # -------------------------------------------------------------------
    # URL errors (unreachable host, connection refused, DNS failure, etc.)
    # -------------------------------------------------------------------
    except urllib.error.URLError as exc:
        return {
            "success": False,
            "error": "Failed to reach remote endpoint",
            "details": {"reason": str(exc)},
        }

    # -------------------------------------------------------------------
    # Unexpected client-side exception
    # -------------------------------------------------------------------
    except Exception as exc:
        return {
            "success": False,
            "error": "Unexpected error during remote sync",
            "details": {"exception": str(exc)},
        }
