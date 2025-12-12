"""
THN Sync V2 (Hybrid-Standard)
-----------------------------

Public API re-exports for the Sync V2 subsystem.

This namespace provides high-level access to the Sync V2 envelope
handling pipeline, including:

    • Envelope loading (raw file / bytes)
    • Sync V2 full apply engine (apply_envelope_v2)
    • Manifest summarization helpers
    • Negotiation utilities for remote Sync servers

This module exposes ONLY the stable external API intended for
importers. All other components (chunk stores, delta engines,
status DB, remote server internals) remain internal.
"""

from .engine import apply_envelope_v2
from .envelope import (inspect_envelope, load_envelope_from_bytes,
                       load_envelope_from_file)
from .manifest import derive_tags_for_file, summarize_manifest
from .remote_negotiation import (ensure_mode_supported,
                                 negotiate_remote_capabilities)
