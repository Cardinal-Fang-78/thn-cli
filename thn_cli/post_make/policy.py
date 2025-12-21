from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class AcceptancePolicy:
    """
    Defines what kinds of drift may be accepted.

    This is intentionally minimal and internal.
    """

    allow_unexpected: bool = True
    allow_owned_sub_scaffold: bool = True
    allow_missing_required: bool = False

    def validate(self, preview: Dict[str, Any]) -> List[str]:
        """
        Returns a list of policy violation messages.
        Empty list means acceptance is allowed.
        """
        violations: List[str] = []

        for note in preview.get("notes", []):
            code = note.get("code")

            if code == "UNEXPECTED_EXTRA" and not self.allow_unexpected:
                violations.append("Unexpected files are not allowed by policy.")

            if code == "OWNED_SUB_SCAFFOLD" and not self.allow_owned_sub_scaffold:
                violations.append("Owned sub-scaffolds are not allowed by policy.")

            if code == "MISSING_EXPECTED" and not self.allow_missing_required:
                violations.append("Missing required paths are not allowed by policy.")

        return violations
