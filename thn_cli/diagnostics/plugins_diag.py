"""
Plugins Diagnostic
------------------

Validates the plugin subsystem:

    • Registry structure correctness
    • Plugin list loadability
    • Module importability
    • Enabled/disabled state integrity
    • Description + metadata presence

Produces Hybrid-Standard DiagnosticResult output.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, List

from .diagnostic_result import DiagnosticResult
from thn_cli.plugins.plugin_loader import (
    list_plugins,
    get_plugin_info,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_importable(module_path: str) -> bool:
    """
    Return True if the plugin’s module can be imported.

    We catch *all* exceptions, because failing to import a plugin should
    be reported as a diagnostic error, not raise.
    """
    try:
        importlib.import_module(module_path)
        return True
    except Exception:
        return False


def _validate_plugin_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single plugin record, returning structured diagnostics.
    """
    module_path = record.get("module", "")
    name = record.get("name", "(unnamed)")
    enabled = record.get("enabled", False)
    description = record.get("description", None)

    importable = _check_importable(module_path)

    return {
        "name": name,
        "module": module_path,
        "enabled": enabled,
        "description_present": bool(description),
        "importable": importable,
    }


# ---------------------------------------------------------------------------
# Public Diagnostic
# ---------------------------------------------------------------------------

def diagnose_plugins() -> Dict[str, Any]:
    """
    Validate plugin registry and importability.

    Success criteria:

        OK if:
            - Plugin list loads successfully
            - All plugin modules import cleanly

        Warnings:
            - Description missing
            - Plugin exists but is disabled

        Errors:
            - Failed module import for any enabled plugin
            - Invalid plugin registry structure
    """
    plugins = list_plugins()
    details: Dict[str, Any] = {}
    warnings: List[str] = []
    errors: List[str] = []

    # Structure validation
    if not isinstance(plugins, list):
        return DiagnosticResult(
            component="plugins",
            ok=False,
            details={"error": "Plugin registry did not return a list."},
            warnings=[],
            errors=["Plugin registry data structure is invalid."],
        ).as_dict()

    # Validate each plugin
    for record in plugins:
        name = record.get("name", "(unnamed)")
        info = _validate_plugin_record(record)
        details[name] = info

        if info["enabled"] and not info["importable"]:
            errors.append(f"Enabled plugin '{name}' failed to import (module={info['module']}).")

        if not info["description_present"]:
            warnings.append(f"Plugin '{name}' has no description metadata.")

        if not info["enabled"]:
            warnings.append(f"Plugin '{name}' is registered but disabled.")

    ok = not errors

    return DiagnosticResult(
        component="plugins",
        ok=ok,
        details=details,
        warnings=warnings,
        errors=errors,
    ).as_dict()
