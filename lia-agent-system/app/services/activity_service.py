"""Shim: re-exports from app.domains.analytics.services.activity_service (canonical location).

Tests patch via app.services.activity_service — this shim ensures importability.
"""
from app.domains.analytics.services.activity_service import *  # noqa: F401, F403
try:
    from app.domains.analytics.services.activity_service import *  # noqa: F401, F403
except ImportError:
    pass
