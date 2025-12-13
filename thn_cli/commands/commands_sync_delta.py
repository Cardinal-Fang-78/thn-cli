# thn_cli/commands_sync_delta.py

"""
THN Sync V2 – Delta Commands (Hybrid-Standard)
==============================================

Adds a consistent Hybrid-Standard interface for all CDC-delta operations:

    • Build delta manifests
    • Inspect manifests
    • Diff two snapshots
    • Inspect per-file chunking
    • Examine chunk-store reference usage
    • Perform safe/dangerous GC with structured reporting

All commands support:
    --json     (machine-readable output)
    Unified error model
    Consistent diagnostic structure
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Tuple

# Snapshot state
import thn_cli.syncv2.state as sync_state

# Delta builders / inspectors
from thn_cli.syncv2.delta.make_delta import build_cdc_delta_manifest, inspect_file_chunks
from thn_cli.syncv2.delta.store import get_chunk_path
from thn_cli.syncv2.delta.visuals import (
    visualize_chunk_map,
    visualize_manifest_full,
    visualize_snapshot_diff,
)

# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------


def _j(obj: Any) -> None:
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def _err(msg: str, json_mode: bool, **kw) -> int:
    if json_mode:
        _j({"status": "ERROR", "message": msg, **kw})
        return 1
    print(f"\nError: {msg}\n")
    return 1


def _ok(obj: Dict[str, Any], json_mode: bool) -> int:
    if json_mode:
        _j(obj)
        return 0
    # Text mode: just pretty-print JSON
    print(json.dumps(obj, indent=4, ensure_ascii=False))
    print()
    return 0


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _load_manifest(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def run_delta_build(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)
    root = os.path.abspath(args.root)
    target = args.target

    if not os.path.isdir(root):
        return _err("Source root does not exist or is not a directory.", json_mode, root=root)

    try:
        manifest = build_cdc_delta_manifest(
            source_root=root,
            target_name=target,
        )
    except Exception as exc:
        return _err("Failed to build CDC delta manifest.", json_mode, error=str(exc))

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except Exception as exc:
            return _err(
                "Failed to write output file.",
                json_mode,
                path=args.output,
                error=str(exc),
            )

        return _ok(
            {
                "status": "OK",
                "message": "manifest written",
                "output": args.output,
                "entries": len(manifest.get("entries", [])),
                "manifest": manifest,
            },
            json_mode,
        )

    # If no output path → print manifest
    return _ok(
        {
            "status": "OK",
            "entries": len(manifest.get("entries", [])),
            "manifest": manifest,
        },
        json_mode,
    )


# ---------------------------------------------------------------------------
# Inspect
# ---------------------------------------------------------------------------


def run_delta_inspect(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)

    try:
        manifest = _load_manifest(args.manifest)
    except Exception as exc:
        return _err("Failed to load manifest.", json_mode, path=args.manifest, error=str(exc))

    if json_mode:
        return _ok({"status": "OK", "manifest": manifest}, json_mode)

    # Text visualization
    print(visualize_manifest_full(manifest))
    print()
    return 0


# ---------------------------------------------------------------------------
# Diff: compare two manifests
# ---------------------------------------------------------------------------


def run_delta_diff(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)

    try:
        before = _load_manifest(args.before)
        after = _load_manifest(args.after)
    except Exception as exc:
        return _err("Failed to load manifests.", json_mode, error=str(exc))

    if json_mode:
        return _ok(
            {
                "status": "OK",
                "before_entries": len(before.get("entries", [])),
                "after_entries": len(after.get("entries", [])),
                "diff_text": visualize_snapshot_diff(before, after),
            },
            json_mode,
        )

    print(visualize_snapshot_diff(before, after))
    print()
    return 0


# ---------------------------------------------------------------------------
# Chunks (per-file)
# ---------------------------------------------------------------------------


def run_delta_chunks(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)

    file_path = os.path.abspath(args.file)
    target = args.target

    if not os.path.isfile(file_path):
        return _err("File not found.", json_mode, file=file_path)

    try:
        sizes, ids = inspect_file_chunks(file_path, target)
    except Exception as exc:
        return _err("Failed chunk inspection.", json_mode, error=str(exc))

    if json_mode:
        return _ok(
            {
                "status": "OK",
                "file": file_path,
                "target": target,
                "chunk_count": len(ids),
                "chunks": [
                    {
                        "id": cid,
                        "size": sz,
                        "path": get_chunk_path(target, cid),
                    }
                    for cid, sz in zip(ids, sizes)
                ],
            },
            json_mode,
        )

    # Text mode output
    print(f"Chunk Structure for:\n  {file_path}\n")
    print("Chunk Map:")
    print(f"  {visualize_chunk_map(ids)}\n")

    print("Chunks:")
    for cid, sz in zip(ids, sizes):
        print(f"  {cid[:8]}...   {sz} bytes  ({get_chunk_path(target, cid)})")
    print()
    return 0


# ---------------------------------------------------------------------------
# GC Utility
# ---------------------------------------------------------------------------


def _scan_chunk_store(target: str) -> Tuple[List[str], List[str]]:
    root = os.environ.get("THN_SYNC_ROOT", r"C:\THN\sync")
    chunk_root = os.path.join(root, "chunks", target)

    # All chunks present
    all_ids: List[str] = []
    if os.path.isdir(chunk_root):
        for shard in os.listdir(chunk_root):
            shard_dir = os.path.join(chunk_root, shard)
            if not os.path.isdir(shard_dir):
                continue
            for name in os.listdir(shard_dir):
                all_ids.append(name)

    # Referenced chunks
    snap = sync_state.load_last_manifest(target)
    ref = set()
    if snap:
        for e in snap.get("entries", []) or []:
            for cid in e.get("chunks", []) or []:
                ref.add(cid)

    return all_ids, sorted(ref)


# ---------------------------------------------------------------------------
# GC
# ---------------------------------------------------------------------------


def run_delta_gc(args: argparse.Namespace) -> int:
    json_mode = bool(args.json)
    target = args.target

    all_ids, ref_ids = _scan_chunk_store(target)
    ref_set = set(ref_ids)

    unused = [cid for cid in all_ids if cid not in ref_set]

    if not args.apply:
        # safe mode
        return _ok(
            {
                "status": "OK",
                "mode": "safe",
                "target": target,
                "total_chunks": len(all_ids),
                "referenced_chunks": len(ref_ids),
                "unused_chunks": len(unused),
                "unused_list": unused,
            },
            json_mode,
        )

    # dangerous mode — delete
    root = os.environ.get("THN_SYNC_ROOT", r"C:\THN\sync")
    base = os.path.join(root, "chunks", target)

    removed = 0
    for cid in unused:
        shard = cid[:2] if len(cid) >= 2 else "xx"
        path = os.path.join(base, shard, cid)
        try:
            if os.path.isfile(path):
                os.remove(path)
                removed += 1
        except Exception:
            pass

    return _ok(
        {
            "status": "OK",
            "mode": "apply",
            "target": target,
            "removed": removed,
            "total_unused": len(unused),
        },
        json_mode,
    )


# ---------------------------------------------------------------------------
# Subparser Wiring
# ---------------------------------------------------------------------------


def add_subparser(parent: argparse._SubParsersAction) -> None:
    parser = parent.add_parser(
        "delta",
        help="CDC-delta inspection, manifest building, chunk-store tools.",
        description="Hybrid-Standard CDC-delta command suite.",
    )

    sub = parser.add_subparsers(dest="delta_cmd", required=True)

    # --------------------- build ---------------------
    p_build = sub.add_parser("build", help="Build a CDC-delta manifest.")
    p_build.add_argument("--root", required=True)
    p_build.add_argument("--target", required=True)
    p_build.add_argument("--output", "-o")
    p_build.add_argument("--json", action="store_true")
    p_build.set_defaults(func=run_delta_build)

    # --------------------- inspect -------------------
    p_inspect = sub.add_parser("inspect", help="Inspect a delta manifest.")
    p_inspect.add_argument("manifest")
    p_inspect.add_argument("--json", action="store_true")
    p_inspect.set_defaults(func=run_delta_inspect)

    # --------------------- diff ----------------------
    p_diff = sub.add_parser("diff", help="Diff two CDC-delta manifests.")
    p_diff.add_argument("before")
    p_diff.add_argument("after")
    p_diff.add_argument("--json", action="store_true")
    p_diff.set_defaults(func=run_delta_diff)

    # --------------------- chunks --------------------
    p_chunks = sub.add_parser("chunks", help="Inspect chunk IDs for a file.")
    p_chunks.add_argument("file")
    p_chunks.add_argument("--target", required=True)
    p_chunks.add_argument("--json", action="store_true")
    p_chunks.set_defaults(func=run_delta_chunks)

    # --------------------- gc ------------------------
    p_gc = sub.add_parser("gc", help="List or delete unused chunks.")
    p_gc.add_argument("--target", required=True)
    p_gc.add_argument("--apply", action="store_true")
    p_gc.add_argument("--json", action="store_true")
    p_gc.set_defaults(func=run_delta_gc)

    # default help
    parser.set_defaults(func=lambda a: parser.print_help())
