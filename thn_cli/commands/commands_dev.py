# thn_cli/commands/commands_dev.py

"""
THN Developer Utilities
-----------------------

Implements:

    thn dev setup
    thn dev test

'setup' installs pytest and related dev tools.
'test' runs pytest inside the THN CLI environment.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def _ensure_package(pkg: str):
    """Install a package if not available."""
    try:
        __import__(pkg)
        print(f"{pkg} already installed.")
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


def run_dev_setup(args: argparse.Namespace) -> int:
    print("\nSetting up THN development environment...\n")

    for pkg in ["pytest", "pytest-cov"]:
        _ensure_package(pkg)

    print("\nDevelopment environment ready.\n")
    return 0


def run_dev_test(args: argparse.Namespace) -> int:
    """Run pytest with coverage collection."""
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
        return exc.returncode

    return 0


def add_subparser(subparsers):
    parser = subparsers.add_parser(
        "dev",
        help="Developer utilities for THN.",
        description="Install dev tools or run the THN test suite.",
    )

    sub = parser.add_subparsers(dest="dev_cmd", required=True)

    p_setup = sub.add_parser("setup", help="Install development toolchain.")
    p_setup.set_defaults(func=run_dev_setup)

    p_test = sub.add_parser("test", help="Run pytest with coverage.")
    p_test.set_defaults(func=run_dev_test)

    parser.set_defaults(func=lambda args: parser.print_help())
