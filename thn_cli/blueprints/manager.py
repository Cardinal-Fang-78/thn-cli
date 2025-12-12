import os
from typing import Dict

from ..pathing import get_thn_paths


# Errors
class BlueprintError(Exception):
    pass


def _get_blueprint_root() -> str:
    """Returns path to the root folder containing all blueprints."""
    paths = get_thn_paths()
    return os.path.join(paths["core_cli"], "thn_cli", "blueprints")


def list_blueprints():
    """Returns a list of available blueprint folder names."""
    from .loader import load_all_blueprints  # lazy import

    root = _get_blueprint_root()
    bp_dict = load_all_blueprints(root)
    return sorted(bp_dict.keys())


def get_blueprint(name: str) -> Dict:
    """Returns a full blueprint dict by name."""
    from .loader import load_all_blueprints  # lazy import

    root = _get_blueprint_root()
    bp_dict = load_all_blueprints(root)
    if name not in bp_dict:
        raise BlueprintError(f"Blueprint '{name}' not found")
    return bp_dict[name]
