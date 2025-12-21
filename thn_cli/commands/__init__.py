"""
THN CLI – Command Group Registry (Hybrid-Standard)
=================================================

RESPONSIBILITIES
----------------
Defines the **canonical registry** of all first-party CLI command modules.

This package is responsible for:
    • Declaring which command modules are eligible for CLI exposure
    • Providing a deterministic, explicit command discovery surface
    • Ensuring all command modules are importable at startup
    • Acting as the authoritative source of truth for command availability

DISCOVERY CONTRACT
------------------
The THN CLI discovers commands by iterating over `thn_cli.commands.__all__`.

Each listed module:
    • MUST be importable without fatal side effects
    • MUST expose add_subparser(subparsers)
    • MUST register its own command(s) when invoked
    • MUST NOT perform business logic at import time

LOAD ORDER
----------
The order of `__all__` is **intentional and stable**.

While argparse does not require ordering, this list:
    • Defines deterministic discovery for loaders
    • Supports reproducible help output
    • Enables tooling, diagnostics, and documentation generation

RELATIONSHIP TO LOADERS
-----------------------
    • `__all__` defines *what* may be loaded
    • Command loaders define *how* loading occurs
    • Loaders MUST NOT bypass or contradict this list

CONTRACT STATUS
---------------
⚠️ CORE CLI REGISTRY — SEMANTICS LOCKED

Changes here affect:
    • CLI command availability
    • Golden tests
    • Help output
    • Automation and plugin tooling

Modify with care.
"""

# Canonical command module registry
__all__ = [
    "commands_accept",
    "commands_blueprints",
    "commands_dev",
    "commands_diag",
    "commands_drift",
    "commands_hub",
    "commands_init",
    "commands_inspect",
    "commands_keys",
    "commands_list",
    "commands_make",
    "commands_make_project",
    "commands_migrate",
    "commands_plugins",
    "commands_registry_tools",
    "commands_routing",
    "commands_snapshots",
    "commands_sync",
    "commands_sync_cli",
    "commands_sync_delta",
    "commands_sync_docs",
    "commands_sync_remote",
    "commands_sync_status",
    "commands_sync_web",
    "commands_tasks",
    "commands_ui",
    "commands_version",
]

# Explicit imports ensure:
#   • early failure for broken modules
#   • predictable import order
#   • compatibility with static loaders
from . import (  # noqa: F401
    commands_accept,
    commands_blueprints,
    commands_dev,
    commands_diag,
    commands_drift,
    commands_hub,
    commands_init,
    commands_inspect,
    commands_keys,
    commands_list,
    commands_make,
    commands_make_project,
    commands_migrate,
    commands_plugins,
    commands_registry_tools,
    commands_routing,
    commands_snapshots,
    commands_sync,
    commands_sync_cli,
    commands_sync_delta,
    commands_sync_docs,
    commands_sync_remote,
    commands_sync_status,
    commands_sync_web,
    commands_tasks,
    commands_ui,
    commands_version,
)
