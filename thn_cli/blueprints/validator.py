import os
from typing import Dict, List

from .manager import BlueprintError
from .resolver import resolve_blueprint


class BlueprintValidationError(Exception):
    pass


def validate_blueprint(name: str) -> Dict:
    """Validate a single blueprint. Returns a dict with status & errors."""
    result = {"blueprint": name, "valid": True, "errors": []}

    try:
        bp = resolve_blueprint(name)
    except Exception as exc:
        result["valid"] = False
        result["errors"].append(str(exc))
        return result

    root = bp["_root"]

    # Validate templates
    for item in bp.get("templates", []):
        src = item.get("source")
        if not src:
            result["valid"] = False
            result["errors"].append("Template entry missing 'source'")
            continue

        abs_path = os.path.join(root, src)
        if not os.path.exists(abs_path):
            result["valid"] = False
            result["errors"].append(f"Missing template file: {src}")

    return result


def validate_all_blueprints() -> List[Dict]:
    """Validate every blueprint in the system."""
    from .manager import list_blueprints  # lazy import

    results = []
    for name in list_blueprints():
        results.append(validate_blueprint(name))
    return results
