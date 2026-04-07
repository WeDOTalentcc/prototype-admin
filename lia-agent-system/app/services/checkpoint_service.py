"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.checkpoint_service import *  # noqa: F401, F403
from app.domains.cv_screening.services.checkpoint_service import _sanitize_state  # noqa: F401
