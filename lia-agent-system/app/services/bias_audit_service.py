"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.bias_audit_service import *  # noqa: F401, F403
from app.shared.services.bias_audit_service import (  # noqa: F401
    APPROVAL_THRESHOLD,
    FOUR_FIFTHS_THRESHOLD,
    _age_group,
    _adverse_impact_ratio,
)
