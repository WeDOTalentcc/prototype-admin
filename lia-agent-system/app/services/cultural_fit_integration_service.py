"""Shim: re-exports from app.domains.cv_screening.services.cultural_fit_integration_service (canonical location).

Tests patch via app.services.cultural_fit_integration_service — this shim ensures importability.
"""
from app.domains.cv_screening.services.cultural_fit_integration_service import *  # noqa: F401, F403
try:
    from app.domains.cv_screening.services.cultural_fit_integration_service import *  # noqa: F401, F403
except ImportError:
    pass
