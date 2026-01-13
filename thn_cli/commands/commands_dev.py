# thn_cli/commands/commands_dev.py

"""
THN Developer Utilities
-----------------------

Implements:

    thn dev setup
    thn dev test
    thn dev goldens
    thn dev diag
    thn dev cleanup temp
    thn dev init
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from thn_cli.contracts.dev.diag import diagnose_dev
from thn_cli.contracts.dev.goldens import inspect_golden_env, run_golden_tests
from thn_cli.contracts.errors import SYSTEM_CONTRACT
from thn_cli.contracts.exceptions import CommandError
from thn_cli.syncv2.utils.fs_ops import (
    _write_dev_cleanup_echo,
    cleanup_temp_root,
    init_dev_folders,
    resolve_temp_root,
)

# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------


def _ensure_package(pkg: str) -> None:
    try:
        __import__(pkg)
        print(f"{pkg} already installed.")
    except ImportError:
        try:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        except subprocess.CalledProcessError as exc:
            raise CommandError(
                contract=SYSTEM_CONTRACT,
                message=f"Failed to install development dependency: {pkg}",
            ) from exc


# ---------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------


def run_dev_setup(args: argparse.Namespace) -> int:
    print("\nSetting up THN development environment...\n")
    for pkg in ("pytest", "pytest-cov"):
        _ensure_package(pkg)
    print("\nDevelopment environment ready.\n")
    return 0


def run_dev_test(args: argparse.Namespace) -> int:
    print("\nRunning THN test suite...\n")
    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=thn_cli",
                "--cov-report=term-missing",
            ]
        )
    except subprocess.CalledProcessError as exc:
        raise CommandError(
            contract=SYSTEM_CONTRACT,
            message="Test suite execution failed.",
        ) from exc
    return 0


def run_dev_goldens(args: argparse.Namespace) -> int:
    print(inspect_golden_env())
    if args.run:
        return run_golden_tests()
    return 0


def run_dev_diag(args: argparse.Namespace) -> int:
    result = diagnose_dev()
    print(json.dumps(result, indent=4))
    return 0


def run_dev_cleanup_temp(args: argparse.Namespace) -> int:
    """
    thn dev cleanup temp

    Cleans the resolved THN temp root.

    Behavior:
        • Safe and idempotent
        • Honors THN_TEMP_ROOT override
        • Emits a diagnostic-only cleanup echo
    """
    deleted = cleanup_temp_root()

    _write_dev_cleanup_echo(
        deleted_paths=deleted,
        resolved_temp_root=resolve_temp_root(),
    )

    result = {
        "success": True,
        "message": "Temp root cleaned",
        "deleted_paths": deleted,
    }

    print(json.dumps(result, indent=4))
    return 0


def run_dev_init(args: argparse.Namespace) -> int:
    """
    thn dev init

    Ensures expected THN local development folders exist.

    Behavior:
        • Non-destructive
        • Safe to re-run
        • Diagnostic convenience only
    """
    created = init_dev_folders()

    result = {
        "success": True,
        "created_paths": created,
    }

    print(json.dumps(result, indent=4))
    return 0


# ---------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "dev",
        help="Developer utilities for THN.",
        description="Developer utilities for THN.",
    )

    sub = parser.add_subparsers(dest="dev_cmd")

    p_setup = sub.add_parser("setup", help="Install development toolchain.")
    p_setup.set_defaults(func=run_dev_setup)

    p_test = sub.add_parser("test", help="Run pytest with coverage.")
    p_test.set_defaults(func=run_dev_test)

    p_goldens = sub.add_parser(
        "goldens",
        help="Inspect golden-test mode and optionally run golden tests.",
    )
    p_goldens.add_argument(
        "--run",
        action="store_true",
        help="Run pytest tests/golden with current environment.",
    )
    p_goldens.set_defaults(func=run_dev_goldens)

    p_diag = sub.add_parser(
        "diag",
        help="Inspect resolved developer environment and flags.",
    )
    p_diag.set_defaults(func=run_dev_diag)

    # -------------------------------------------------------------
    # Cleanup commands
    # -------------------------------------------------------------

    p_cleanup = sub.add_parser(
        "cleanup",
        help="Cleanup developer artifacts.",
    )

    cleanup_sub = p_cleanup.add_subparsers(
        dest="cleanup_target",
        required=True,
    )

    p_cleanup_temp = cleanup_sub.add_parser(
        "temp",
        help="Clean the THN temp root (safe, idempotent).",
    )
    p_cleanup_temp.set_defaults(func=run_dev_cleanup_temp)

    # -------------------------------------------------------------
    # Init command
    # -------------------------------------------------------------

    p_init = sub.add_parser(
        "init",
        help="Create expected local THN folders (safe, non-destructive).",
    )
    p_init.set_defaults(func=run_dev_init)

    parser.set_defaults(func=lambda args: parser.print_help())
