"""Shim: re-exports from app.shared.services.checkpoint_service (canonical location).

Tests patch via app.services.checkpoint_service — this shim ensures importability.
"""
from app.shared.services.checkpoint_service import *  # noqa: F401, F403
try:
    from app.shared.services.checkpoint_service import *  # noqa: F401, F403
except ImportError:
    pass
