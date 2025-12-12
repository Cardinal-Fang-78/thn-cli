# thn_cli/syncv2/remote_server.py

"""
THN Sync V2 Remote Server (Hybrid-Standard)
------------------------------------------

Exposes an HTTP endpoint for receiving fully-formed Sync V2 envelopes
and applying them using the unified Sync V2 engine.

Endpoint:
    POST /sync/apply

Required Headers:
    X-THN-Target:   "web" | "cli" | "docs"
    X-THN-Dry-Run:  "1" | "0"

Body:
    Raw envelope ZIP bytes.

Response:
    • Always JSON, always Hybrid-Standard shaped.
    • success: bool
    • error: str | None
    • details: dict | None
    • For success == True: engine.apply_envelope_v2(...) payload is returned.

Server startup:
    python -m thn_cli.syncv2.remote_server
"""

from __future__ import annotations

import json
import os
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Type

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.envelope import load_envelope_from_file
from thn_cli.syncv2.targets.cli import CliSyncTarget
from thn_cli.syncv2.targets.docs import DocsSyncTarget
from thn_cli.syncv2.targets.web import WebSyncTarget

# ---------------------------------------------------------------------------
# Target mapping (extendable)
# ---------------------------------------------------------------------------

TARGET_MAP = {
    "web": WebSyncTarget,
    "cli": CliSyncTarget,
    "docs": DocsSyncTarget,
}


# ---------------------------------------------------------------------------
# Request Handler
# ---------------------------------------------------------------------------


class SyncRequestHandler(BaseHTTPRequestHandler):
    server_version = "THNRemoteSync/2.0"

    # -------------------------------------------------------
    # Utilities
    # -------------------------------------------------------

    def _json_response(self, status_code: int, payload: Dict[str, Any]) -> None:
        """
        Send a JSON response (always Hybrid-Standard compliant).
        """
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        """
        Lightweight server-side log.
        """
        print(f"[RemoteSync] {self.address_string()} - {fmt % args}")

    # -------------------------------------------------------
    # HTTP POST
    # -------------------------------------------------------

    def do_POST(self) -> None:
        # Validate endpoint
        if self.path != "/sync/apply":
            self._json_response(
                404,
                {
                    "success": False,
                    "error": "Not found",
                    "details": {"path": self.path},
                },
            )
            return

        # Validate headers
        target_name = self.headers.get("X-THN-Target")
        dry_run_header = self.headers.get("X-THN-Dry-Run", "0")

        if not target_name or target_name not in TARGET_MAP:
            self._json_response(
                400,
                {
                    "success": False,
                    "error": "Missing or invalid X-THN-Target header",
                    "details": {"received": target_name},
                },
            )
            return

        dry_run = dry_run_header == "1"

        # Validate body length
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json_response(
                400,
                {
                    "success": False,
                    "error": "Invalid Content-Length header",
                    "details": {"raw": self.headers.get("Content-Length")},
                },
            )
            return

        if length <= 0:
            self._json_response(
                400,
                {
                    "success": False,
                    "error": "Request body is empty",
                },
            )
            return

        # Read request body
        try:
            body = self.rfile.read(length)
        except Exception as exc:
            self._json_response(
                500,
                {
                    "success": False,
                    "error": "Failed to read request body",
                    "details": {"exception": str(exc)},
                },
            )
            return

        # -------------------------------------------------------
        # Persist envelope temporarily
        # -------------------------------------------------------
        try:
            fd, envelope_zip = tempfile.mkstemp(suffix=".thn-envelope.zip")
            os.close(fd)
            with open(envelope_zip, "wb") as f:
                f.write(body)
        except Exception as exc:
            self._json_response(
                500,
                {
                    "success": False,
                    "error": "Failed to persist envelope to temporary storage",
                    "details": {"exception": str(exc)},
                },
            )
            return

        # -------------------------------------------------------
        # Load envelope
        # -------------------------------------------------------
        try:
            envelope = load_envelope_from_file(envelope_zip)
        except Exception as exc:
            os.remove(envelope_zip)
            self._json_response(
                400,
                {
                    "success": False,
                    "error": "Failed to load envelope",
                    "details": {"exception": str(exc)},
                },
            )
            return

        # -------------------------------------------------------
        # Apply envelope to target
        # -------------------------------------------------------
        try:
            target_cls: Type = TARGET_MAP[target_name]
            target = target_cls()
            result = apply_envelope_v2(envelope, target, dry_run=dry_run)

            # Guarantee Hybrid-Standard shape
            if not isinstance(result, dict):
                result = {
                    "success": False,
                    "error": "Target returned non-dict response",
                    "details": {"type": type(result).__name__},
                }

        except Exception as exc:
            result = {
                "success": False,
                "error": "Unhandled exception during apply",
                "details": {"exception": str(exc)},
            }

        finally:
            if os.path.exists(envelope_zip):
                try:
                    os.remove(envelope_zip)
                except Exception:
                    pass  # Non-fatal

        # -------------------------------------------------------
        # Emit response
        # -------------------------------------------------------
        status = 200 if result.get("success") else 500
        self._json_response(status, result)


# ---------------------------------------------------------------------------
# Server bootstrap
# ---------------------------------------------------------------------------


def run_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    """
    Launch the THN Remote Sync server.

    This is intentionally minimal: production deployments should
    wrap with a WSGI, reverse proxy, or container supervisor.
    """
    server_address = (host, port)
    httpd = HTTPServer(server_address, SyncRequestHandler)
    print(f"THN Remote Sync Server (Hybrid-Standard) listening on {host}:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down THN Remote Sync server...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
