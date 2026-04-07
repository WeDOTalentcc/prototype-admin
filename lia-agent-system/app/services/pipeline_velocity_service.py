"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.pipeline_velocity_service import *  # noqa: F401, F403
from app.shared.services.pipeline_velocity_service import (  # noqa: F401
    _threshold_for_stage,
)
