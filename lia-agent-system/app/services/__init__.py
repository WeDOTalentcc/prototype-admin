# Services module
from app.domains.analytics.services.job_analytics_prompt_service import (
    COMMAND_TEMPLATES,
    AnalyticsResponse,
    JobAnalyticsPromptService,
    job_analytics_prompt_service,
)
from app.domains.analytics.services.job_insights_service import (
    JobInsightsService,
    job_insights_service,
)
from app.domains.communication.services.communication_dispatcher import (
    CommunicationDispatcher,
    communication_dispatcher,
)
from app.domains.communication.services.communication_service import (
    ApprovalStatus,
    CandidateOptOut,
    CandidateQuarantine,
    CommunicationLog,
    CommunicationService,
    CommunicationStatus,
    MessageChannel,
    MessageType,
    PendingApproval,
    communication_service,
)
from app.domains.cv_screening.services.eligibility_verification_service import (
    EligibilityQuestion,
    EligibilityVerificationService,
    ReconsiderationContext,
    ReconsiderationResult,
    eligibility_service,
)
from app.domains.cv_screening.services.personalized_feedback_service import (
    CandidateContext,
    FeedbackChannel,
    FeedbackTone,
    JobContext,
    PersonalizedFeedbackRecord,
    PersonalizedFeedbackRequest,
    PersonalizedFeedbackResult,
    PersonalizedFeedbackService,
    PersonalizedFeedbackStatus,
    WSIEvaluationContext,
    personalized_feedback_service,
)
from app.domains.job_management.services.jd_generator_service import (
    JobDescriptionGeneratorService,
    JobDescriptionInput,
    JobDescriptionOutput,
    JobDescriptionSection,
    jd_generator_service,
)
from app.domains.recruiter_assistant.services.conversation_memory import (
    ConversationMemory,
    conversation_memory,
)
from app.domains.sourcing.services.apify_service import ApifyService, apify_service
from app.shared.services.audit_service import AuditService, audit_service
from app.shared.services.benefits_service import (
    BENEFIT_CATEGORIES,
    BenefitsService,
    benefits_service,
)
from app.shared.services.compensation_analysis_service import (
    CompensationAnalysisService,
    compensation_analysis_service,
)
from app.shared.services.confidence_policy_service import (
    ConfidenceAction,
    ConfidencePolicyService,
    ConfidenceResult,
    ConfidenceThresholds,
    confidence_policy_service,
)
from app.shared.services.explainability_service import ExplainabilityService, explainability_service
from app.shared.services.intent_classifier import (
    ClassificationResult,
    IntentClassifierService,
    IntentType,
    intent_classifier_service,
)
from app.shared.services.learning_hub_service import (
    ConfirmationResult,
    LearningContext,
    LearningHubService,
    learning_hub_service,
)
from app.shared.services.market_benchmark_service import (
    MarketBenchmarkService,
    market_benchmark_service,
)
from app.shared.services.otp_service import (
    OTPService,
    otp_service,
)
from app.shared.services.response_cache_service import (
    CacheConfig,
    InMemoryCache,
    ResponseCacheService,
    cached_response,
    response_cache_service,
)
from app.shared.services.responsibilities_catalog_service import (
    RESPONSIBILITIES_CATALOG,
    ROLE_RESPONSIBILITIES_MAPPING,
    ResponsibilitiesCatalogService,
    responsibilities_catalog_service,
)
from app.shared.services.skills_catalog_service import (
    BEHAVIORAL_COMPETENCIES_CATALOG,
    ROLE_SKILLS_MAPPING,
    TECH_SKILLS_CATALOG,
    SkillsCatalogService,
    skills_catalog_service,
)

__all__ = [
    "CommunicationService",
    "communication_service",
    "MessageType",
    "MessageChannel",
    "ApprovalStatus",
    "CommunicationStatus",
    "PendingApproval",
    "CommunicationLog",
    "CandidateOptOut",
    "CandidateQuarantine",
    "PersonalizedFeedbackService",
    "personalized_feedback_service",
    "PersonalizedFeedbackRequest",
    "PersonalizedFeedbackResult",
    "PersonalizedFeedbackStatus",
    "PersonalizedFeedbackRecord",
    "CandidateContext",
    "JobContext",
    "WSIEvaluationContext",
    "FeedbackChannel",
    "FeedbackTone",
    "AuditService",
    "audit_service",
    "ExplainabilityService",
    "explainability_service",
    "BenefitsService",
    "benefits_service",
    "BENEFIT_CATEGORIES",
    "ApifyService",
    "apify_service",
    "CommunicationDispatcher",
    "communication_dispatcher",
    "IntentClassifierService",
    "intent_classifier_service",
    "IntentType",
    "ClassificationResult",
    "JobInsightsService",
    "job_insights_service",
    "MarketBenchmarkService",
    "market_benchmark_service",
    "JobDescriptionGeneratorService",
    "jd_generator_service",
    "JobDescriptionSection",
    "JobDescriptionInput",
    "JobDescriptionOutput",
    "JobAnalyticsPromptService",
    "job_analytics_prompt_service",
    "AnalyticsResponse",
    "COMMAND_TEMPLATES",
    "OTPService",
    "otp_service",
    "EligibilityVerificationService",
    "eligibility_service",
    "ReconsiderationResult",
    "EligibilityQuestion",
    "ReconsiderationContext",
    "ConfidencePolicyService",
    "confidence_policy_service",
    "ConfidenceAction",
    "ConfidenceThresholds",
    "ConfidenceResult",
    "SkillsCatalogService",
    "skills_catalog_service",
    "TECH_SKILLS_CATALOG",
    "BEHAVIORAL_COMPETENCIES_CATALOG",
    "ROLE_SKILLS_MAPPING",
    "ResponsibilitiesCatalogService",
    "responsibilities_catalog_service",
    "RESPONSIBILITIES_CATALOG",
    "ROLE_RESPONSIBILITIES_MAPPING",
    "CompensationAnalysisService",
    "compensation_analysis_service",
    "LearningHubService",
    "learning_hub_service",
    "ConversationMemory",
    "conversation_memory",
    "ResponseCacheService",
    "response_cache_service",
    "InMemoryCache",
    "CacheConfig",
    "cached_response",
]

# Shim: voice_screening_analysis accessible from app.services
try:
    from app.domains.voice.services import voice_screening_analysis  # noqa: F401
except ImportError:
    pass
