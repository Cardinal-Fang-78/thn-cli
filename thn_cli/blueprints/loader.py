import json
import os
from typing import Dict

from .manager import BlueprintError  # OK, no cycle (no imports below)


def load_blueprint_folder(folder: str) -> Dict:
    """Loads one blueprint folder into a dict."""
    bp_file = os.path.join(folder, "blueprint.json")
    if not os.path.exists(bp_file):
        raise BlueprintError(f"Blueprint folder missing blueprint.json: {folder}")

    with open(bp_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["_root"] = folder
    return data


def load_all_blueprints(root: str) -> Dict[str, Dict]:
    """Discovers all blueprint folders."""
    bp_dict = {}

    if not os.path.exists(root):
        return bp_dict

    for entry in os.listdir(root):
        folder = os.path.join(root, entry)
        if not os.path.isdir(folder):
            continue
        if not os.path.exists(os.path.join(folder, "blueprint.json")):
            continue
        bp = load_blueprint_folder(folder)
        bp_dict[bp["name"]] = bp

    return bp_dict
