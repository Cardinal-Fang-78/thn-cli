# thn_cli/syncv2/delta/remote_chunk_index.py

"""
Remote Chunk Index Negotiation (Hybrid-Standard)
===============================================

Purpose
-------
This module provides the foundation for *remote* CDC-delta optimization:

    • Before sending a large CDC delta envelope, the client queries the remote
      host for which chunks it already possesses.
    • The client then omits redundant chunks, sends only missing ones, and
      updates the delta manifest accordingly.
    • The remote server records newly received chunks and applies the now-
      minimized delta.

This dramatically reduces bandwidth for:
    - large binary assets
    - repeated syncs of similar content
    - slowly evolving datasets (logs, documents, blobs)

Protocol (High-Level)
---------------------
Client:
    1. Collect all chunk IDs in the delta manifest.
    2. POST a JSON body to:
           <server>/sync/chunks/has
       with:
           { "target": "<str>", "chunks": ["<id1>", "<id2>", ...] }

Server:
    Responds:
           { "has": [...], "missing": [...] }

Client:
    Uploads only missing chunks to:
           <server>/sync/chunks/put
       using a binary POST.

The module does not enforce HTTP specifics — that is handled by the
Remote Sync Server extension. This module defines the *algorithmic
contract* and *client-side helpers*.

This file is imported by:
    • make_delta.py (optional optimization)
    • remote_client.py (for future advanced bundles)
    • remote_negotiation.py (Hybrid-Standard placeholder)

Dependencies:
    • No local state required.
    • No chunk store access here — remote host determines that.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Public API – client-side functions
# ---------------------------------------------------------------------------


def query_remote_chunk_index(
    *,
    url: str,
    target: str,
    chunk_ids: List[str],
    timeout: float = 20.0,
) -> Dict[str, Any]:
    """
    Query the remote endpoint for which chunks it already has.

    Request (POST <url>/sync/chunks/has):
        {
            "target": "<target_name>",
            "chunks": ["<chunk_id>", ...]
        }

    Response:
        {
            "success": true/false,
            "has": [...],
            "missing": [...],
            "error": <optional>
        }

    The result structure is normalized to always contain keys:
        has: list[str]
        missing: list[str]
        success: bool
    """
    payload = json.dumps(
        {
            "target": target,
            "chunks": chunk_ids,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url=f"{url}/sync/chunks/has",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(text)
                return {
                    "success": bool(data.get("success", False)),
                    "has": data.get("has", []),
                    "missing": data.get("missing", []),
                    "error": data.get("error"),
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "has": [],
                    "missing": [],
                    "error": "Non-JSON response from remote host",
                }

    except urllib.error.HTTPError as exc:
        return {
            "success": False,
            "has": [],
            "missing": [],
            "error": f"HTTPError: {exc}",
        }

    except Exception as exc:
        return {
            "success": False,
            "has": [],
            "missing": [],
            "error": f"Network error: {exc}",
        }


def upload_missing_chunk(
    *,
    url: str,
    target: str,
    chunk_id: str,
    data: bytes,
    timeout: float = 20.0,
) -> Dict[str, Any]:
    """
    Upload a single missing chunk to the remote host.

    Request:
        POST <url>/sync/chunks/put
        Headers:
            X-THN-Target: <target>
            X-THN-Chunk-ID: <chunk_id>
        Body:
            raw bytes of the chunk

    Response:
        { "success": true } or { "success": false, "error": ... }
    """

    headers = {
        "Content-Type": "application/octet-stream",
        "X-THN-Target": target,
        "X-THN-Chunk-ID": chunk_id,
    }

    req = urllib.request.Request(
        url=f"{url}/sync/chunks/put",
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Remote returned non-JSON response",
                }
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
            return json.loads(body)
        except Exception:
            return {
                "success": False,
                "error": f"HTTPError: {exc}",
            }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Network error: {exc}",
        }


# ---------------------------------------------------------------------------
# Utility: normalize negotiation result
# ---------------------------------------------------------------------------


def partition_chunks(
    *,
    chunk_ids: List[str],
    remote_has: List[str],
) -> Dict[str, List[str]]:
    """
    Given a full local list of chunk IDs and a remote 'has' list,
    compute:
        - chunks to upload
        - chunks already present

    Returns:
        {
            "missing": [...],
            "present": [...],
        }
    """
    remote_set = set(remote_has)
    missing = []
    present = []

    for cid in chunk_ids:
        if cid in remote_set:
            present.append(cid)
        else:
            missing.append(cid)

    return {
        "missing": missing,
        "present": present,
    }
