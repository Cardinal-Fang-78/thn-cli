"""
Remote Negotiation Protocol (Hybrid-Standard)
--------------------------------------------

This module implements the capability-negotiation layer for THN Sync V2.

Purpose:
    Before uploading an envelope, the client queries the remote host for
    declared capabilities, supported targets, version information, and
    protocol constraints.

Why this is needed:
    • CDC-delta support may or may not be enabled on the remote host.
    • Different targets may exist remotely.
    • Payload size limits may apply.
    • Signature requirements may vary between deployments.

Protocol (HTTP):

    Request:
        GET <base_url>/sync/negotiation

    Response:
        {
            "success": true,
            "remote_version": "1.0.0",
            "capabilities": {
                "modes": ["raw-zip", "cdc-delta"],
                "max_payload_bytes": 268435456,
                "signature_required": true,
            },
            "targets": ["web", "cli", "docs"]
        }

If the remote does not support negotiation, callers must assume:
    • raw-zip only
    • signature_required = False
    • max_payload_bytes = 32 MB
    • targets = ["web"]

Client Entry Points:
    - negotiate_remote_capabilities(url: str)
    - ensure_mode_supported(capabilities, desired_mode)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Defaults if remote host does not support negotiation
# ---------------------------------------------------------------------------

DEFAULT_NEGOTIATION_FALLBACK = {
    "success": False,
    "remote_version": "unknown",
    "capabilities": {
        "modes": ["raw-zip"],
        "signature_required": False,
        "max_payload_bytes": 32 * 1024 * 1024,  # 32 MB
    },
    "targets": ["web"],
    "error": "Remote host did not provide negotiation endpoint",
}


# ---------------------------------------------------------------------------
# Client: Fetch capabilities from remote
# ---------------------------------------------------------------------------


def negotiate_remote_capabilities(
    base_url: str, timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Query <base_url>/sync/negotiation for full capability metadata.

    Returns a dict:
        {
            "success": bool,
            "remote_version": str,
            "capabilities": { ... },
            "targets": [...],
            "error": optional str
        }

    On any failure, returns DEFAULT_NEGOTIATION_FALLBACK.
    """

    url = base_url.rstrip("/") + "/sync/negotiation"

    req = urllib.request.Request(url=url, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            try:
                obj = json.loads(payload)
            except json.JSONDecodeError:
                return {
                    **DEFAULT_NEGOTIATION_FALLBACK,
                    "error": "Negotiation endpoint returned non-JSON response",
                }

            # Ensure required fields exist
            if not isinstance(obj, dict):
                return {
                    **DEFAULT_NEGOTIATION_FALLBACK,
                    "error": "Negotiation endpoint returned invalid structure",
                }

            # Fill in defaults for missing components
            obj.setdefault("success", True)
            obj.setdefault("remote_version", "unknown")
            obj.setdefault("capabilities", {})
            obj.setdefault("targets", [])

            caps = obj["capabilities"]
            caps.setdefault("modes", ["raw-zip"])
            caps.setdefault("signature_required", False)
            caps.setdefault("max_payload_bytes", 32 * 1024 * 1024)

            return obj

    except Exception:
        return DEFAULT_NEGOTIATION_FALLBACK.copy()


# ---------------------------------------------------------------------------
# Client helpers to validate local intention vs remote capability
# ---------------------------------------------------------------------------


def ensure_mode_supported(
    remote_caps: Dict[str, Any],
    desired_mode: str,
) -> Dict[str, Any]:
    """
    Check whether a desired envelope mode ("raw-zip", "cdc-delta") is
    supported by the remote capabilities dictionary.

    Returns:
        {
            "ok": bool,
            "mode": <desired or downgraded mode>,
            "reason": optional str
        }
    """

    supported = remote_caps.get("modes", ["raw-zip"])

    if desired_mode in supported:
        return {"ok": True, "mode": desired_mode}

    # Remote can't handle CDC — downgrade to raw-zip where possible
    if desired_mode == "cdc-delta" and "raw-zip" in supported:
        return {
            "ok": True,
            "mode": "raw-zip",
            "reason": "Remote does not support CDC-delta; falling back to raw-zip",
        }

    return {
        "ok": False,
        "mode": None,
        "reason": f"Remote host does not support required mode '{desired_mode}'",
    }


# ---------------------------------------------------------------------------
# Server-side helpers (used optionally in remote_server)
# ---------------------------------------------------------------------------


def server_negotiation_payload(
    *,
    modes=("raw-zip", "cdc-delta"),
    signature_required=True,
    max_payload_bytes=256 * 1024 * 1024,
    targets=("web", "cli", "docs"),
    version="1.0.0",
) -> Dict[str, Any]:
    """
    Build a standard negotiation response for remote_server.

    Not required for server operation, but recommended.
    """

    return {
        "success": True,
        "remote_version": version,
        "capabilities": {
            "modes": list(modes),
            "signature_required": bool(signature_required),
            "max_payload_bytes": int(max_payload_bytes),
        },
        "targets": list(targets),
    }
