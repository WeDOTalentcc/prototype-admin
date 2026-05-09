"""Shim: re-exports from canonical app.domains.cv_screening.services.hitl_service.

The full implementation lives in the cv_screening domain. This shim exists so that
callers that do `from app.services.hitl_service import HITLService` keep working.
"""
from app.domains.cv_screening.services.hitl_service import *  # noqa: F401, F403
try:
    from app.domains.cv_screening.services.hitl_service import (
        _HITL_TTL_SECONDS,
        _get_redis,
        _db_save_pending,
        _db_resolve,
        _db_get_pending,
        HITLService,
        hitl_service,
    )
except ImportError:
    pass
