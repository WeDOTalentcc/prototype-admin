"""Backwards-compatibility shim — real implementation in app/domains/analytics/services."""
from app.domains.analytics.services.learning_confirmation_service import *  # noqa: F401,F403
from app.domains.analytics.services.learning_confirmation_service import _calculate_confidence  # noqa: F401
