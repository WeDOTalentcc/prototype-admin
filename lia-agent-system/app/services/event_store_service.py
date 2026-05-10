"""Shim: re-exports from app.shared.services.event_store_service (canonical location).

Tests patch via app.services.event_store_service — this shim ensures importability.
"""
from app.shared.services.event_store_service import *  # noqa: F401, F403
# Re-export private names needed for test patching
try:
    from app.shared.services.event_store_service import (  # noqa: F401
        EventStoreService,
        event_store_service,
    )
    from sqlalchemy import select  # noqa: F401 — exposed for test mocking
except ImportError:
    pass

# Always expose _DomainEvent so test patches via patch.object work.
# In test environments lia_models is unavailable so this is a None sentinel —
# the real append() logic handles the fallback import internally.
try:
    from app.domains.analytics.services.event_store_service import _DomainEvent  # noqa: F401
except Exception:
    _DomainEvent = None  # noqa: F841
