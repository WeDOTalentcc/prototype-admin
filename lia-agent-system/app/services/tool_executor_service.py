"""Shim: re-exports from app.shared.services.tool_executor_service (canonical location).

Tests patch via app.services.tool_executor_service — this shim ensures importability.
"""
from app.shared.services.tool_executor_service import *  # noqa: F401, F403
try:
    from app.shared.services.tool_executor_service import *  # noqa: F401, F403
except ImportError:
    pass
