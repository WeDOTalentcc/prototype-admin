"""Backwards compatibility shim — import from async_agent_tasks instead."""
import warnings
warnings.warn(
    "Import from 'agents_legacy' is deprecated. Use 'async_agent_tasks' instead.",
    DeprecationWarning,
    stacklevel=2,
)
from app.jobs.tasks.async_agent_tasks import *  # noqa: F401, F403
