from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from thn_cli.__main__ import main

# ---------------------------------------------------------------------------
# Golden env guard (STRICT)
# ---------------------------------------------------------------------------

if os.getenv("THN_UPDATE_GOLDEN") and os.getenv("THN_UPDATE_GOLDENS"):
    raise RuntimeError(
        "Both THN_UPDATE_GOLDEN and THN_UPDATE_GOLDENS are set. "
        "Use only THN_UPDATE_GOLDEN (singular)."
    )

if os.getenv("THN_UPDATE_GOLDENS"):
    raise RuntimeError(
        "Invalid environment variable THN_UPDATE_GOLDENS detected. "
        "Did you mean THN_UPDATE_GOLDEN?"
    )

# ---------------------------------------------------------------------------

SNAPSHOTS = Path(__file__).parent / "snapshots"


def _update_enabled() -> bool:
    return os.getenv("THN_UPDATE_GOLDEN") == "1"


@dataclass
class RunResult:
    code: int
    out: str
    err: str


def _write_snapshot(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_or_update(path: Path, content: str) -> str:
    if _update_enabled():
        _write_snapshot(path, content)
        return content

    return path.read_text(encoding="utf-8")


def run_cli(
    argv: List[str],
    capsys,
    *,
    debug: bool = False,
) -> RunResult:
    # --- environment setup ---
    if debug:
        os.environ["THN_CLI_DEBUG"] = "1"
    else:
        os.environ.pop("THN_CLI_DEBUG", None)

    # --- argv simulation (REAL CLI BEHAVIOR) ---
    old_argv = sys.argv
    sys.argv = ["thn", *argv]

    try:
        code = main()
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 0
    finally:
        sys.argv = old_argv

    captured = capsys.readouterr()

    return RunResult(
        code=code,
        out=captured.out,
        err=captured.err,
    )


def assert_stdout(name: str, result: RunResult) -> None:
    path = SNAPSHOTS / f"{name}.stdout.txt"
    expected = _load_or_update(path, result.out)
    assert result.out == expected


def assert_stderr(name: str, result: RunResult) -> None:
    path = SNAPSHOTS / f"{name}.stderr.txt"
    expected = _load_or_update(path, result.err)
    assert result.err == expected
