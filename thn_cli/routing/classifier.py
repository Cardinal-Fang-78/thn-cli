"""
THN Routing Classifier (Hybrid-Standard)
----------------------------------------

Purpose:
    Provide deterministic, pluggable file-type classification for routing.
    This version matches the Hybrid-Standard routing rules schema:

        classifier = {
            "patterns": {
                "*.png":  "images",
                "*.jpg":  "images",
                "*.md":   "docs",
                "*.css":  "styles",
                ...
            },
            "weights": {
                "images": 0.70,
                "docs":   0.55,
                "styles": 0.60,
                ...
            },
            "minimum_confidence": 0.50
        }

Classifier ALWAYS returns:
    (category: str, confidence: float)

Classifier NEVER throws.
"""

from __future__ import annotations

import fnmatch
import os
from typing import Any, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_ext(filename: str) -> str:
    """
    Return normalized lowercase extension.
    Examples:
        photo.PNG → .png
        archive.tar.gz → .gz
        noext → ""
    """
    _, ext = os.path.splitext(filename)
    return ext.lower().strip()


# ---------------------------------------------------------------------------
# Matching Logic
# ---------------------------------------------------------------------------


def _match_by_patterns(
    filename: str,
    patterns: Dict[str, str],
) -> Optional[str]:
    """
    Attempt to match filename or extension against declared classifier patterns.

    Example patterns:
        "*.png": "images"
        "*.css": "styles"

    Returns:
        category (str) or None if no match is found.
    """
    # First pass: exact extension (fast)
    ext = _normalize_ext(filename)
    if ext:
        ext_pattern = f"*{ext}"
        if ext_pattern in patterns:
            return patterns[ext_pattern]

    # Second pass: glob match
    for pattern, category in patterns.items():
        if fnmatch.fnmatch(filename.lower(), pattern.lower()):
            return category

    return None


# ---------------------------------------------------------------------------
# Main Classifier API
# ---------------------------------------------------------------------------


def classify_filetype(
    zip_bytes: Optional[bytes],
    filename: str,
    classifier_cfg: Dict[str, Any],
) -> Tuple[str, float]:
    """
    Determine routing category + confidence level.

    Parameters:
        zip_bytes      (unused, placeholder for future ML support)
        filename       first file inside ZIP payload
        classifier_cfg rules loaded from routing.rules.load_routing_rules()

    Returns:
        (category: str, confidence: float)
    """

    patterns = classifier_cfg.get("patterns", {})
    weights = classifier_cfg.get("weights", {})
    min_conf = float(classifier_cfg.get("minimum_confidence", 0.50))

    # --------------------------------------------------------------
    # Phase 1: match against configured patterns
    # --------------------------------------------------------------
    category = _match_by_patterns(filename, patterns)
    if category:
        # Confidence uses category weight if available
        conf = float(weights.get(category, min_conf))
        conf = max(conf, min_conf)
        return category, conf

    # --------------------------------------------------------------
    # Phase 2: fallback by extension only
    # --------------------------------------------------------------
    ext = _normalize_ext(filename)
    if ext:
        # crude fallback: extension → pseudo-category
        pseudo_category = ext.lstrip(".")
        conf = float(weights.get(pseudo_category, min_conf))
        conf = max(conf, min_conf)
        return pseudo_category, conf

    # --------------------------------------------------------------
    # Phase 3: full fallback when filename has no extension
    # --------------------------------------------------------------
    return "assets", min_conf
