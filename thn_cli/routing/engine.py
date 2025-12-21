# thn_cli/routing/engine.py

"""
THN Routing Engine (Hybrid-Standard)
------------------------------------

RESPONSIBILITIES
----------------
Interpret a routing *tag* and optional ZIP payload into a structured,
deterministic routing decision.

This module is responsible for:
    • Loading merged routing configuration (rules + classifier)
    • Evaluating tag-pattern routing rules
    • Applying project-mapping inference
    • Performing lightweight ZIP content classification
    • Producing a stable routing decision dict

The routing decision shape is:

    {
        "project":    <str | None>,
        "module":     <str | None>,
        "category":   <str>,
        "subfolder":  <str>,
        "source":     "tag-pattern" | "project-map" | "classifier" | "default",
        "confidence": float,
    }

PIPELINE (DETERMINISTIC)
-----------------------
    1. Load routing rules + classifier configuration
    2. Apply tag-pattern routing
    3. Apply project-mapping inference
    4. Inspect ZIP contents via classifier (if provided)
    5. Emit routing decision (no side effects)

AUTHORITY BOUNDARY
------------------
This module is **authoritative for routing decisions only**.

It must:
    • Perform no filesystem writes
    • Perform no registry mutation
    • Perform no Sync apply behavior
    • Remain deterministic for identical inputs

All apply semantics belong to:
    • thn_cli.syncv2.engine

NON-GOALS
---------
• This module does NOT apply files
• This module does NOT validate payload integrity
• This module does NOT infer multi-file semantics
• This module does NOT enforce policy gates

FUTURE EXPANSION
----------------
The `envelope` parameter is reserved for future multi-asset or
cross-file inference. Its presence does not imply current usage.

Any expansion must preserve:
    • Determinism
    • Confidence monotonicity
    • Zero side effects
"""

from __future__ import annotations

import io
import zipfile
from typing import Any, Dict, List, Optional

from .classifier import classify_filetype
from .rules import load_routing_rules

# ---------------------------------------------------------------------------
# Simple Pattern Matching
# ---------------------------------------------------------------------------


def _matches_pattern(value: str, pattern: str) -> bool:
    """
    Evaluate minimal wildcard patterns.

    Supported:
        "name"   → exact match
        "name*"  → prefix match

    Rationale:
        Keep routing deterministic, transparent, and inexpensive.
    """
    if pattern.endswith("*"):
        return value.startswith(pattern[:-1])
    return value == pattern


# ---------------------------------------------------------------------------
# ZIP Introspection Helpers
# ---------------------------------------------------------------------------


def _extract_file_list(zip_bytes: Optional[bytes]) -> List[str]:
    """
    Return a list of file names found inside a ZIP byte stream.

    Behavior:
        • Returns [] if zip_bytes is None
        • Returns [] if ZIP is malformed
        • Never raises
    """
    if not zip_bytes:
        return []

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            return z.namelist()
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Routing Decision Engine
# ---------------------------------------------------------------------------


def auto_route(
    *,
    envelope: Any,  # reserved for future multi-file inference
    tag: str,
    zip_bytes: Optional[bytes],
    paths: Dict[str, str],
) -> Dict[str, Any]:
    """
    Compute routing metadata for a THN Sync operation.

    Args:
        envelope:
            Full envelope manifest (currently unused; future-reserved)

        tag:
            Routing tag chosen by CLI or automation
            (e.g. "sync_v2", "assets*", "project-alpha")

        zip_bytes:
            Raw ZIP payload bytes (optional but recommended)

        paths:
            Path dictionary from thn_cli.pathing.get_thn_paths()

    Returns:
        Deterministic routing decision dict.

    CONFIDENCE RULES
    ----------------
        • Tag-pattern routing establishes strong confidence
        • Project mapping augments project inference
        • Classifier overrides only if strictly higher confidence
    """

    # Normalize tag defensively
    tag = str(tag or "")

    # ------------------------------------------------------------------
    # Load routing configuration
    # ------------------------------------------------------------------
    cfg = load_routing_rules()
    routing_rules = cfg.get("rules", {})
    classifier_cfg = cfg.get("classifier", {})

    tag_patterns: Dict[str, Dict[str, Any]] = routing_rules.get("tag_patterns", {})
    project_map: Dict[str, str] = routing_rules.get("project_mappings", {})

    # Base defaults
    project: Optional[str] = None
    module: Optional[str] = None
    category: str = routing_rules.get("default_category", "assets")
    subfolder: str = routing_rules.get("default_subfolder", "incoming")

    source: str = "default"
    confidence: float = 0.0

    # ------------------------------------------------------------------
    # Phase 1 — Tag-Pattern Routing
    # ------------------------------------------------------------------
    for pattern, rule in tag_patterns.items():
        if _matches_pattern(tag, pattern):
            category = rule.get("category", category)
            subfolder = rule.get("subfolder", subfolder)
            source = "tag-pattern"
            confidence = 0.85  # Convention: pattern routing is authoritative
            break

    # ------------------------------------------------------------------
    # Phase 2 — Project Mapping
    # ------------------------------------------------------------------
    for pattern, proj_name in project_map.items():
        if _matches_pattern(tag, pattern):
            project = proj_name
            if confidence < 0.85:
                source = "project-map"
            break

    # ------------------------------------------------------------------
    # Phase 3 — Payload Classifier
    # ------------------------------------------------------------------
    file_list = _extract_file_list(zip_bytes)

    if file_list:
        # Convention: first file governs classification
        primary_name = file_list[0]
        cat_guess, conf = classify_filetype(
            zip_bytes=zip_bytes,
            filename=primary_name,
            config=classifier_cfg,
        )

        # Adopt classifier result only if strictly stronger
        if conf > confidence:
            category = cat_guess
            confidence = float(conf)
            source = "classifier"

    # ------------------------------------------------------------------
    # Final Routing Decision
    # ------------------------------------------------------------------
    return {
        "project": project,
        "module": module,
        "category": category,
        "subfolder": subfolder,
        "source": source,
        "confidence": float(confidence),
    }
