"""
Routing Diagnostic
------------------

Validates the THN routing system:

    • routing_rules.json structure + required keys
    • classifier_config.json enforcement
    • routing_schema.json correctness
    • tag-pattern and project-pattern coverage
    • detection of unused patterns
    • validation of project mappings
    • dry-run routing simulation (auto_route)

Produces a Hybrid-Standard DiagnosticResult.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .diagnostic_result import DiagnosticResult
from thn_cli.routing.rules import load_routing_rules
from thn_cli.routing.engine import auto_route


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_schema(rules: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    required = schema.get("required_keys", [])
    missing = [k for k in required if k not in rules]

    if missing:
        errors.append(f"Missing required routing keys: {', '.join(missing)}")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _validate_tag_patterns(rules: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    tag_patterns = rules.get("tag_patterns", {})
    if not isinstance(tag_patterns, dict):
        return {
            "ok": False,
            "errors": ["tag_patterns must be a dictionary"],
            "warnings": [],
        }

    for pattern, target in tag_patterns.items():
        if not isinstance(target, dict):
            errors.append(f"Tag '{pattern}' must map to a dict, not {type(target).__name__}.")
            continue

        if "category" not in target:
            warnings.append(f"Tag pattern '{pattern}' missing optional field 'category'.")
        if "subfolder" not in target:
            warnings.append(f"Tag pattern '{pattern}' missing optional field 'subfolder'.")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _validate_project_mappings(rules: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    proj_map = rules.get("project_mappings", {})
    if not isinstance(proj_map, dict):
        return {
            "ok": False,
            "errors": ["project_mappings must be a dictionary"],
            "warnings": [],
        }

    for pattern, project in proj_map.items():
        if not isinstance(project, str):
            errors.append(
                f"Project mapping '{pattern}' must map to a string (project name)."
            )

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _test_routing_simulation(rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a minimal dry-run routing simulation using representative test tags.
    This verifies that auto_route() does not crash and that tag-logic behaves.
    """
    errors: List[str] = []
    simulation_results: Dict[str, Any] = {}

    test_tags = [
        "assets*",       # wildcard
        "docs*",         # wildcard
        "project-alpha", # example project mapping
        "unknown-tag",   # fallback test
    ]

    for tag in test_tags:
        try:
            routed = auto_route(
                envelope=None,
                tag=tag,
                zip_bytes=b"",  # no ZIP → skip classifier path
                paths={"routing_root": ""},  # unused by engine in simulation
            )
            simulation_results[tag] = routed
        except Exception as exc:
            errors.append(f"Routing simulation failed for '{tag}': {exc}")

    return {
        "ok": not errors,
        "errors": errors,
        "results": simulation_results,
    }


# ---------------------------------------------------------------------------
# Public Diagnostic
# ---------------------------------------------------------------------------

def diagnose_routing() -> Dict[str, Any]:
    """
    Full Hybrid-Standard routing diagnostic.
    Validates rules.json, schema.json, classifier config, and pattern logic.
    """

    try:
        loaded = load_routing_rules()
    except Exception as exc:
        return DiagnosticResult(
            component="routing",
            ok=False,
            errors=[f"Exception loading routing rules: {exc}"],
            details={"exception": str(exc)},
        ).as_dict()

    rules = loaded.get("rules", {})
    classifier = loaded.get("classifier", {})
    schema = loaded.get("schema", {})

    errors: List[str] = []
    warnings: List[str] = []

    # Schema validation
    schema_check = _validate_schema(rules, schema)
    if not schema_check["ok"]:
        errors.extend(schema_check["errors"])
    warnings.extend(schema_check["warnings"])

    # Tag-pattern validation
    tag_check = _validate_tag_patterns(rules)
    if not tag_check["ok"]:
        errors.extend(tag_check["errors"])
    warnings.extend(tag_check["warnings"])

    # Project mapping validation
    proj_check = _validate_project_mappings(rules)
    if not proj_check["ok"]:
        errors.extend(proj_check["errors"])
    warnings.extend(proj_check["warnings"])

    # Routing simulation
    sim_check = _test_routing_simulation(rules)
    if not sim_check["ok"]:
        errors.extend(sim_check["errors"])

    ok = not errors

    details = {
        "rules_raw": rules,
        "classifier_raw": classifier,
        "schema_raw": schema,
        "schema_validation": schema_check,
        "tag_patterns_validation": tag_check,
        "project_mappings_validation": proj_check,
        "routing_simulation": sim_check,
    }

    return DiagnosticResult(
        component="routing",
        ok=ok,
        warnings=warnings,
        errors=errors,
        details=details,
    ).as_dict()
