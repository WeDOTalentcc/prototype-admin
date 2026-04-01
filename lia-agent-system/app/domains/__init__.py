from app.domains.base import (
    DomainPrompt,
    DomainContext,
    DomainResponse,
    DomainAction,
    IntentResult,
)
from app.domains.registry import DomainRegistry, register_domain
from app.domains.compliance_base import ComplianceDomainPrompt  # LIA-C01

# --- Domain auto-discovery ---
# Importing domain modules triggers @register_domain decorators
from app.domains.sourcing.domain import SourcingDomain  # noqa: F401
from app.domains.job_management.domain import JobManagementDomain  # noqa: F401
from app.domains.cv_screening.domain import CVScreeningDomain  # noqa: F401
from app.domains.communication.domain import CommunicationDomain  # noqa: F401
from app.domains.analytics.domain import AnalyticsDomain  # noqa: F401
from app.domains.interview_scheduling.domain import InterviewSchedulingDomain  # noqa: F401
from app.domains.ats_integration.domain import ATSIntegrationDomain  # noqa: F401
from app.domains.automation.domain import AutomationDomain  # noqa: F401
from app.domains.recruiter_assistant.domain import RecruiterAssistantDomain  # noqa: F401
from app.domains.hiring_policy.domain import HiringPolicyDomain  # noqa: F401
