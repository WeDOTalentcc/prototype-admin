"""Backwards-compatibility shim — real implementation in app/domains/cv_screening/services."""
from app.domains.cv_screening.services.hitl_service import *  # noqa: F401,F403
from app.domains.cv_screening.services.hitl_service import (  # noqa: F401
    _HITL_TTL_SECONDS,
    _get_redis,
)
