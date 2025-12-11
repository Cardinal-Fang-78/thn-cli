# thn_cli/syncv2/keys.py

"""
Persistent Ed25519 key management for THN Sync V2.

Responsibilities:
    - Generate and store a persistent Ed25519 signing key
    - Expose the public key for distribution
    - Maintain a trusted public-key store for verification
    - Sign and verify Sync V2 manifests

Key storage layout:

    Root (default):
        Windows:  C:\\THN\\keys
        Others:   ~/.thn/keys

    Overridable via environment variable:
        THN_KEYS_ROOT

Files under the key root:

    signing_key_ed25519.json
        {
            "private_key_hex": "<hex>",
            "public_key_hex": "<hex>"
        }

    trusted_pubkeys.json
        {
            "keys": ["<hex>", "<hex>", ...]
        }
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import json
import os

try:
    from nacl.encoding import HexEncoder
    from nacl.signing import SigningKey, VerifyKey
except ImportError as exc:  # pragma: no cover - hard failure path
    raise RuntimeError(
        "PyNaCl is required for Ed25519 signatures but is not installed. "
        "Install it with: pip install pynacl"
    ) from exc


__all__ = [
    "get_key_root",
    "create_signing_key",
    "load_signing_key",
    "load_or_create_signing_key",
    "add_trusted_public_key",
    "get_trusted_pubkeys",
    "sign_manifest",
    "verify_manifest_signature",
]


# ---------------------------------------------------------------------------
# Key root / path utilities
# ---------------------------------------------------------------------------

def _default_key_root() -> str:
    """
    Default on-disk root for THN key material.

    Windows:
        C:\\THN\\keys

    Others:
        ~/.thn/keys
    """
    if os.name == "nt":
        return r"C:\THN\keys"
    return os.path.join(os.path.expanduser("~"), ".thn", "keys")


def get_key_root() -> str:
    """
    Resolve the active key root, honoring THN_KEYS_ROOT if set.
    """
    return os.environ.get("THN_KEYS_ROOT", _default_key_root())


def _ensure_key_root() -> str:
    """
    Ensure the key root exists on disk, returning the resolved path.
    """
    root = get_key_root()
    os.makedirs(root, exist_ok=True)
    return root


def _signing_key_path() -> str:
    """
    Full path to the signing key JSON file.
    """
    root = _ensure_key_root()
    return os.path.join(root, "signing_key_ed25519.json")


def _trusted_keys_path() -> str:
    """
    Full path to the trusted public-keys JSON file.
    """
    root = _ensure_key_root()
    return os.path.join(root, "trusted_pubkeys.json")


# ---------------------------------------------------------------------------
# Signing key management
# ---------------------------------------------------------------------------

def create_signing_key(overwrite: bool = False) -> Tuple[SigningKey, str]:
    """
    Create a new Ed25519 signing key and store it on disk.

    Args:
        overwrite:
            If False and a key already exists, raise RuntimeError instead
            of overwriting. If True, replace any existing signing key.

    Returns:
        (signing_key, public_key_hex)
    """
    path = _signing_key_path()

    if os.path.exists(path) and not overwrite:
        raise RuntimeError(
            f"Signing key already exists: {path}. "
            "Use overwrite=True or the 'thn keys rotate' command."
        )

    sk = SigningKey.generate()
    vk = sk.verify_key

    priv_hex = sk.encode(encoder=HexEncoder).decode("ascii")
    pub_hex = vk.encode(encoder=HexEncoder).decode("ascii")

    data = {
        "private_key_hex": priv_hex,
        "public_key_hex": pub_hex,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Ensure trust store contains this new public key
    add_trusted_public_key(pub_hex)

    return sk, pub_hex


def load_signing_key() -> Tuple[SigningKey, str]:
    """
    Load the existing Ed25519 signing key from disk.

    Returns:
        (signing_key, public_key_hex)

    Raises:
        RuntimeError if the key file is missing or incomplete.
    """
    path = _signing_key_path()
    if not os.path.exists(path):
        raise RuntimeError(
            f"Signing key not found at {path}. "
            "Generate one with: thn keys generate"
        )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    priv_hex = data.get("private_key_hex")
    pub_hex = data.get("public_key_hex")

    if not priv_hex or not pub_hex:
        raise RuntimeError("Signing key file is missing required fields.")

    sk = SigningKey(priv_hex, encoder=HexEncoder)
    return sk, pub_hex


def load_or_create_signing_key() -> Tuple[SigningKey, str]:
    """
    Load the signing key if present, otherwise create and store a new one.

    Returns:
        (signing_key, public_key_hex)
    """
    try:
        return load_signing_key()
    except RuntimeError:
        return create_signing_key(overwrite=False)


# ---------------------------------------------------------------------------
# Trusted public-key store
# ---------------------------------------------------------------------------

def _load_trusted_pubkeys() -> List[str]:
    """
    Internal helper: read the trusted_pubkeys.json file.

    Returns an empty list if the file is missing or malformed.
    """
    path = _trusted_keys_path()
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    keys = data.get("keys", [])
    if not isinstance(keys, list):
        return []

    return [k for k in keys if isinstance(k, str)]


def _save_trusted_pubkeys(keys: List[str]) -> None:
    """
    Internal helper: write the trusted_pubkeys.json file atomically.
    """
    path = _trusted_keys_path()
    payload = {"keys": sorted(set(keys))}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def add_trusted_public_key(pub_hex: str) -> None:
    """
    Add a public key (hex string) to the trusted public-key store.

    No-op if the key is already present.
    """
    if not pub_hex:
        return

    keys = _load_trusted_pubkeys()
    if pub_hex not in keys:
        keys.append(pub_hex)
        _save_trusted_pubkeys(keys)


def get_trusted_pubkeys() -> List[str]:
    """
    Return the list of trusted public keys (hex strings).
    """
    return _load_trusted_pubkeys()


# ---------------------------------------------------------------------------
# Manifest signing / verification
# ---------------------------------------------------------------------------

def sign_manifest(unsigned_manifest: Dict[str, object]) -> Dict[str, object]:
    """
    Sign the given unsigned manifest dict with the current signing key.

    The original dict is not mutated; a new dict is returned containing
    all original fields plus:

        signature       (hex-encoded bytes)
        signature_type  "ed25519"
        public_key      (hex-encoded Ed25519 public key)

    Returns:
        New manifest dict with signature attached.
    """
    sk, pub_hex = load_or_create_signing_key()

    data_bytes = json.dumps(unsigned_manifest, sort_keys=True).encode("utf-8")
    sig = sk.sign(data_bytes).signature

    manifest = dict(unsigned_manifest)
    manifest["signature"] = sig.hex()
    manifest["signature_type"] = "ed25519"
    manifest["public_key"] = pub_hex

    return manifest


def verify_manifest_signature(manifest: Dict[str, object]) -> List[str]:
    """
    Verify a manifest's signature against the trusted public-key store.

    Returns:
        A list of error messages; an empty list means verification succeeded.
    """
    errors: List[str] = []

    sig_hex = manifest.get("signature")
    sig_type = manifest.get("signature_type")
    pub_hex = manifest.get("public_key")

    if not sig_hex or not sig_type or not pub_hex:
        return ["Manifest is missing signature, signature_type, or public_key."]

    if sig_type != "ed25519":
        return [f"Unsupported signature_type: {sig_type} (expected 'ed25519')."]

    trusted = get_trusted_pubkeys()
    if pub_hex not in trusted:
        errors.append(
            "Manifest signed by an untrusted public key. "
            "Public key not found in trusted_pubkeys.json."
        )
        return errors

    # Rebuild the unsigned manifest payload
    unsigned = dict(manifest)
    for field in ("signature", "signature_type", "public_key"):
        unsigned.pop(field, None)

    data_bytes = json.dumps(unsigned, sort_keys=True).encode("utf-8")

    try:
        vk = VerifyKey(pub_hex, encoder=HexEncoder)
        vk.verify(data_bytes, bytes.fromhex(sig_hex))
    except Exception as exc:
        errors.append(f"Ed25519 signature verification failed: {exc}")

    return errors
