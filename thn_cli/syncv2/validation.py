# thn_cli/syncv2/validation.py

"""
Sync V2 Envelope Validation (Hybrid-Standard)
=============================================

RESPONSIBILITIES
----------------
Provides **static, side-effect-free validation** of Sync V2 envelopes.

This module is responsible for:
    • Validating Sync V2 manifests and payload ZIPs
    • Verifying Ed25519 manifest signatures (ONLY when declared)
    • Verifying per-file SHA256 hashes (raw-zip mode only)
    • Computing the overall payload SHA256
    • Returning a stable, structured validation result

This module performs *static validation only*:
    • No filesystem writes
    • No target inspection
    • No routing
    • No CDC apply or mutation

SIGNATURE POLICY
----------------
Signature verification is **policy-neutral**.

Signatures are verified ONLY if signature material is explicitly declared
in the manifest. Requiring signatures is a future strict-mode policy
(env flag or CLI flag) and is NOT enforced here by default.

RETURN CONTRACT
---------------
All validation functions return a stable structure:

    {
        "valid": bool,
        "errors": [str, ...],
        "hash": "<sha256-of-payload>" | None
    }

AUTHORITY BOUNDARY
------------------
This module is **non-authoritative**.

Final enforcement and apply semantics are owned by:
    • thn_cli.syncv2.engine.validate_envelope()
    • thn_cli.syncv2.engine.apply_envelope_v2()

This module must never:
    • Apply files
    • Infer destinations
    • Enforce CDC safety rules
    • Mutate state

NON-GOALS
---------
• This module does NOT parse CLI arguments
• This module does NOT perform routing
• This module does NOT validate destination trees
• This module does NOT implement CDC apply semantics

NOTE
----
Unknown or future manifest modes are permitted.
They do not invalidate the envelope but may emit warnings.
"""

from __future__ import annotations

import hashlib
import zipfile
from typing import Any, Dict, List

from thn_cli.syncv2.keys import verify_manifest_signature

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _manifest_declares_signature(manifest: Dict[str, Any]) -> bool:
    """
    Return True if the manifest declares any signature-related material.

    This gate ensures signature verification is opt-in and policy-neutral.
    """
    return bool(
        manifest.get("signature") or manifest.get("signature_type") or manifest.get("public_key")
    )


def _sha256_of_file(path: str) -> str:
    """
    Compute SHA-256 hash of a file.

    CONTRACT
    --------
    • Streaming
    • Deterministic
    • Read-only
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_raw_zip_manifest(
    manifest: Dict[str, Any],
    payload_zip: str,
) -> List[str]:
    """
    Validate per-file SHA256 hashes for raw-zip mode.

    Behavior:
        • Only runs if manifest["file_hashes"] exists
        • Hash mismatches are treated as errors
        • Missing files are treated as mismatches
    """
    errors: List[str] = []
    expected = manifest.get("file_hashes", {})

    if not expected:
        return errors  # Nothing further to validate

    try:
        with zipfile.ZipFile(payload_zip, "r") as zf:
            computed: Dict[str, str] = {}

            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                with zf.open(name) as f:
                    h = hashlib.sha256()
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                    computed[name] = h.hexdigest()

        for name, exp_hash in expected.items():
            act = computed.get(name)
            if act != exp_hash:
                errors.append(f"File hash mismatch: {name}")

    except Exception as exc:
        errors.append(f"Failed to verify per-file hashes: {exc}")

    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_envelope(
    manifest: Dict[str, Any],
    payload_path: str,
) -> Dict[str, Any]:
    """
    Validate a Sync V2 envelope (manifest + payload.zip).

    This function is:
        • Deterministic
        • Side-effect free
        • Safe for inspect, preview, and CI usage
    """
    errors: List[str] = []

    # --- Signature verification (opt-in) ------------------------------------
    if _manifest_declares_signature(manifest):
        errors.extend(verify_manifest_signature(manifest))

    # --- Payload hash -------------------------------------------------------
    try:
        payload_hash = _sha256_of_file(payload_path)
    except Exception as exc:
        errors.append(f"Failed to compute payload SHA-256: {exc}")
        return {
            "valid": False,
            "errors": errors,
            "hash": None,
        }

    # --- Mode-specific validation ------------------------------------------
    mode = manifest.get("mode", "raw-zip")

    if mode == "raw-zip":
        errors.extend(_validate_raw_zip_manifest(manifest, payload_path))

    elif mode == "cdc-delta":
        # CDC-delta validation is enforced during engine apply.
        pass

    else:
        # Unknown modes are permitted but reported.
        errors.append(f"Unknown manifest mode: {mode}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "hash": payload_hash,
    }
