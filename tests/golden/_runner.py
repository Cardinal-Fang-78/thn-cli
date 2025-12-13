from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from thn_cli.__main__ import main

SNAPSHOTS = Path(__file__).parent / "snapshots"
UPDATE = os.getenv("THN_UPDATE_GOLDEN") == "1"


@dataclass
class RunResult:
    code: int
    out: str
    err: str


def _write_snapshot(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_or_update(path: Path, content: str) -> str:
    if UPDATE:
        _write_snapshot(path, content)
        return content

    return path.read_text(encoding="utf-8")


def run_cli(
    argv: List[str],
    capsys,
    *,
    debug: bool = False,
) -> RunResult:
    env = os.environ.copy()

    if debug:
        env["THN_CLI_DEBUG"] = "1"
    else:
        env.pop("THN_CLI_DEBUG", None)

    try:
        code = main(argv)
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1

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
