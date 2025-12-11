"""
THN CLI – Command Group Package
===============================

This package aggregates all command-group submodules used by the
THN CLI root dispatcher.

The CLI root (`thn_cli.main`) performs command discovery by calling
the `add_subparser()` function exposed by each command module listed
in `__all__`.

Command groups included here follow the Hybrid-Standard requirements:
    • Stable import surface
    • Deterministic ordering
    • Predictable dispatch registration
    • Clear separation of subsystems
"""

# Explicit export surface for command loaders
__all__ = [
    "commands_init",
    "commands_list",
    "commands_make",
    "commands_make_project",
    "commands_plugins",
    "commands_registry_tools",
    "commands_routing",
    "commands_sync",
    "commands_sync_cli",
    "commands_sync_docs",
    "commands_sync_web",
    "commands_sync_remote",
    "commands_sync_status",
    "commands_sync_delta",
    "commands_blueprints",
    "commands_blueprint_new",
    "commands_tasks",
    "commands_ui",
    "commands_hub",
    "commands_diag",
]

# NOTE:
# These imports are intentionally *lazy* to avoid unnecessary module
# initialization at runtime. The CLI root imports each module only
# when building the argparse tree.

from . import commands_init
from . import commands_list
from . import commands_make
from . import commands_make_project
from . import commands_plugins
from . import commands_registry_tools
from . import commands_routing
from . import commands_sync
from . import commands_sync_cli
from . import commands_sync_docs
from . import commands_sync_web
from . import commands_sync_remote
from . import commands_sync_status
from . import commands_sync_delta
from . import commands_blueprints
from . import commands_blueprint_new
from . import commands_tasks
from . import commands_ui
from . import commands_hub
from . import commands_diag
