"""Shim: re-exports from app.domains.analytics.services.ml_feedback_service (canonical location).

Tests patch via app.services.ml_feedback_service — this shim ensures importability.
"""
from app.domains.analytics.services.ml_feedback_service import *  # noqa: F401, F403
try:
    from app.domains.analytics.services.ml_feedback_service import *  # noqa: F401, F403
except ImportError:
    pass
