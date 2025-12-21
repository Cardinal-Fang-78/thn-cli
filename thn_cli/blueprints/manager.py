import os
from typing import Dict


# Errors
class BlueprintError(Exception):
    pass


def _get_blueprint_root() -> str:
    """
    Return the absolute path to the blueprints directory
    colocated with the thn_cli.blueprints package.
    """
    return os.path.dirname(__file__)


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
