# C:\THN\core\cli\thn_cli\blueprints\renderer.py

import os

from jinja2 import (Environment, FileSystemLoader, StrictUndefined,
                    TemplateError)


def _build_environment(search_path: str) -> Environment:
    """
    Internal helper: construct a Jinja2 environment rooted at `search_path`.
    """
    return Environment(
        loader=FileSystemLoader(search_path),
        undefined=StrictUndefined,  # Fail on missing variables
        autoescape=False,  # Raw text files, not HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(template_content: str, variables: dict) -> str:
    """
    Render an inline Jinja2 template string with the given variables.
    Used for:
      - Rendering template *contents*
      - Rendering destination paths
    """
    # Create a minimal environment for inline text
    env = Environment(
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    try:
        tmpl = env.from_string(template_content)
        return tmpl.render(**variables)
    except TemplateError as exc:
        raise TemplateError(f"Jinja2 error: {exc}") from exc


def render_file_template(template_path: str, variables: dict) -> str:
    """
    Render a template located on disk.

    template_path: Absolute path to the template file.
    """
    search_root = os.path.dirname(template_path)
    filename = os.path.basename(template_path)

    env = _build_environment(search_root)

    try:
        template = env.get_template(filename)
        return template.render(**variables)
    except TemplateError as exc:
        raise TemplateError(
            f"Error rendering template file '{template_path}': {exc}"
        ) from exc
