"""
Observability models — canonical source is libs/models/lia_models/observability.py.

This module re-exports everything from the canonical library so that both import paths work:
  from lia_models.observability import ...                        # lib consumers
  from app.domains.analytics.models.observability import ...     # app consumers

Do NOT add model definitions here. Edit lia_models/observability.py instead.
"""
from lia_models.observability import *  # noqa: F401, F403
from lia_models.observability import (  # explicit re-export for type checkers
    AgentType, TaskStatus, DataCategory, ConsentStatus, IncidentSeverity,
    IncidentStatus, ComplianceStatus, ControlType, ControlFrequency,
    AIInferenceLog, DataAccessLog, ConsentRecord, ConsentEvent, ConsentVersion,
    ConsentOptOut, IncidentReport, ModelEvaluation, ComplianceControl,
    AuditTrail, PrivacyImpactAssessment, SystemHealthMetric,
)
