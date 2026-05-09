"""Shim: re-exports from app.shared.services.embedding_cache_service (canonical location).

Tests patch via app.services.embedding_cache_service — this shim ensures importability.
"""
from app.shared.services.embedding_cache_service import *  # noqa: F401, F403
try:
    from app.shared.services.embedding_cache_service import *  # noqa: F401, F403
except ImportError:
    pass
