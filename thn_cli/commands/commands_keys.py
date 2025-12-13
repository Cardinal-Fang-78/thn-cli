"""
THN Keys Management (Hybrid-Standard)
------------------------------------

Manages Ed25519 signing identities used for Sync V2.

Commands:
    thn keys generate [--force]
    thn keys show
    thn keys rotate
    thn keys trust <public_key_hex>

Hybrid-Standard guarantees:
    • All commands produce deterministic JSON output
    • No tracebacks unless THN_CLI_VERBOSE is enabled
    • Safe trust-store operations
    • No silent failures
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from thn_cli.syncv2.keys import (
    add_trusted_public_key,
    create_signing_key,
    get_trusted_pubkeys,
    load_signing_key,
)

# ---------------------------------------------------------------------------
# JSON Output Helper
# ---------------------------------------------------------------------------


def _out(obj: Dict[str, Any]) -> None:
    """
    Centralized JSON printer for Hybrid-Standard CLI output.
    """
    print(json.dumps(obj, indent=4))


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------


def run_keys_generate(args: argparse.Namespace) -> int:
    """
    Generate a new Ed25519 signing key.
    """
    force = bool(args.force)

    try:
        priv_hex, pub_hex = create_signing_key(overwrite=force)
    except RuntimeError as exc:
        _out(
            {
                "command": "keys.generate",
                "status": "ERROR",
                "force": force,
                "message": str(exc),
            }
        )
        return 1

    _out(
        {
            "command": "keys.generate",
            "status": "OK",
            "force": force,
            "public_key": pub_hex,
            "message": "New signing key generated and trusted.",
        }
    )
    return 0


def run_keys_show(_: argparse.Namespace) -> int:
    """
    Display the current signing key and trusted key list.
    """
    try:
        _, current_pub = load_signing_key()
        key_status = "OK"
    except RuntimeError as exc:
        current_pub = None
        key_status = "MISSING"

    trusted: List[str] = get_trusted_pubkeys()

    _out(
        {
            "command": "keys.show",
            "status": "OK",
            "signing_key": {
                "present": current_pub is not None,
                "public_key": current_pub,
                "state": key_status,
            },
            "trusted_keys": trusted,
        }
    )
    return 0


def run_keys_rotate(_: argparse.Namespace) -> int:
    """
    Rotate the signing key — old public key remains trusted.
    """
    try:
        _, old_pub = load_signing_key()
    except RuntimeError:
        old_pub = None

    try:
        _, new_pub = create_signing_key(overwrite=True)
    except RuntimeError as exc:
        _out(
            {
                "command": "keys.rotate",
                "status": "ERROR",
                "message": str(exc),
            }
        )
        return 1

    _out(
        {
            "command": "keys.rotate",
            "status": "OK",
            "new_public_key": new_pub,
            "old_public_key": old_pub,
            "message": "Signing key rotated; previous key remains trusted.",
        }
    )
    return 0


def run_keys_trust(args: argparse.Namespace) -> int:
    """
    Add a public key to the trusted store.
    """
    pub_hex = args.public_key.strip()

    if not pub_hex:
        _out(
            {
                "command": "keys.trust",
                "status": "ERROR",
                "message": "No public key provided.",
            }
        )
        return 1

    try:
        add_trusted_public_key(pub_hex)
    except Exception as exc:
        _out(
            {
                "command": "keys.trust",
                "status": "ERROR",
                "public_key": pub_hex,
                "message": str(exc),
            }
        )
        return 1

    _out(
        {
            "command": "keys.trust",
            "status": "OK",
            "public_key": pub_hex,
            "message": "Public key added to trusted store.",
        }
    )
    return 0


# ---------------------------------------------------------------------------
# Parser Registration
# ---------------------------------------------------------------------------


def add_subparser(root_subparsers: argparse._SubParsersAction) -> None:
    """
    Register:
        thn keys generate
        thn keys show
        thn keys rotate
        thn keys trust <public_key_hex>
    """
    parser = root_subparsers.add_parser(
        "keys",
        help="Manage THN Ed25519 signing keys and trusted key store.",
        description=(
            "Generate, show, rotate, and trust Ed25519 identities used by "
            "the Sync V2 signature pipeline."
        ),
    )

    sub = parser.add_subparsers(
        dest="keys_command",
        title="keys commands",
    )

    # --- generate ---
    p_gen = sub.add_parser(
        "generate",
        help="Generate a new signing key; fails unless --force is used.",
    )
    p_gen.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing signing key.",
    )
    p_gen.set_defaults(func=run_keys_generate)

    # --- show ---
    p_show = sub.add_parser(
        "show",
        help="Display current signing key and trusted key list.",
    )
    p_show.set_defaults(func=run_keys_show)

    # --- rotate ---
    p_rot = sub.add_parser(
        "rotate",
        help="Rotate the signing key; old public key remains trusted.",
    )
    p_rot.set_defaults(func=run_keys_rotate)

    # --- trust ---
    p_trust = sub.add_parser(
        "trust",
        help="Add an external public key to the trusted store.",
    )
    p_trust.add_argument(
        "public_key",
        help="Hex-encoded public key to trust.",
    )
    p_trust.set_defaults(func=run_keys_trust)

    # Default → help
    parser.set_defaults(func=lambda args: parser.print_help())
