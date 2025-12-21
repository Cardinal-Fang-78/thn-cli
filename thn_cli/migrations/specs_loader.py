from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .models import MigrationSpec
from .parse import parse_migration_spec


def load_specs_from_dir(specs_dir: Path) -> List[MigrationSpec]:
    if not specs_dir.exists() or not specs_dir.is_dir():
        return []

    specs: List[MigrationSpec] = []
    for p in sorted(specs_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            spec = parse_migration_spec(data)
            specs.append(spec)
        except Exception:
            # Spec files must be safe to ignore; diagnostics can surface later.
            continue

    return specs


def index_specs(specs: List[MigrationSpec]) -> Dict[str, Dict[str, Dict[str, MigrationSpec]]]:
    """
    index[blueprint_id][from_version][to_version] = spec
    """
    out: Dict[str, Dict[str, Dict[str, MigrationSpec]]] = {}
    for s in specs:
        out.setdefault(s.blueprint_id, {}).setdefault(s.from_version, {})[s.to_version] = s
    return out
