"""
THN Migration Registry (Hybrid-Standard)
---------------------------------------

RESPONSIBILITIES
----------------
This module defines the **migration discovery and planning registry**.

It is responsible for:
    • Loading all available MigrationSpec definitions from disk
    • Indexing migration specs by blueprint and version
    • Computing a valid migration chain between blueprint versions
    • Producing a deterministic MigrationPlan for execution

This registry defines the **authoritative migration path selection semantics**
used by:
    • thn migrate scaffold
    • CLI migration planning
    • Future GUI or CI-driven migrations

CONTRACT STATUS
---------------
⚠️ PLANNING LOGIC — SEMANTICS LOCKED

Changes to this module may:
    • Alter migration ordering
    • Change which paths are considered valid
    • Affect reproducibility of migrations
    • Break expectations around version reachability

Any modification MUST preserve:
    • Deterministic path selection
    • No implicit or inferred migrations
    • Explicit spec-defined transitions only

NON-GOALS
---------
• This module does NOT execute migrations
• This module does NOT mutate project state
• This module does NOT validate migration step semantics
• This module does NOT infer version jumps

Execution is handled by migrations.engine.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import BlueprintRef, MigrationPlan, MigrationSpec
from .specs_loader import index_specs, load_specs_from_dir


@dataclass(frozen=True)
class MigrationRegistry:
    specs_dir: Path

    def load_all(self) -> List[MigrationSpec]:
        return load_specs_from_dir(self.specs_dir)

    def plan(self, *, blueprint_id: str, current: str, target: str) -> MigrationPlan:
        specs = self.load_all()
        idx = index_specs(specs)

        if blueprint_id not in idx:
            raise ValueError(f"No migrations found for blueprint '{blueprint_id}'")

        graph = idx[blueprint_id]  # from_version -> {to_version: spec}

        path = _bfs_find_path(graph, start=current, goal=target)
        if not path:
            raise ValueError(
                f"No migration path for blueprint '{blueprint_id}' from {current} to {target}"
            )

        # path is list of versions like ["1", "2", "3"] → specs are 1→2, 2→3
        chain: List[MigrationSpec] = []
        for a, b in zip(path, path[1:]):
            chain.append(graph[a][b])

        return MigrationPlan(
            blueprint_id=blueprint_id,
            start=BlueprintRef(id=blueprint_id, version=current),
            target=BlueprintRef(id=blueprint_id, version=target),
            specs=chain,
        )


def _bfs_find_path(
    graph: Dict[str, Dict[str, MigrationSpec]],
    *,
    start: str,
    goal: str,
) -> Optional[List[str]]:
    if start == goal:
        return [start]

    q: deque[str] = deque([start])
    prev: Dict[str, Optional[str]] = {start: None}
    visited: Set[str] = {start}

    while q:
        v = q.popleft()
        for nxt in sorted(graph.get(v, {}).keys()):
            if nxt in visited:
                continue
            visited.add(nxt)
            prev[nxt] = v
            if nxt == goal:
                return _reconstruct(prev, goal)
            q.append(nxt)

    return None


def _reconstruct(prev: Dict[str, Optional[str]], goal: str) -> List[str]:
    out: List[str] = []
    cur: Optional[str] = goal
    while cur is not None:
        out.append(cur)
        cur = prev.get(cur)
    out.reverse()
    return out
