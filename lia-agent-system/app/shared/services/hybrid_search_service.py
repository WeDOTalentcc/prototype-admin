"""Backwards-compatibility shim — real implementation in app/domains/ai/services."""
from app.domains.ai.services.hybrid_search_service import *  # noqa: F401,F403
from app.domains.ai.services.hybrid_search_service import (  # noqa: F401
    _normalize_scores,
    _merge_results,
)
