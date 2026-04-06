
"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.learning_confirmation_service import *  # noqa: F401, F403
from app.shared.services.learning_confirmation_service import _calculate_confidence  # noqa: F401

