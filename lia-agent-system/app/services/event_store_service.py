"""Shim: re-exports from app.shared.services.event_store_service (canonical location).

Tests patch via app.services.event_store_service — this shim ensures importability.
"""
from app.shared.services.event_store_service import *  # noqa: F401, F403
try:
    from app.shared.services.event_store_service import *  # noqa: F401, F403
except ImportError:
    pass
