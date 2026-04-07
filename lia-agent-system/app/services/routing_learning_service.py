"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.routing_learning_service import *  # noqa: F401, F403
from app.domains.analytics.services.routing_learning_service import _MIN_SAMPLES  # noqa: F401
