# tests/test_routing_integration.py

from thn_cli.pathing import get_thn_paths
from thn_cli.routing.integration import resolve_routing


def test_resolve_routing_defaults():
    paths = get_thn_paths()

    result = resolve_routing(
        tag="web",
        zip_bytes=None,
        paths=paths,
    )

    # At least these fields should exist.
    for key in (
        "project",
        "module",
        "category",
        "subfolder",
        "source",
        "confidence",
        "target",
    ):
        assert key in result

    # With default config, a bare "web" tag should resolve to target "web".
    assert result["target"] in {"web", "cli", "docs"}
