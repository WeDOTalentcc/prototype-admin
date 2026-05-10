"""Shim: bias_audit_service — re-exports from app.shared.services.bias_audit_service (canonical).

Tests patch app.services.bias_audit_service._SCIPY_AVAILABLE and .logger — this shim
exposes them so patch.object() can find the attributes.
"""
import logging
from app.shared.services.bias_audit_service import (  # noqa: F401
    BiasAuditService,
    _SCIPY_AVAILABLE,
    _chi_square_test,
    _audit_dimension,
)
# Re-export logger under this module's name (tests patch it here)
logger = logging.getLogger("app.services.bias_audit_service")

# Re-export everything else
from app.shared.services.bias_audit_service import *  # noqa: F401, F403
try:
    from app.shared.services.bias_audit_service import BiasAuditReport, DemographicAuditResult  # noqa: F401
except ImportError:
    pass
