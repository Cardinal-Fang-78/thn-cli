"""
Indentation Diagnostic (Extended)
---------------------------------

Provides deeper indentation + structural checks used for debugging
template rendering, blueprint expansion, or misaligned multi-line
content inside THN tools.

This diagnostic expands on `indent_diag` by providing:

    • Indentation depth analysis per line
    • Leading/trailing whitespace detection
    • Mixed indentation detection (tabs/spaces)
    • ASCII visual alignment map
    • Line-indexed output for precise debugging

Used exclusively for diagnostics and never during normal THN operation.
"""

from __future__ import annotations

from typing import Dict, Any, List

from .diagnostic_result import DiagnosticResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calc_indent_depth(line: str) -> int:
    """
    Count leading spaces. Tabs count as 4 spaces for diagnostic purposes.
    """
    depth = 0
    for ch in line:
        if ch == " ":
            depth += 1
        elif ch == "\t":
            depth += 4
        else:
            break
    return depth


def _detect_mixed_indent(line: str) -> bool:
    """
    Return True if indentation uses both spaces and tabs.
    """
    leading = []
    for ch in line:
        if ch in (" ", "\t"):
            leading.append(ch)
        else:
            break
    return (" " in leading) and ("\t" in leading)


def _line_summary(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Build per-line indentation metrics.
    """
    summary: List[Dict[str, Any]] = []

    for idx, raw in enumerate(lines, start=1):
        text = raw.rstrip("\n")
        indent = _calc_indent_depth(text)
        has_mixed = _detect_mixed_indent(text)
        trailing_ws = (len(text) != len(text.rstrip(" \t")))
        empty = (text.strip() == "")

        summary.append({
            "line": idx,
            "empty": empty,
            "indent_depth": indent,
            "mixed_indent": has_mixed,
            "trailing_whitespace": trailing_ws,
            "visual": (" " * indent) + "▕" + text[indent:],
        })

    return summary


# ---------------------------------------------------------------------------
# Diagnostic Entry Point
# ---------------------------------------------------------------------------

def diagnose_indent_extended(text: str) -> Dict[str, Any]:
    """
    Hybrid-standard extended indentation diagnostic.

    Input:
        raw text block

    Output:
        DiagnosticResult with:
            • line-by-line summaries
            • min/max indentation depth
            • mixed-indent locations
            • trailing-whitespace locations
            • structural statistics
    """
    if not isinstance(text, str):
        return DiagnosticResult(
            component="indent_extended",
            ok=False,
            errors=["Input text must be a string."],
            details={"input_type": str(type(text))},
        ).as_dict()

    lines = text.splitlines(True)
    summary = _line_summary(lines)

    indent_values = [s["indent_depth"] for s in summary]
    mixed_lines = [s for s in summary if s["mixed_indent"]]
    trailing_ws = [s for s in summary if s["trailing_whitespace"]]

    details = {
        "line_count": len(lines),
        "min_indent": min(indent_values) if indent_values else 0,
        "max_indent": max(indent_values) if indent_values else 0,
        "mixed_indent_lines": [m["line"] for m in mixed_lines],
        "trailing_whitespace_lines": [t["line"] for t in trailing_ws],
        "summary": summary,
    }

    ok = not mixed_lines and not trailing_ws

    warnings = []
    if mixed_lines:
        warnings.append("Mixed indentation detected (tabs + spaces).")
    if trailing_ws:
        warnings.append("Trailing whitespace detected.")

    return DiagnosticResult(
        component="indent_extended",
        ok=ok,
        warnings=warnings,
        errors=[],
        details=details,
    ).as_dict()
