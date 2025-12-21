from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from thn_cli.snapshots.lineage import (
    SnapshotLineageError,
    load_snapshot_index,
    resolve_lineage,
    validate_lineage_consistency,
)


def explain_recovery(plan: Dict[str, Any], regen_owned: bool = False) -> Dict[str, Any]:
    """
    Explain the reasoning and intent behind recovery actions.

    Presentation-only. No execution occurs here.
    Adds best-effort snapshot lineage diagnostics if available.
    """
    explanations: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Banner notes (regen intent)
    # ------------------------------------------------------------------

    banner_notes: List[Dict[str, str]] = []
    if regen_owned:
        banner_notes.append(
            {
                "code": "REGEN_OWNED_ENABLED",
                "message": (
                    "regen-owned is enabled: will attempt to regenerate "
                    "blueprint-owned files and will not overwrite existing user content."
                ),
            }
        )
    else:
        banner_notes.append(
            {
                "code": "REGEN_OWNED_DISABLED",
                "message": (
                    "regen-owned is disabled: regeneration may be recommended "
                    "but will not be performed."
                ),
            }
        )

    # ------------------------------------------------------------------
    # Per-action explanations
    # ------------------------------------------------------------------

    for act in plan.get("actions", []):
        path = act.get("path")
        reason = act.get(
            "reason",
            "Path is missing from the current scaffold but exists in the accepted snapshot baseline.",
        )
        semantics = act.get("recovery_semantics")

        if semantics == "regen_recommended":
            if regen_owned:
                explanations.append(
                    {
                        "path": path,
                        "reason": reason,
                        "meaning": (
                            "Blueprint-owned file is missing; regeneration will be attempted "
                            "(no overwrites)."
                        ),
                    }
                )
            else:
                explanations.append(
                    {
                        "path": path,
                        "reason": reason,
                        "meaning": (
                            "Blueprint-owned file is missing; placeholder restores structure, "
                            "but regeneration is recommended to restore content."
                        ),
                    }
                )
        else:
            explanations.append(
                {
                    "path": path,
                    "reason": reason,
                    "meaning": (
                        "Expected path is missing; placeholder creation restores "
                        "structural compliance."
                    ),
                }
            )

    status = "nothing_to_explain" if not explanations else "explained"

    # ------------------------------------------------------------------
    # Snapshot lineage diagnostics (best-effort, non-fatal)
    # ------------------------------------------------------------------

    lineage_notes: List[Dict[str, str]] = []
    root_str = plan.get("path")

    if isinstance(root_str, str) and root_str.strip():
        scaffold_root = Path(root_str)
        try:
            index = load_snapshot_index(scaffold_root)
            chain = resolve_lineage(index)
            warnings = validate_lineage_consistency(chain)

            if warnings:
                for w in warnings:
                    lineage_notes.append(
                        {
                            "code": "SNAPSHOT_LINEAGE_WARNING",
                            "message": w,
                        }
                    )
            else:
                lineage_notes.append(
                    {
                        "code": "SNAPSHOT_LINEAGE_OK",
                        "message": "Snapshot lineage is consistent.",
                    }
                )

        except SnapshotLineageError as exc:
            lineage_notes.append(
                {
                    "code": "SNAPSHOT_LINEAGE_UNAVAILABLE",
                    "message": str(exc),
                }
            )
        except Exception:
            lineage_notes.append(
                {
                    "code": "SNAPSHOT_LINEAGE_UNAVAILABLE",
                    "message": "Snapshot lineage could not be inspected.",
                }
            )

    # ------------------------------------------------------------------
    # Final notes merge
    # ------------------------------------------------------------------

    plan_notes = plan.get("notes", [])
    if not isinstance(plan_notes, list):
        plan_notes = []

    merged_notes = [
        *banner_notes,
        *lineage_notes,
        *plan_notes,
    ]

    return {
        "status": status,
        "path": plan.get("path"),
        "blueprint": plan.get("blueprint"),
        "explanations": explanations,
        "notes": merged_notes,
    }
