"""
THN Tasks Framework

Provides:
- A registry for scheduled tasks
- A placeholder scheduler for future automation
"""

from .scheduler import (
    list_tasks,
    add_task,
    remove_task,
    run_task,
)
