"""Backwards-compatibility shim - real implementation in app/domains/analytics/services."""
from app.domains.analytics.services.sector_benchmark_service import *  # noqa: F401,F403
from app.domains.analytics.services.sector_benchmark_service import (  # noqa: F401
    _normalize_area,
    _normalize_seniority,
)
