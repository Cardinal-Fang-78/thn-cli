# thn_cli/commands/commands_inspect.py

"""
THN Inspect Command Group (Hybrid-Standard)
==========================================

RESPONSIBILITIES
----------------
Provides **read-only diagnostic inspection commands** for THN state and
Sync V2 artifacts that are NOT part of the apply or execution pipeline.

This module owns CLI entrypoints for:
    • thn inspect scaffold
    • thn inspect cdc

It is responsible for:
    • Argument parsing and CLI wiring
    • Delegating all inspection logic to read-only helpers
    • Emitting deterministic, structured diagnostic output

NON-GOALS
---------
This module MUST NOT:
    • Apply Sync envelopes
    • Mutate filesystem state
    • Enforce routing or policy
    • Perform recovery or repair
    • Contain business logic for CDC inspection

CDC inspection logic is delegated to:
    thn_cli.syncv2.delta.inspectors

CONTRACT STATUS
---------------
⚠️ LOCKED CLI DIAGNOSTIC SURFACE

All JSON output emitted by this command group is:
    • Externally visible
    • Golden-tested
    • Intended for CLI, CI, and future GUI consumption

Any changes to:
    • output keys
    • nesting structure
    • semantic meaning

MUST be accompanied by updated golden tests or a versioned surface change.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from thn_cli.contracts.errors import SYSTEM_CONTRACT, USER_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.pathing import get_thn_paths
from thn_cli.scaffolds.drift_preview import preview_scaffold_drift
from thn_cli.syncv2.delta.inspectors import (
    check_payload_completeness,
    snapshot_chunk_health,
    summarize_snapshot,
)
from thn_cli.syncv2.envelope import load_envelope_from_file

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _emit(obj: Dict[str, Any]) -> int:
    print(json.dumps(obj, indent=4, ensure_ascii=False))
    return 0


def _require_existing_dir(target_path: Path) -> None:
    if not target_path.exists():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path does not exist: {target_path}",
        )
    if not target_path.is_dir():
        raise CommandError(
            contract=USER_CONTRACT,
            message=f"Path is not a directory: {target_path}",
        )


def _require_under_thn_root(target_path: Path) -> None:
    paths = get_thn_paths()
    thn_root = paths.get("root", "")
    if isinstance(thn_root, str) and thn_root.strip():
        try:
            target_path.resolve().relative_to(Path(thn_root).resolve())
        except Exception:
            raise CommandError(
                contract=USER_CONTRACT,
                message=("Target is not under THN root: " f"{target_path} (root={thn_root})"),
            )


def _derive_cdc_target_name(manifest: Dict[str, Any]) -> str:
    """
    Derive a receiver/target name for snapshot diagnostics.

    Preference order:
        1) manifest["meta"]["target"] if present
        2) manifest["target"] if present
        3) "web" fallback
    """
    meta = manifest.get("meta", {}) or {}
    if isinstance(meta, dict):
        t = meta.get("target")
        if isinstance(t, str) and t.strip():
            return t.strip()

    t2 = manifest.get("target")
    if isinstance(t2, str) and t2.strip():
        return t2.strip()

    return "web"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def run_inspect_scaffold(args: argparse.Namespace) -> int:
    target_path = Path(args.path)

    _require_existing_dir(target_path)
    _require_under_thn_root(target_path)

    try:
        result = preview_scaffold_drift(target_path)
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to inspect scaffold.",
        ) from exc

    return _emit(result)


def run_inspect_cdc(args: argparse.Namespace) -> int:
    """
    Inspect a CDC-delta envelope with additional diagnostics.

    CONTRACT
    --------
    Diagnostic-only and read-only:
        • MUST NOT mutate filesystem
        • MUST produce deterministic JSON in --json mode
    """
    zip_path = args.zip
    json_mode = bool(args.json)

    if not zip_path:
        raise CommandError(
            contract=USER_CONTRACT,
            message="Envelope path is required.",
        )

    try:
        env = load_envelope_from_file(zip_path)
        manifest = env.get("manifest", {}) or {}
        payload_zip = env.get("payload_zip")

        mode = manifest.get("mode", "raw-zip")
        target = _derive_cdc_target_name(manifest)

        if mode == "cdc-delta":
            completeness = check_payload_completeness(
                manifest=manifest,
                payload_zip=str(payload_zip) if payload_zip else "",
            )
        else:
            completeness = {"expected": 0, "present": 0, "missing": [], "extra": []}

        snap = summarize_snapshot(target)
        chunk = snapshot_chunk_health(target)

        inspect_block: Dict[str, Any] = {
            "source_path": env.get("source_path"),
            "mode": mode,
            "cdc_diagnostics": {
                "payload_completeness": completeness,
                "snapshot": {
                    "target": target,
                    **snap,
                },
                "chunk_health": {
                    "target": target,
                    **chunk,
                },
            },
        }

    except CommandError:
        raise
    except Exception as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Failed to inspect CDC envelope.",
            extra_suggestions=[str(exc)],
        ) from exc

    if json_mode:
        return _emit({"status": "OK", "inspect": inspect_block})

    print("\nTHN Inspect CDC\n")
    print(json.dumps(inspect_block, indent=4, ensure_ascii=False))
    print()
    return 0


# ---------------------------------------------------------------------------
# Command Registration
# ---------------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "inspect",
        help="Inspect diagnostic state (read-only).",
        description="Read-only inspection helpers for scaffolds and Sync V2 envelopes.",
    )

    sub = parser.add_subparsers(dest="inspect_cmd", required=True)

    p_scaffold = sub.add_parser("scaffold", help="Inspect a scaffold directory.")
    p_scaffold.add_argument("path", help="Scaffold directory to inspect.")
    p_scaffold.set_defaults(func=run_inspect_scaffold)

    p_cdc = sub.add_parser(
        "cdc",
        help="Inspect a CDC-delta envelope (diagnostic-only).",
        description="Read-only CDC-delta envelope inspection with payload completeness and snapshot diagnostics.",
    )
    p_cdc.add_argument("zip", help="Path to the CDC-delta envelope ZIP.")
    p_cdc.add_argument("--json", action="store_true", help="Emit structured JSON output.")
    p_cdc.set_defaults(func=run_inspect_cdc)

    parser.set_defaults(func=lambda args: parser.print_help())
