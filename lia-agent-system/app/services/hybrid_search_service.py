"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.hybrid_search_service import *  # noqa: F401, F403
from app.shared.services.hybrid_search_service import (  # noqa: F401
    _normalize_scores,
    _merge_results,
)
