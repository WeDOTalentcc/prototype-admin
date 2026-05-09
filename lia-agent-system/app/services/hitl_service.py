"""Shim: re-exports from app.domains.cv_screening.services.hitl_service (canonical location).

Tests patch via app.services.hitl_service — this shim ensures importability.
"""
from app.domains.cv_screening.services.hitl_service import *  # noqa: F401, F403
try:
    from app.domains.cv_screening.services.hitl_service import *  # noqa: F401, F403
except ImportError:
    pass
