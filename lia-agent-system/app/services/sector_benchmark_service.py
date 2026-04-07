"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.sector_benchmark_service import *  # noqa: F401, F403
from app.shared.services.sector_benchmark_service import (  # noqa: F401
    _normalize_area,
    _normalize_seniority,
)
from app.domains.analytics.services.sector_benchmark_service import (  # noqa: F401
    _BENCHMARKS,
    _AREA_ALIASES,
    _SENIORITY_ALIASES,
)
