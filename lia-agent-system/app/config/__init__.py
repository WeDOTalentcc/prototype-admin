"""Configuration modules."""
# CacheSettings was consolidated into app.shared.cache_strategy (Fase 7, LIA-D05).
# Re-exported here for backwards compatibility with existing call sites.
from app.shared.cache_strategy import (
    CacheSettings,
    cache_settings,
)
from app.core.industry_weights import (
    INDUSTRY_WEIGHTS,
    UNIVERSAL_WEIGHTS,
    Industry,
    IndustryWeights,
    ScoringWeights,
    get_weights,
    get_weights_for_industry,
    list_available_industries,
)

__all__ = [
    "ScoringWeights",
    "IndustryWeights",
    "Industry",
    "UNIVERSAL_WEIGHTS",
    "INDUSTRY_WEIGHTS",
    "get_weights",
    "get_weights_for_industry",
    "list_available_industries",
    "CacheSettings",
    "cache_settings",
]
