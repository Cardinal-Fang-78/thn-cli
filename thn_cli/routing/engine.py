"""
THN Routing Engine (Hybrid-Standard)
------------------------------------

Purpose
-------
Interpret a routing *tag* and optional ZIP payload into a structured,
future-safe routing decision dict:

    {
        "project":   <str | None>,
        "module":    <str | None>,
        "category":  <str>,
        "subfolder": <str>,
        "source":    "tag-pattern" | "project-map" | "classifier" | "default",
        "confidence": float,
    }

Pipeline (deterministic):
    1. Load merged routing configuration (rules + classifier)
    2. Match tag-pattern routing
    3. Match project-mapping routing
    4. Inspect ZIP contents and apply content classifier
    5. Produce routing decision object (no side effects)

Notes
-----
• The engine performs *no* filesystem writes.
• The envelope parameter is reserved for future multi-asset inference.
• Both raw-zip and CDC-delta envelopes use this engine uniformly.
• Confidence is monotonic: higher layers override lower ones only when strictly greater.
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
        Keep routing deterministic and inexpensive.
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
    If the buffer is missing or malformed, fail gracefully.
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
    envelope: Any,  # placeholder for future multi-file inference
    tag: str,
    zip_bytes: Optional[bytes],
    paths: Dict[str, str],
) -> Dict[str, Any]:
    """
    Compute routing metadata for a THN Sync operation.

    Args:
        envelope:   Full envelope manifest (currently unused)
        tag:        Tag chosen by the user or CLI behavior (e.g., "sync_v2")
        zip_bytes:  Raw ZIP payload (optional but recommended)
        paths:      Path dictionary from thn_cli.pathing.get_thn_paths()

    Returns:
        Routing decision dict (project/module/category/subfolder).

    Deterministic rules:
        • Tag-pattern rules override defaults.
        • Project mappings override project=None.
        • Classifier overrides only if higher confidence.
    """

    # ------------------------------------------------------------------
    # Load merged routing configuration
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
            confidence = 0.85  # convention: pattern routing is authoritative
            break

    # ------------------------------------------------------------------
    # Phase 2 — Project-Inference Layer
    # ------------------------------------------------------------------
    for pattern, proj_name in project_map.items():
        if _matches_pattern(tag, pattern):
            project = proj_name
            # Only override source if nothing stronger is active
            if confidence < 0.85:
                source = "project-map"
            break

    # ------------------------------------------------------------------
    # Phase 3 — Payload Classifier (ZIP)
    # ------------------------------------------------------------------
    file_list = _extract_file_list(zip_bytes)

    if file_list:
        # Convention: first file's semantic class governs routing
        primary_name = file_list[0]
        cat_guess, conf = classify_filetype(
            zip_bytes=zip_bytes,
            filename=primary_name,
            config=classifier_cfg,
        )

        # Only adopt classifier result if strictly more confident
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
