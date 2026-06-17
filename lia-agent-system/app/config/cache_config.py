"""
Cache config shim (Fase 7 consolidation, LIA-D05).

All cache configuration is now in app.shared.cache_strategy.
This module exists for backwards compat only.
"""
# noqa: F401
from app.shared.cache_strategy import CacheSettings, cache_settings

__all__ = ["CacheSettings", "cache_settings"]
