from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class BlueprintRef:
    id: str
    version: str


@dataclass(frozen=True)
class MigrationStep:
    op: str
    args: Dict[str, Any]


@dataclass(frozen=True)
class MigrationSpec:
    schema_version: int
    blueprint_id: str
    from_version: str
    to_version: str
    description: str
    steps: List[MigrationStep]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class MigrationPlan:
    blueprint_id: str
    start: BlueprintRef
    target: BlueprintRef
    specs: List[MigrationSpec]


@dataclass(frozen=True)
class MigrationResult:
    status: str  # "OK" or "NOOP"
    path: str
    blueprint_id: str
    from_version: str
    to_version: str
    applied: List[Dict[str, Any]]
    notes: List[str]
    dry_run: bool
    expected_count: Optional[int] = None
