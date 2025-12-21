from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from .manager import get_blueprint
from .renderer import render_template


class BlueprintApplyError(Exception):
    pass


MANIFEST_NAME = ".thn-tree.json"


def _normalize_rel(path: str) -> str:
    path = path.replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    return path.strip("/")


def _read_directories_file(bp_root: str) -> List[str]:
    path = os.path.join(bp_root, "directories.txt")
    if not os.path.exists(path):
        return []

    dirs: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            dirs.append(_normalize_rel(raw))
    return dirs


def _write_tree_manifest(
    *,
    root: str,
    blueprint_id: str,
    blueprint_version: str,
    expected_paths: List[str],
    rules: Dict[str, List[str]] | None,
) -> None:
    manifest_path = os.path.join(root, MANIFEST_NAME)
    tmp_path = manifest_path + ".tmp"

    payload: Dict[str, Any] = {
        "schema_version": 2,
        "blueprint": {
            "id": blueprint_id,
            "version": blueprint_version,
        },
        "expected_paths": sorted(expected_paths),
    }

    if rules:
        payload["rules"] = rules

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    os.replace(tmp_path, manifest_path)


# ---------------------------------------------------------------------------
# Core Blueprint Application (destination-aware)
# ---------------------------------------------------------------------------


def apply_blueprint(
    *,
    blueprint_name: str,
    variables: Dict[str, Any],
    output_root: str,
) -> Dict[str, Any]:
    """
    Render a blueprint into the given output_root.

    This function is destination-aware and MUST NOT assume
    global THN paths.
    """
    bp = get_blueprint(blueprint_name)
    if not bp:
        raise BlueprintApplyError(f"Blueprint '{blueprint_name}' not found")

    bp_root = bp["_root"]

    written_abs: List[str] = []
    expected_rel: List[str] = []

    templates = bp.get("templates", [])
    for item in templates:
        src_rel = item.get("source")
        dst_rel = item.get("destination")

        if not src_rel or not dst_rel:
            raise BlueprintApplyError(
                f"Invalid template entry in blueprint '{blueprint_name}': {item}"
            )

        src_abs = os.path.join(bp_root, src_rel)
        if not os.path.exists(src_abs):
            raise BlueprintApplyError(
                f"Template '{src_rel}' not found in blueprint '{blueprint_name}'"
            )

        rendered_dst = render_template(dst_rel, variables)
        dst_abs = os.path.join(output_root, rendered_dst)

        os.makedirs(os.path.dirname(dst_abs), exist_ok=True)

        with open(src_abs, "r", encoding="utf-8") as f:
            src_content = f.read()

        rendered_content = render_template(src_content, variables)

        with open(dst_abs, "w", encoding="utf-8") as f:
            f.write(rendered_content)

        written_abs.append(dst_abs)
        expected_rel.append(_normalize_rel(os.path.relpath(dst_abs, output_root)))

    return {
        "blueprint": {
            "id": bp.get("name"),
            "version": str(bp.get("version")),
        },
        "output_root": output_root,
        "files_written": written_abs,
        "expected_tree": expected_rel,
    }


# ---------------------------------------------------------------------------
# Scaffold Application Wrapper
# ---------------------------------------------------------------------------


def apply_blueprint_scaffold(
    *,
    blueprint_name: str,
    variables: Dict[str, Any],
    destination: str,
) -> Dict[str, Any]:
    """
    Apply a blueprint into a scaffold root and write the
    initial .thn-tree.json manifest.
    """
    os.makedirs(destination, exist_ok=True)

    bp = get_blueprint(blueprint_name)
    if not bp:
        raise BlueprintApplyError(f"Blueprint '{blueprint_name}' not found")

    result = apply_blueprint(
        blueprint_name=blueprint_name,
        variables=variables,
        output_root=destination,
    )

    bp_root = bp["_root"]

    expected: List[str] = []

    # 1) Directories (must exist and be expected)
    for d in _read_directories_file(bp_root):
        abs_dir = os.path.join(destination, d)
        os.makedirs(abs_dir, exist_ok=True)
        expected.append(_normalize_rel(d))

    # 1.5) THN internal registry (infrastructure-owned)
    expected.extend(
        [
            ".thn",
            ".thn/registry",
            ".thn/registry/scaffold.json",
        ]
    )

    # 2) Files written by templates
    for rel in result["expected_tree"]:
        expected.append(_normalize_rel(rel))

    rules = None
    if blueprint_name == "project_default":
        rules = {
            "allow_children": ["modules/*"],
            "ignore": [
                ".thn-tree.json",
                ".thn-snapshots/**",
                "logs/**",
                "temp/**",
            ],
        }

    _write_tree_manifest(
        root=destination,
        blueprint_id=result["blueprint"]["id"],
        blueprint_version=result["blueprint"]["version"],
        expected_paths=expected,
        rules=rules,
    )

    return {
        **result,
        "scaffold_root": destination,
        "expected_tree": expected,
    }
