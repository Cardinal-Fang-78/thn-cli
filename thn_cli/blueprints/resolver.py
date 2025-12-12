from .manager import BlueprintError, get_blueprint


def resolve_blueprint(name: str):
    """Returns the validated, loaded blueprint dict."""
    bp = get_blueprint(name)
    if not isinstance(bp, dict):
        raise BlueprintError(f"Invalid blueprint format for '{name}'")
    return bp
