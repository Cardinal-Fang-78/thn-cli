from __future__ import annotations

import json
import os

from thn_cli.pathing import get_thn_paths


def _safe_name(name: str) -> str:
    """Normalize and canonicalize blueprint names."""
    return name.strip().lower().replace(" ", "_")


def run_blueprint_new(args) -> int:
    """
    Entry point for:

        thn blueprint new --name <name>

    Creates:
        <blueprints_root>/<name>/
            blueprint.json
            templates/example.txt.j2
    """
    name = _safe_name(args.name)
    paths = get_thn_paths()

    bp_root = os.path.join(paths["blueprints_root"], name)

    if os.path.exists(bp_root):
        print("\nError: Blueprint already exists:")
        print(f"  {bp_root}\n")
        return 1

    os.makedirs(bp_root, exist_ok=True)
    os.makedirs(os.path.join(bp_root, "templates"), exist_ok=True)

    descriptor = {
        "name": name,
        "version": 1,
        "description": f"New THN blueprint '{name}'.",
        "variables": {
            "example_var": "str",
        },
        "templates": [
            {
                "source": "templates/example.txt.j2",
                "destination": "{{ example_var }}/output.txt",
            }
        ],
    }

    descriptor_path = os.path.join(bp_root, "blueprint.json")
    with open(descriptor_path, "w", encoding="utf-8") as f:
        json.dump(descriptor, f, indent=4)

    tmpl_path = os.path.join(bp_root, "templates", "example.txt.j2")
    with open(tmpl_path, "w", encoding="utf-8") as f:
        f.write(
            "Generated from blueprint '{{ name }}'.\n"
            "Variable example_var = {{ example_var }}\n"
        )

    print("\nTHN Blueprint Creator")
    print("----------------------")
    print(f"Blueprint created: {name}")
    print(f"Location: {bp_root}\n")

    print("Next steps:")
    print(f"  • Edit descriptor: {descriptor_path}")
    print(f"  • Add templates under: {os.path.join(bp_root, 'templates')}")
    print("  • Example apply:")
    print(f'      thn blueprint apply --name {name} --var example_var="value"\n')

    return 0


def add_subparser(subparsers) -> None:
    """Register: thn blueprint new"""
    parser = subparsers.add_parser(
        "new",
        help="Create a new THN blueprint.",
        description="Generates a new blueprint folder and starter descriptor.",
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Name of the blueprint to create.",
    )

    parser.set_defaults(func=run_blueprint_new)
