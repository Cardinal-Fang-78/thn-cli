#!/usr/bin/env python
"""
Developer-only advisory verification tool.

PURPOSE
-------
Verifies that **diagnostic-domain** CLI command modules remain structurally
non-execution-capable.

This tool is a **safety net** against accidental authority escalation such as:
    - importing execution engines into diagnostic commands
    - calling mutation primitives from diagnostic surfaces
    - introducing write/delete side effects in read-only command modules

This tool is intentionally **structural**, not inferential:
    - It checks for explicit forbidden imports / symbols / side-effect calls.
    - It does NOT perform call-graph analysis.
    - It does NOT attempt capability inference.
    - It does NOT “prove” correctness.

SCOPE (OPTION A — ACTIVE)
-------------------------
- Scans a targeted set of diagnostic command modules (explicit allowlist)
- Flags explicit forbidden imports and explicit mutation primitives
- Fails loudly on any match

OPTION B (FUTURE ONLY — NOT IMPLEMENTED)
---------------------------------------
A capability-oriented scan (import graph + exported surface classification)
may be introduced later as an explicit, opt-in advisory mode.

This script is structured to be Option B-capable without activating any
pre-wiring that could:
    - create hidden coupling
    - introduce dead-code maintenance burden
    - violate the “no simulated workflows / no inference” Tenet

INVARIANTS
----------
- Read-only
- Deterministic
- Non-authoritative
- Developer-only (not runtime, CI, or release gating)
- Fails loudly on any mismatch or parse ambiguity
- Never mutates repository state

EXIT CODES
----------
0 = No violations found
1 = Violations found
2 = Script or scan error
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

# ---------------------------------------------------------------------------
# Configuration (explicit, deterministic)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(".")
THN_CLI_ROOT = REPO_ROOT / "thn_cli"
COMMANDS_DIR = THN_CLI_ROOT / "commands"

# Explicit allowlist: diagnostic-domain command modules only.
#
# Notes:
# - This tool is a safety net, not an authoritative registry.
# - Keep this list small and intentional.
# - If you add a new diagnostic command registrar, add it here deliberately.
DIAGNOSTIC_COMMAND_MODULES: Tuple[str, ...] = (
    "commands_diag.py",
    "commands_inspect.py",
    "commands_drift.py",  # drift “inspection/control utilities” should remain non-mutating at the registrar layer
    "commands_registry_tools.py",  # inspection tooling (registrar should not mutate)
    "commands_routing.py",  # registrar should not apply; apply surfaces must be explicit and audited
    "commands_plugins.py",
    "commands_keys.py",
    "commands_list.py",
    "commands_init.py",  # deterministic setup; should not pull execution engines
    "commands_dev.py",  # developer tooling (still must not import execution engines unintentionally)
    "commands_hub.py",  # integration registrars should not apply/mutate without explicit policy
    # Add more diagnostic registrars intentionally as needed.
)

# Forbidden imports: execution/mutation engines that must never appear in
# diagnostic command registrars.
#
# IMPORTANT:
# Keep these as stable “domain import anchors”, not overly broad regexes.
FORBIDDEN_IMPORT_SUBSTRINGS: Tuple[str, ...] = (
    # Sync / apply engines
    "thn_cli.syncv2.engine",
    "apply_envelope_v2",
    "thn_cli.syncv2.apply",
    # Recovery / migrations / accept (execution domains)
    "thn_cli.recovery",
    "recover_apply",
    "thn_cli.migrations",
    "migrate_apply",
    "thn_cli.post_make.accept",
    "accept_drift",
    # Snapshot mutations (if registrar should not mutate)
    "thn_cli.snapshots",
    "write_snapshot",
    # Registry mutation surfaces (tooling registrars must not write)
    "thn_cli.registry",
    "registry_write",
)

# Forbidden mutation / side-effect primitives.
#
# This is intentionally conservative: the registrar layer should not be
# performing filesystem writes/deletes even if “developer-only”.
FORBIDDEN_CALL_PATTERNS: Tuple[Tuple[str, str], ...] = (
    # Path writes / deletes
    (r"\bPath\([^)]*\)\.write_text\s*\(", "Path.write_text"),
    (r"\bPath\([^)]*\)\.write_bytes\s*\(", "Path.write_bytes"),
    (r"\bPath\([^)]*\)\.unlink\s*\(", "Path.unlink"),
    (r"\bPath\([^)]*\)\.rename\s*\(", "Path.rename"),
    (r"\bPath\([^)]*\)\.replace\s*\(", "Path.replace"),
    (r"\bopen\s*\([^)]*,\s*['\"]w", "open(..., 'w*')"),
    (r"\bopen\s*\([^)]*,\s*['\"]a", "open(..., 'a*')"),
    # os-level deletes / renames
    (r"\bos\.remove\s*\(", "os.remove"),
    (r"\bos\.unlink\s*\(", "os.unlink"),
    (r"\bos\.rename\s*\(", "os.rename"),
    (r"\bos\.replace\s*\(", "os.replace"),
    (r"\bshutil\.rmtree\s*\(", "shutil.rmtree"),
    (r"\bshutil\.move\s*\(", "shutil.move"),
    (r"\bshutil\.copy\s*\(", "shutil.copy"),
    (r"\bshutil\.copytree\s*\(", "shutil.copytree"),
)

# Some command registrars will legitimately use argparse, json, sys, etc.
# No allowlist is required for safe imports; only forbidden checks are used.

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    relpath: str
    line_no: int
    kind: str
    detail: str
    line: str


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _die(message: str, *, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        _die(f"Failed to read file: {path} ({exc})")
    raise AssertionError("unreachable")


def _iter_target_files() -> List[Path]:
    if not COMMANDS_DIR.exists():
        _die(f"Commands directory not found: {COMMANDS_DIR}")

    files: List[Path] = []
    for name in DIAGNOSTIC_COMMAND_MODULES:
        p = COMMANDS_DIR / name
        if not p.exists():
            _die(
                "Diagnostic domain scan file missing from allowlist:\n"
                f"  expected: {p}\n"
                "If this module was renamed or removed, update the allowlist."
            )
        files.append(p)

    # Deterministic ordering
    return sorted(files, key=lambda x: x.as_posix())


def _relpath(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except Exception:
        return path.as_posix()


def _find_forbidden_imports(text: str, *, relpath: str) -> List[Finding]:
    findings: List[Finding] = []
    lines = text.splitlines()

    # Fast substring checks, then line attribution.
    forbidden_hits: List[str] = []
    for needle in FORBIDDEN_IMPORT_SUBSTRINGS:
        if needle in text:
            forbidden_hits.append(needle)

    if not forbidden_hits:
        return findings

    for i, line in enumerate(lines, start=1):
        for needle in forbidden_hits:
            if needle in line:
                findings.append(
                    Finding(
                        relpath=relpath,
                        line_no=i,
                        kind="forbidden_import_or_symbol",
                        detail=needle,
                        line=line.rstrip("\n"),
                    )
                )

    return findings


def _find_forbidden_calls(text: str, *, relpath: str) -> List[Finding]:
    findings: List[Finding] = []
    lines = text.splitlines()

    compiled: List[Tuple[re.Pattern[str], str]] = []
    for pattern, label in FORBIDDEN_CALL_PATTERNS:
        try:
            compiled.append((re.compile(pattern), label))
        except re.error as exc:
            _die(f"Invalid regex in FORBIDDEN_CALL_PATTERNS ({label}): {exc}")

    for i, line in enumerate(lines, start=1):
        for rx, label in compiled:
            if rx.search(line):
                findings.append(
                    Finding(
                        relpath=relpath,
                        line_no=i,
                        kind="forbidden_side_effect_call",
                        detail=label,
                        line=line.rstrip("\n"),
                    )
                )

    return findings


def scan_files(paths: Sequence[Path]) -> List[Finding]:
    """
    Option A (active):
        Structural scan for forbidden imports/symbols and forbidden
        side-effect primitives within diagnostic command registrars.
    """
    all_findings: List[Finding] = []

    for path in paths:
        text = _read_text(path)
        rp = _relpath(path)

        all_findings.extend(_find_forbidden_imports(text, relpath=rp))
        all_findings.extend(_find_forbidden_calls(text, relpath=rp))

    return all_findings


# ---------------------------------------------------------------------------
# Option B (future-only, disabled by design)
# ---------------------------------------------------------------------------


def scan_import_capabilities_future_only(*_: object) -> None:
    """
    FUTURE (NOT IMPLEMENTED — Option B concept only)

    A future advisory mode could:
        - build a conservative import graph starting from command registrars
        - map imported modules to declared authority boundaries
        - report “capability proximity” without inferring behavior

    This is intentionally NOT implemented now to avoid:
        - inference-driven tooling
        - maintenance tax / dead code
        - accidental activation or coupling

    If introduced later:
        - must be explicit opt-in (flag)
        - must remain advisory and non-authoritative
        - must not gate CI unless separately approved
    """
    raise NotImplementedError("Option B capability scan is intentionally not implemented.")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_findings(findings: Sequence[Finding]) -> None:
    by_file: Dict[str, List[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.relpath, []).append(f)

    for relpath in sorted(by_file.keys()):
        print(f"{relpath}")
        for f in sorted(by_file[relpath], key=lambda x: (x.line_no, x.kind, x.detail)):
            print(f"  L{f.line_no:>4}  {f.kind}: {f.detail}")
            print(f"        {f.line.strip()}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> None:
    # This tool intentionally takes no flags today.
    # If flags are ever added, they must preserve determinism and remain advisory.
    _ = argv or sys.argv[1:]

    targets = _iter_target_files()
    findings = scan_files(targets)

    if not findings:
        print(
            "OK: Diagnostic command registrars contain no forbidden execution imports or side effects."
        )
        sys.exit(0)

    print("DIAGNOSTIC DOMAIN PURITY VIOLATIONS DETECTED\n")
    print("The following diagnostic command registrar modules appear to include")
    print("execution-domain imports/symbols or mutation primitives.\n")
    _print_findings(findings)

    print("Meaning:")
    print("  - Diagnostic command registrars must remain observational/read-only.")
    print("  - Any execution/apply/mutation capability must be explicit and audited.")
    sys.exit(1)


if __name__ == "__main__":
    main()
