"""
Agent Robustness Module - Infrastructure for robust agent behavior.

This module provides:
- Intent schemas with entity requirements
- Standardized error handling
- Input validation with Pydantic
- Context management utilities
- Defensive prompt helpers
- Enhanced base agent and registry
"""

from app.shared.robustness.intent_schemas import (
    IntentSchema,
    EntityRequirement,
    EntityImportance,
    EntityType,
    get_agent_intents,
    get_intent_schema,
    ALL_INTENT_SCHEMAS
)

from app.shared.robustness.error_handling import (
    AgentError,
    AgentErrorCode,
    AgentErrorResponse,
    handle_agent_errors,
    create_user_friendly_error,
    raise_missing_entity,
    raise_not_found,
    raise_validation_error
)

from app.shared.robustness.input_validation import (
    BaseAgentInput,
    JobInput,
    CandidateInput,
    SearchInput,
    InterviewInput,
    WSIInput,
    MessageInput,
    validate_agent_input,
    sanitize_text,
    sanitize_sql_input,
    detect_language,
    SupportedLanguage,
    is_empty_or_whitespace,
    normalize_text
)

from app.shared.robustness.context_management import (
    ContextManager,
    ContextStatus,
    CancellationHandler,
    HandoffContract,
    ContextSnapshot,
    CANCELLATION_KEYWORDS,
    RESTART_KEYWORDS,
    CONFIRMATION_KEYWORDS
)

from app.shared.robustness.defensive_prompts import (
    CLARIFICATION_TRIGGERS,
    OUT_OF_SCOPE_RESPONSES,
    AMBIGUITY_DETECTION_PROMPT,
    ERROR_RECOVERY_PROMPT,
    WHAT_I_CAN_DO,
    get_defensive_prompt_section,
    get_clarification_message,
    get_out_of_scope_response,
    format_confirmation_message
)

from app.shared.robustness.enhanced_base import (
    EnhancedBaseAgent,
    RobustAgentMixin
)

from app.shared.robustness.enhanced_registry import (
    EnhancedAgentRegistry,
    RoutingDecision,
    RoutingTelemetry,
    FALLBACK_CHAINS,
    enhanced_registry
)

from app.shared.robustness.response_filter import (
    ToneFilter,
    filter_response,
    validate_response,
    tone_filter,
    INFORMAL_TERMS,
    FORBIDDEN_PATTERNS,
    PROFESSIONAL_INDICATORS,
)

__all__ = [
    "IntentSchema",
    "EntityRequirement",
    "EntityImportance",
    "EntityType",
    "get_agent_intents",
    "get_intent_schema",
    "ALL_INTENT_SCHEMAS",
    "AgentError",
    "AgentErrorCode",
    "AgentErrorResponse",
    "handle_agent_errors",
    "create_user_friendly_error",
    "raise_missing_entity",
    "raise_not_found",
    "raise_validation_error",
    "BaseAgentInput",
    "JobInput",
    "CandidateInput",
    "SearchInput",
    "InterviewInput",
    "WSIInput",
    "MessageInput",
    "validate_agent_input",
    "sanitize_text",
    "sanitize_sql_input",
    "detect_language",
    "SupportedLanguage",
    "is_empty_or_whitespace",
    "normalize_text",
    "ContextManager",
    "ContextStatus",
    "CancellationHandler",
    "HandoffContract",
    "ContextSnapshot",
    "CLARIFICATION_TRIGGERS",
    "OUT_OF_SCOPE_RESPONSES",
    "AMBIGUITY_DETECTION_PROMPT",
    "get_defensive_prompt_section",
    "get_clarification_message",
    "get_out_of_scope_response",
    "format_confirmation_message",
    "EnhancedBaseAgent",
    "RobustAgentMixin",
    "EnhancedAgentRegistry",
    "RoutingDecision",
    "RoutingTelemetry",
    "FALLBACK_CHAINS",
    "enhanced_registry",
    "ToneFilter",
    "filter_response",
    "validate_response",
    "tone_filter",
    "INFORMAL_TERMS",
    "FORBIDDEN_PATTERNS",
    "PROFESSIONAL_INDICATORS",
]
