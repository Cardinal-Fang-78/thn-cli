from __future__ import annotations

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Status presentation
# ---------------------------------------------------------------------------


def present_status(status: str) -> Dict[str, str]:
    """
    Convert internal status codes into user-facing messages.
    """
    if status == "clean":
        return {
            "code": "no_change",
            "message": "Scaffold already matches the expected structure",
        }

    if status == "drifted":
        return {
            "code": "changes_detected",
            "message": "Scaffold differs from the expected structure",
        }

    return {
        "code": "unknown",
        "message": f"Unknown status: {status}",
    }


# ---------------------------------------------------------------------------
# Drift diff presentation (Phase 12F)
# ---------------------------------------------------------------------------


def present_diff(diff: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convert normalized drift diff entries into user-facing descriptions.

    This function assumes Phase 12F canonical diff entries produced by
    build_drift_diff().
    """
    out: List[Dict[str, str]] = []

    for entry in diff:
        path = str(entry.get("path", ""))
        kind = entry.get("kind", "unknown")
        classification = entry.get("classification", "unknown")
        impact = entry.get("impact", "unknown")
        reason = entry.get("reason_code", "UNSPECIFIED")

        if kind == "missing":
            out.append(
                {
                    "action": "missing",
                    "location": path,
                    "impact": impact,
                    "code": reason,
                    "description": "Required path is missing from the scaffold",
                }
            )
            continue

        if kind == "extra":
            out.append(
                {
                    "action": "extra",
                    "location": path,
                    "impact": impact,
                    "code": reason,
                    "description": "Unexpected extra path exists in the scaffold",
                }
            )
            continue

        # Future-proof fallback
        out.append(
            {
                "action": kind,
                "location": path,
                "impact": impact,
                "code": reason,
                "description": "Unrecognized drift classification",
            }
        )

    return out


# ---------------------------------------------------------------------------
# Notes presentation
# ---------------------------------------------------------------------------


def present_notes(notes: List[Any]) -> List[Dict[str, str]]:
    """
    Normalize notes into a stable, user-readable structure.
    """
    presented: List[Dict[str, str]] = []

    for n in notes:
        if isinstance(n, dict):
            presented.append(
                {
                    "code": str(n.get("code", "INFO")),
                    "path": str(n.get("path", "")),
                    "message": str(n.get("message", "")),
                }
            )
        else:
            presented.append(
                {
                    "code": "INFO",
                    "path": "",
                    "message": str(n),
                }
            )

    return presented
