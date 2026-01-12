"""
Diagnostic normalization layer.

This module defines the explicit presentation-boundary normalization
surface for diagnostic payloads.

DX-2.1 CONTRACT GUARANTEES
-------------------------
• Normalization is non-enforcing
• Normalization is lossy-safe
• Unknown fields are preserved
• Metadata remains non-semantic
• Runtime behavior is unchanged

This function currently performs an identity transform and exists
solely to provide a stable, test-backed extension point for future
DX branches (e.g., strict mode).
"""

import os
from typing import Any, Dict


def normalize_diagnostics(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize diagnostic payloads for presentation.

    Current behavior:
    - Pass-through (identity)
    - No mutation of existing fields
    - No filtering
    - No validation

    DX-2.1:
    - When THN_DIAG_NORMALIZATION_PROBE=1 is set, an explicit
      non-semantic marker is added for test verification.
    """

    if os.environ.get("THN_DIAG_NORMALIZATION_PROBE") == "1":
        payload = dict(payload)
        payload["__normalized__"] = True

    return payload
