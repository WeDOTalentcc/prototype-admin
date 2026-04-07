"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.hitl_service import *  # noqa: F401, F403
from app.shared.services.hitl_service import (  # noqa: F401
    _HITL_TTL_SECONDS,
    _get_redis,
)
