"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.cache_manager_service import *  # noqa: F401, F403
from app.shared.resilience.cache_manager_service import get_cache_manager_service  # noqa: F401
