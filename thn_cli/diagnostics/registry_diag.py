"""
Registry Diagnostic
-------------------

Validates and summarizes the THN state registry:

    • Loads registry.json via the registry subsystem and pathing
    • Runs structural validation (version, projects, modules)
    • Computes project/module counts and basic stats
    • Surfaces recent registry events for quick inspection

Produces a Hybrid-Standard DiagnosticResult.
"""

from __future__ import annotations

from typing import Any, Dict, List

from thn_cli.pathing import get_thn_paths
from thn_cli.registry import get_recent_events, load_registry, validate_registry

from .diagnostic_result import DiagnosticResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _summarize_projects(registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a quick summary of projects and modules from the registry.
    """
    projects = registry.get("projects", {}) or {}
    if not isinstance(projects, dict):
        # Defensive: if corrupted, fall back to empty.
        return {
            "project_count": 0,
            "module_count": 0,
            "project_names": [],
        }

    project_names: List[str] = sorted(projects.keys())
    project_count = len(project_names)

    module_count = 0
    for proj in projects.values():
        modules = proj.get("modules") or []
        if isinstance(modules, list):
            module_count += len(modules)

    return {
        "project_count": project_count,
        "module_count": module_count,
        "project_names": project_names,
    }


def _summarize_events(registry: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
    """
    Pull recent registry events, but keep the diagnostic payload bounded.
    """
    events = get_recent_events(registry, limit=limit)
    return {
        "recent_events_count": len(events),
        "recent_events": events,
    }


# ---------------------------------------------------------------------------
# Public Diagnostic
# ---------------------------------------------------------------------------


def diagnose_registry() -> Dict[str, Any]:
    """
    Full Hybrid-Standard registry diagnostic.

    Checks:
        • registry.json loadability
        • structural validity via validate_registry()
        • project/module summary
        • recent event log activity
    """
    paths = get_thn_paths()

    try:
        registry = load_registry(paths)
    except Exception as exc:
        return DiagnosticResult(
            component="registry",
            ok=False,
            errors=[f"Exception while loading registry: {exc}"],
            details={"exception": str(exc)},
        ).as_dict()

    validation = validate_registry(registry)

    errors: List[str] = []
    warnings: List[str] = []

    if not validation.get("valid", False):
        errors.extend(validation.get("errors", []))

    # If registry is technically valid but empty, treat as a soft warning.
    projects = registry.get("projects", {})
    if not projects:
        warnings.append("Registry contains no projects; THN may not be initialized.")

    # Build summaries regardless of validity so UI can still introspect.
    project_summary = _summarize_projects(registry)
    events_summary = _summarize_events(registry, limit=10)

    ok = not errors

    details: Dict[str, Any] = {
        "validation": validation,
        "project_summary": project_summary,
        "events_summary": events_summary,
        "registry_version": registry.get("version"),
    }

    return DiagnosticResult(
        component="registry",
        ok=ok,
        details=details,
        warnings=warnings,
        errors=errors,
    ).as_dict()
