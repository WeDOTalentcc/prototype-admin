"""Shim: canonical implementation moved to app.services.hitl_service.

Re-exports HITLService, models, and helper functions so existing imports
from this domain path continue to work unchanged.
"""
from app.services.hitl_service import *  # noqa: F401, F403
try:
    from app.services.hitl_service import (  # noqa: F401
        _HITL_TTL_SECONDS,
        _get_redis,
        _db_save_pending,
        _db_resolve,
        _db_get_pending,
        HITLService,
    )
except ImportError:
    pass
