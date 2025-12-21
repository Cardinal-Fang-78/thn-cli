# thn_cli/routing/classifier.py

"""
THN Routing Classifier (Hybrid-Standard)
----------------------------------------

RESPONSIBILITIES
----------------
Provide deterministic, pluggable file-type classification to assist
the routing engine in category selection.

This classifier:
    • Matches filenames against configured glob patterns
    • Applies category-specific confidence weights
    • Provides a stable fallback when no pattern matches
    • Never raises exceptions

Classifier configuration schema:

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

RETURN CONTRACT
---------------
The classifier ALWAYS returns:

    (category: str, confidence: float)

AUTHORITY BOUNDARY
------------------
This module is **non-authoritative**.

It must:
    • Perform no filesystem writes
    • Perform no routing decisions by itself
    • Perform no payload validation
    • Never raise exceptions

Final routing authority belongs to:
    • thn_cli.routing.engine

FUTURE EXPANSION
----------------
The `zip_bytes` parameter is reserved for future content-aware
classification (e.g., ML-based inference).

Its presence does NOT imply:
    • Current ZIP inspection
    • Heuristic inference
    • Non-deterministic behavior

Any future expansion must preserve:
    • Determinism
    • Zero side effects
    • Stable return shape
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
    Return normalized lowercase file extension.

    Examples:
        photo.PNG        → ".png"
        archive.tar.gz   → ".gz"
        README           → ""
    """
    _, ext = os.path.splitext(filename or "")
    return ext.lower().strip()


# ---------------------------------------------------------------------------
# Matching Logic
# ---------------------------------------------------------------------------


def _match_by_patterns(
    filename: str,
    patterns: Dict[str, str],
) -> Optional[str]:
    """
    Attempt to match a filename against configured classifier patterns.

    Matching strategy:
        1. Fast-path extension lookup ("*.png")
        2. Full glob match via fnmatch

    Returns:
        category (str) if matched, otherwise None
    """
    filename = filename or ""

    # Fast-path: exact extension match
    ext = _normalize_ext(filename)
    if ext:
        ext_pattern = f"*{ext}"
        if ext_pattern in patterns:
            return patterns[ext_pattern]

    # Fallback: glob match
    for pattern, category in patterns.items():
        if fnmatch.fnmatch(filename.lower(), pattern.lower()):
            return category

    return None


# ---------------------------------------------------------------------------
# Public Classifier API
# ---------------------------------------------------------------------------


def classify_filetype(
    zip_bytes: Optional[bytes],
    filename: str,
    classifier_cfg: Dict[str, Any],
) -> Tuple[str, float]:
    """
    Determine routing category and confidence level.

    Parameters:
        zip_bytes:
            Reserved for future content-aware classification (unused)

        filename:
            Logical filename extracted from payload

        classifier_cfg:
            Classifier configuration loaded from routing rules

    Returns:
        (category: str, confidence: float)

    This function:
        • Is deterministic
        • Never raises
        • Always returns a valid category and confidence
    """

    patterns = classifier_cfg.get("patterns", {}) or {}
    weights = classifier_cfg.get("weights", {}) or {}
    min_conf = float(classifier_cfg.get("minimum_confidence", 0.50))

    # --------------------------------------------------------------
    # Phase 1 — Pattern-based classification
    # --------------------------------------------------------------
    category = _match_by_patterns(filename, patterns)
    if category:
        conf = float(weights.get(category, min_conf))
        conf = max(conf, min_conf)
        return category, conf

    # --------------------------------------------------------------
    # Phase 2 — Extension-only fallback
    # --------------------------------------------------------------
    ext = _normalize_ext(filename)
    if ext:
        pseudo_category = ext.lstrip(".")
        conf = float(weights.get(pseudo_category, min_conf))
        conf = max(conf, min_conf)
        return pseudo_category, conf

    # --------------------------------------------------------------
    # Phase 3 — Absolute fallback
    # --------------------------------------------------------------
    return "assets", min_conf
