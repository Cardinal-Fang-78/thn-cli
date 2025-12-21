"""
THN Post-Make subsystem.

This layer runs only AFTER a successful `make` has completed and AFTER registry
updates have been committed.

Rules:
- No path inference. All paths must come from get_thn_paths() via the context.
- Hooks must be safe to run multiple times (idempotent where possible).
"""

from .runner import run_post_make

__all__ = ["run_post_make"]
