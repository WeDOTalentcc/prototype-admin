"""Backwards-compatibility shim — real implementation in app/domains/analytics/services."""
from app.domains.analytics.services.recruiter_behavior_service import *  # noqa: F401,F403
from app.domains.analytics.services.recruiter_behavior_service import (  # noqa: F401
    _behavior_key,
)
