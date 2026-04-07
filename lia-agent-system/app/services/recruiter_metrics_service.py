"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.recruiter_metrics_service import *  # noqa: F401, F403
from app.shared.services.recruiter_metrics_service import (  # noqa: F401
    _urgency_threshold,
    _urgency_weight,
)
