"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.recruiter_behavior_service import *  # noqa: F401, F403
# Explicitly re-export private helper so tests can import it directly
from app.domains.analytics.services.recruiter_behavior_service import _behavior_key  # noqa: F401
