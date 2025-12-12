"""
THN Routing Integration Layer (Hybrid-Standard)
===============================================

This module is the SINGLE authoritative entry point for all routing
operations performed by:

    • Sync V2 executor / engine
    • Blueprint engine
    • Tasks subsystem
    • UI subsystem
    • Hub subsystem
    • Developer tooling

It unifies:
    • Routing rules (rules.py)
    • Classifier configuration (routing_config.py)
    • Hybrid-Standard routing engine (engine.py)

This prevents subsystems from implementing ad-hoc routing logic
and guarantees future upgrade compatibility.

Public API:

    from thn_cli.routing.integration import resolve_routing

    decision = resolve_routing(
        tag="web-assets",
        zip_bytes=payload_bytes,
        paths=get_thn_paths()
    )
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from thn_cli.routing.engine import auto_route
from thn_cli.routing.rules import load_routing_rules
from thn_cli.routing_config import load_routing_config

# ---------------------------------------------------------------------------
# Final Routing API
# ---------------------------------------------------------------------------


def resolve_routing(
    *,
    tag: str,
    zip_bytes: Optional[bytes],
    paths: Dict[str, str],
) -> Dict[str, Any]:
    """
    Produce a complete routing decision:

        {
            "project": <str|None>,
            "module": <str|None>,
            "category": <str>,
            "subfolder": <str|None>,
            "source": <"tag-pattern"|"project-map"|"classifier"|"default">,
            "confidence": <float>,
            "target": <"web"|"cli"|"docs">
        }

    The decision integrates:
        • Declarative routing rules (rules.py)
        • Classifier config (routing_config.py)
        • Hybrid-Standard routing engine (engine.py)
    """

    # --------------------------------------------------------------
    # Load rule set & classifier config bundle
    # --------------------------------------------------------------
    rule_cfg = load_routing_rules(paths)
    config_bundle = load_routing_config(paths)

    # The routing engine consumes only the merged config bundle.
    # (classifier_cfg is used internally by engine/classifier modules)
    # Future support will merge config_bundle["rules"] into tag-pattern routing.

    # --------------------------------------------------------------
    # Run the Hybrid-Standard routing engine
    # --------------------------------------------------------------
    decision = auto_route(
        envelope=None,  # reserved for future multi-file routing
        tag=tag,
        zip_bytes=zip_bytes,
        paths=paths,
    )

    # decision returns: project, module, category, subfolder, source, confidence

    # --------------------------------------------------------------
    # Determine final high-level TARGET (web / cli / docs)
    # --------------------------------------------------------------
    tag_routes = rule_cfg.get("tag_routes", {})
    default_target = rule_cfg.get("default_target", "web")

    final_target: Optional[str] = None

    for pattern, cfg in tag_routes.items():
        # Prefix match keeps rules simple and predictable
        if tag.startswith(pattern):
            final_target = cfg.get("target")
            break

    if final_target is None:
        final_target = default_target

    # --------------------------------------------------------------
    # Normalize and finalize routing object
    # --------------------------------------------------------------
    result = {
        "project": decision.get("project"),
        "module": decision.get("module"),
        "category": decision.get("category") or "assets",
        "subfolder": decision.get("subfolder"),
        "source": decision.get("source") or "default",
        "confidence": float(decision.get("confidence", 0.0)),
        "target": final_target,
    }

    return result
