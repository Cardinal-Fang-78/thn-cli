"""
Migration hooks package.

Hooks are optional Python modules referenced by declarative specs.
They must expose:

    def run(*, root: Path, context: dict) -> dict

Return value must be JSON-serializable.
"""
