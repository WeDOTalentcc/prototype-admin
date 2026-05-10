"""Shim: re-exports from app.shared.services.event_store_service (canonical location).

Tests patch via app.services.event_store_service — this shim ensures importability.
"""
from app.shared.services.event_store_service import *  # noqa: F401, F403
# Re-export private names needed for test patching
try:
    from app.shared.services.event_store_service import (  # noqa: F401
        _DomainEvent,
        EventStoreService,
    )
    from sqlalchemy import select  # noqa: F401 — exposed for test mocking
except ImportError:
    pass
