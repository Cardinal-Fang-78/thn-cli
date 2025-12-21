from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def op_mkdir(*, root: Path, rel: str) -> Dict[str, Any]:
    p = root / rel
    p.mkdir(parents=True, exist_ok=True)
    return {"op": "mkdir", "path": rel}


def op_touch(*, root: Path, rel: str) -> Dict[str, Any]:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("", encoding="utf-8")
    return {"op": "touch", "path": rel}


def op_write_json(*, root: Path, rel: str, data: Any) -> Dict[str, Any]:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"op": "write_json", "path": rel}


def op_delete(*, root: Path, rel: str) -> Dict[str, Any]:
    p = root / rel
    if not p.exists():
        return {"op": "delete", "path": rel, "note": "already missing"}
    if p.is_dir():
        # Only delete empty dirs (safe default)
        try:
            p.rmdir()
            return {"op": "delete", "path": rel, "note": "dir removed"}
        except OSError:
            return {"op": "delete", "path": rel, "note": "dir not empty; skipped"}
    p.unlink()
    return {"op": "delete", "path": rel, "note": "file removed"}
