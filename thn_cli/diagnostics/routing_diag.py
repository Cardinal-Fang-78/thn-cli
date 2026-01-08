# thn_cli/diagnostics/routing_diag.py

"""
Routing Diagnostic
------------------

Validates the THN routing system configuration.

This diagnostic performs **static, non-executing validation** of routing
rules to ensure they are structurally sound, internally consistent, and
safe to consume by the routing engine.

Validated aspects include:
    • routing_rules.json structure + required keys
    • tag-pattern and project-pattern shape validation
    • detection of malformed rule targets
    • basic coverage and fallback presence
    • future-safety checks for engine compatibility

This diagnostic explicitly does NOT:
    • Execute routing logic
    • Invoke auto_route()
    • Simulate envelope execution
    • Depend on engine permissiveness

Produces a Hybrid-Standard DiagnosticResult.
"""

from __future__ import annotations

from typing import Any, Dict, List

from thn_cli.routing.rules import load_routing_rules

from .diagnostic_result import DiagnosticResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_schema(rules: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate routing rules against the declared schema requirements.
    """
    errors: List[str] = []
    warnings: List[str] = []

    required = schema.get("required_keys", [])
    if isinstance(required, list):
        missing = [k for k in required if k not in rules]
        if missing:
            errors.append(f"Missing required routing keys: {', '.join(missing)}")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _validate_tag_patterns(rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate tag_patterns structure and target shapes.
    """
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
        if not isinstance(pattern, str) or not pattern.strip():
            errors.append("Tag pattern keys must be non-empty strings.")
            continue

        if not isinstance(target, dict):
            errors.append(f"Tag '{pattern}' must map to a dict, not {type(target).__name__}.")
            continue

        # Optional fields (warnings only)
        if "category" not in target:
            warnings.append(f"Tag pattern '{pattern}' missing optional field 'category'.")
        if "subfolder" not in target:
            warnings.append(f"Tag pattern '{pattern}' missing optional field 'subfolder'.")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _validate_project_mappings(rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate project_mappings structure.
    """
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
        if not isinstance(pattern, str) or not pattern.strip():
            errors.append("Project mapping keys must be non-empty strings.")
            continue

        if not isinstance(project, str) or not project.strip():
            errors.append(f"Project mapping '{pattern}' must map to a non-empty project name.")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _validate_fallbacks(rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that routing rules define reasonable fallback behavior.

    This does NOT execute routing logic; it only checks presence.
    """
    errors: List[str] = []
    warnings: List[str] = []

    tag_patterns = rules.get("tag_patterns", {})
    has_wildcard = any(isinstance(k, str) and "*" in k for k in tag_patterns.keys())

    if not has_wildcard:
        warnings.append("No wildcard tag pattern detected; unknown tags may route unpredictably.")

    return {"ok": True, "errors": errors, "warnings": warnings}


# ---------------------------------------------------------------------------
# Public Diagnostic
# ---------------------------------------------------------------------------


def diagnose_routing() -> Dict[str, Any]:
    """
    Full Hybrid-Standard routing diagnostic.

    Performs static validation only. No routing execution occurs.
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

    # Fallback / coverage validation
    fallback_check = _validate_fallbacks(rules)
    warnings.extend(fallback_check["warnings"])

    ok = not errors

    details = {
        "rules_raw": rules,
        "classifier_raw": classifier,
        "schema_raw": schema,
        "schema_validation": schema_check,
        "tag_patterns_validation": tag_check,
        "project_mappings_validation": proj_check,
        "fallback_validation": fallback_check,
    }


def diagnose_routing() -> dict:
    return {
        "component": "routing",
        "category": "routing",
        "ok": False,
        "details": {},
        "warnings": [],
        "errors": [],
    }
