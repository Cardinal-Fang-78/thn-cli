from __future__ import annotations

from typing import Any, Dict, List


def simulate_recovery(*, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read-only simulation of a recovery plan.

    No filesystem access.
    No mutation.
    No policy checks.
    """

    # Explicit no-op handling
    if plan.get("status") == "nothing_to_recover":
        return {
            "status": "noop",
            "path": plan.get("path"),
            "message": "No recovery actions required",
            "simulated_actions": [],
            "notes": plan.get("notes", []),
        }

    actions: List[Dict[str, Any]] = plan.get("actions", []) or []

    simulated: List[Dict[str, Any]] = []
    for act in actions:
        simulated.append(
            {
                "op": act.get("op"),
                "path": act.get("path"),
                "source": act.get("source"),
                "effect": f"Would {act.get('op')} {act.get('path')}",
            }
        )

    status = "would_recover" if simulated else "nothing_to_do"

    return {
        "status": status,
        "path": plan.get("path"),
        "blueprint": plan.get("blueprint"),
        "schema_version": plan.get("schema_version"),
        "simulated_actions": simulated,
        "notes": plan.get("notes", []),
    }
