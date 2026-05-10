"""Backwards-compatibility shim — real implementation in app/domains/analytics/services."""
from app.domains.analytics.services.routing_learning_service import *  # noqa: F401,F403
from app.domains.analytics.services.routing_learning_service import _MIN_SAMPLES  # noqa: F401 — re-export private for patching
