"""Backwards-compatibility shim — canonical implementation in app/services/toon_service."""
from app.services.toon_service import *  # noqa: F401, F403
from app.services.toon_service import (  # noqa: F401
    _toon_cache_key,
    _build_headline,
    _build_location,
    _build_highlights,
    _compute_skills_match,
    _compute_match_score,
    _get_redis,
)
