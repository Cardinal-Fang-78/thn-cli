from __future__ import annotations

"""
Scaffold Drift Explanation Layer (Diagnostic-Only, Hybrid-Standard)
=================================================================

RESPONSIBILITIES
----------------
Provides a human-readable explanation of scaffold drift classifications.

This module:
    • Consumes the output of preview_scaffold_drift()
    • Translates diagnostic notes into stable explanation records
    • Maps internal reason codes to user-facing classifications
    • Produces deterministic, read-only explanation output

This layer exists strictly to answer:
    “Why is this path classified the way it is?”

DEPENDENCIES
------------
This module depends entirely on:
    • thn_cli.scaffolds.drift_preview.preview_scaffold_drift

It MUST:
    • NOT recompute drift
    • NOT reclassify paths
    • NOT reinterpret rules
    • NOT inspect filesystem state directly

CONTRACT STATUS
---------------
⚠️ DIAGNOSTIC / PRESENTATION LAYER — NON-AUTHORITATIVE

All authoritative drift semantics originate from:
    • drift_preview
    • classifier
    • verifier / accept / migrate flows

Changes here must never alter drift outcomes.

NON-GOALS
---------
• This module does NOT perform classification
• This module does NOT enforce policy
• This module does NOT mutate state
• This module does NOT affect accept/migrate behavior
"""

from pathlib import Path
from typing import Any, Dict, List

from thn_cli.scaffolds.drift_preview import preview_scaffold_drift


def explain_scaffold_drift(path: Path) -> Dict[str, Any]:
    """
    Explain WHY each path is classified the way it is.

    Characteristics:
        • Read-only
        • Deterministic
        • Consumes preview output verbatim
        • Does not reclassify or recompute
    """
    preview = preview_scaffold_drift(path)

    explanations: List[Dict[str, str]] = []

    # Explain each note emitted by preview (authoritative source)
    for note in preview.get("notes", []):
        explanations.append(
            {
                "code": note.get("code", "UNKNOWN"),
                "path": note.get("path", ""),
                "classification": _classification_from_code(note.get("code")),
                "reason": note.get("message", ""),
            }
        )

    # Clean scaffold explanation
    if not explanations:
        explanations.append(
            {
                "code": "CLEAN",
                "path": "",
                "classification": "clean",
                "reason": "All filesystem paths match the expected scaffold and rules",
            }
        )

    return {
        "status": preview["status"],
        "path": preview["path"],
        "blueprint": preview.get("blueprint", {}),
        "explanations": explanations,
    }


def _classification_from_code(code: str | None) -> str:
    """
    Map preview reason codes to stable human classifications.

    This mapping is intentionally shallow and presentation-oriented.
    """
    return {
        "OWNED_SUB_SCAFFOLD": "owned_sub_scaffold",
        "UNEXPECTED_EXTRA": "unexpected",
        "MISSING_EXPECTED": "missing",
        "IGNORED_PATH": "ignored",
    }.get(code or "", "unknown")
