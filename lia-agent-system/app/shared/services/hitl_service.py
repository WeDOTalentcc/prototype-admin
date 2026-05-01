"""Backwards-compatibility shim — canonical implementation in app.domains.cv_screening.services.hitl_service."""
from app.domains.cv_screening.services.hitl_service import *  # noqa: F401,F403
from app.domains.cv_screening.services.hitl_service import (  # noqa: F401
    _HITL_TTL_SECONDS,
    _get_redis,
    _db_save_pending,
    _db_resolve,
)
