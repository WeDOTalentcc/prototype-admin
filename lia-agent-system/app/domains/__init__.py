from app.domains.analytics.domain import AnalyticsDomain  # noqa: F401
from app.domains.ats_integration.domain import ATSIntegrationDomain  # noqa: F401
from app.domains.automation.domain import AutomationDomain  # noqa: F401
from app.domains.base import (
    DomainAction,
    DomainContext,
    DomainPrompt,
    DomainResponse,
    IntentResult,
)
from app.domains.communication.domain import CommunicationDomain  # noqa: F401
from app.domains.compliance_base import ComplianceDomainPrompt  # LIA-C01
from app.domains.cv_screening.domain import CVScreeningDomain  # noqa: F401
from app.domains.hiring_policy.domain import HiringPolicyDomain  # noqa: F401
from app.domains.interview_scheduling.domain import InterviewSchedulingDomain  # noqa: F401
from app.domains.job_management.domain import JobManagementDomain  # noqa: F401
from app.domains.recruiter_assistant.domain import RecruiterAssistantDomain  # noqa: F401
from app.domains.registry import DomainRegistry, register_domain

# --- Domain auto-discovery ---
# Importing domain modules triggers @register_domain decorators
from app.domains.pipeline.domain import PipelineTransitionDomain  # noqa: F401
from app.domains.sourcing.domain import SourcingDomain  # noqa: F401

# --- Phase 6 domains (Agent Studio, Talent Pool, Digital Twin, Campaign) ---
from app.domains.talent_pool.domain import TalentPoolDomain  # noqa: F401
from app.domains.agent_studio.domain import AgentStudioDomain  # noqa: F401
from app.domains.digital_twin.domain import DigitalTwinDomain  # noqa: F401
from app.domains.recruitment_campaign.domain import RecruitmentCampaignDomain  # noqa: F401
from app.domains.offer.domain import OfferDomain  # noqa: F401  # Sprint B Offer domain
try:
    from app.domains.job_creation.domain import JobCreationDomain  # noqa: F401  # Wizard WSI Phase B
except ImportError as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"JobCreationDomain not loaded (missing deps): {_e}")

try:
    from app.domains.company_settings.domain import CompanySettingsDomain  # noqa: F401
except ImportError as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"CompanySettingsDomain not loaded: {_e}")
try:
    from app.domains.candidate_self_service.domain import CandidateSelfServiceDomain  # noqa: F401
except ImportError as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"CandidateSelfServiceDomain not loaded: {_e}")
