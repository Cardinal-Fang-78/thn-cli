# C:\THN\core\cli\thn_cli\blueprints\engine.py

import os
from typing import Any, Dict

from thn_cli.pathing import get_thn_paths

from .manager import get_blueprint  # FIXED import
from .renderer import render_template


class BlueprintApplyError(Exception):
    pass


def apply_blueprint(blueprint_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply a blueprint:
      - Load blueprint metadata
      - Render each template using Jinja2
      - Write output into <THN projects root>
    """
    bp = get_blueprint(blueprint_name)
    if not bp:
        raise BlueprintApplyError(f"Blueprint '{blueprint_name}' not found")

    paths = get_thn_paths()

    # All rendered blueprint output goes into the THN projects root
    output_root = paths["projects"]

    written = []

    # bp["_root"] = directory containing this blueprint
    bp_root = bp["_root"]

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

        # Destination path (Jinja-rendered)
        rendered_dst = render_template(dst_rel, variables)
        dst_abs = os.path.join(output_root, rendered_dst)

        os.makedirs(os.path.dirname(dst_abs), exist_ok=True)

        # Render the template contents
        with open(src_abs, "r", encoding="utf-8") as f:
            src_content = f.read()

        rendered_content = render_template(src_content, variables)

        with open(dst_abs, "w", encoding="utf-8") as f:
            f.write(rendered_content)

        written.append(dst_abs)

    return {
        "blueprint": blueprint_name,
        "output_root": output_root,
        "files_written": written,
    }
