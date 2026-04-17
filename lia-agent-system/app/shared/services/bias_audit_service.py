"""
DEPRECATED shim — bias_audit_service was moved to app.shared.compliance.

This module re-exports the canonical location for backward compatibility.
New imports should target app.shared.compliance.bias_audit_service directly.

See task #321 (W6) for context.
"""
from app.shared.compliance.bias_audit_service import *  # noqa: F401,F403
from app.shared.compliance.bias_audit_service import (  # noqa: F401
    AGE_GROUP_MID,
    AGE_GROUP_SENIOR,
    AGE_GROUP_YOUNG,
    APPROVAL_THRESHOLD,
    FOUR_FIFTHS_THRESHOLD,
    NOT_INFORMED,
    BiasAuditReport,
    BiasAuditService,
    DemographicAuditResult,
    _adverse_impact_ratio,
    _age_group,
    _audit_dimension,
    _chi2_survival,
    _chi_square_fallback,
    _chi_square_test,
    _gammaincc,
    _gammaincl_cf,
    _gammaincl_series,
    bias_audit_service,
)
