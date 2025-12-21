from __future__ import annotations

from typing import Any, Dict, List

from .models import MigrationSpec, MigrationStep

SUPPORTED_SPEC_SCHEMA_VERSIONS = {1}


def _require_str(d: Dict[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"Migration spec invalid: '{key}' must be a non-empty string")
    return v.strip()


def _require_int(d: Dict[str, Any], key: str) -> int:
    v = d.get(key)
    if not isinstance(v, int):
        raise ValueError(f"Migration spec invalid: '{key}' must be an int")
    return v


def _require_list(d: Dict[str, Any], key: str) -> List[Any]:
    v = d.get(key)
    if not isinstance(v, list):
        raise ValueError(f"Migration spec invalid: '{key}' must be a list")
    return v


def parse_migration_spec(data: Dict[str, Any]) -> MigrationSpec:
    schema_version = _require_int(data, "schema_version")
    if schema_version not in SUPPORTED_SPEC_SCHEMA_VERSIONS:
        raise ValueError(
            f"Migration spec invalid: unsupported schema_version {schema_version}. "
            f"Supported: {sorted(SUPPORTED_SPEC_SCHEMA_VERSIONS)}"
        )

    blueprint_id = _require_str(data, "blueprint_id")
    from_version = _require_str(data, "from_version")
    to_version = _require_str(data, "to_version")
    description = _require_str(data, "description")

    raw_steps = _require_list(data, "steps")
    steps: List[MigrationStep] = []
    for i, s in enumerate(raw_steps):
        if not isinstance(s, dict):
            raise ValueError(f"Migration spec invalid: steps[{i}] must be an object")
        op = s.get("op")
        if not isinstance(op, str) or not op.strip():
            raise ValueError(f"Migration spec invalid: steps[{i}].op must be a string")
        args = s.get("args", {})
        if not isinstance(args, dict):
            raise ValueError(f"Migration spec invalid: steps[{i}].args must be an object")
        steps.append(MigrationStep(op=op.strip(), args=args))

    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    return MigrationSpec(
        schema_version=schema_version,
        blueprint_id=blueprint_id,
        from_version=from_version,
        to_version=to_version,
        description=description,
        steps=steps,
        metadata=metadata,
    )
