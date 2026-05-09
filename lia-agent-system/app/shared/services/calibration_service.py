# R-054: re-export shim — canonical in app/domains/analytics/services/calibration_service.py
# R-055: not a duplicate — this is a backwards-compat re-export for callers that predate
#         the analytics domain restructure (app/api/v1/calibration.py, candidates/_shared.py).
#         Action: migrate callers to import directly from the canonical, then delete this shim.
"""Backwards-compatibility shim — real implementation in app/domains/analytics/services."""
from app.domains.analytics.services.calibration_service import *  # noqa: F401,F403
