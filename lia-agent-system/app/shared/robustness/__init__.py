"""
Agent Robustness Module - Infrastructure for robust agent behavior.

This module provides:
- Intent schemas with entity requirements
- Standardized error handling
- Input validation with Pydantic
- Context management utilities
- Defensive prompt helpers

W1-002 cleanup (2026-05-22): removidos exports de:
- EnhancedBaseAgent, RobustAgentMixin (DEAD CODE — zero subclasses live)
- EnhancedAgentRegistry, enhanced_registry, RoutingDecision, RoutingTelemetry,
  FALLBACK_CHAINS (DEAD CODE — zero callers reais; ToolRoutingDecision em
  lia_agents_core é classe diferente, namespace diferente)
- handle_agent_errors decorator (DEAD CODE — zero @handle_agent_errors em
  código vivo; única ocorrência era docstring example)
"""

from app.shared.robustness.context_management import (
    CANCELLATION_KEYWORDS,
    CONFIRMATION_KEYWORDS,
    RESTART_KEYWORDS,
    CancellationHandler,
    ContextManager,
    ContextSnapshot,
    ContextStatus,
    HandoffContract,
)
from app.shared.robustness.defensive_prompts import (
    AMBIGUITY_DETECTION_PROMPT,
    CLARIFICATION_TRIGGERS,
    ERROR_RECOVERY_PROMPT,
    OUT_OF_SCOPE_RESPONSES,
    WHAT_I_CAN_DO,
    format_confirmation_message,
    get_clarification_message,
    get_defensive_prompt_section,
    get_out_of_scope_response,
)
from app.shared.robustness.error_handling import (
    AgentError,
    AgentErrorCode,
    AgentErrorResponse,
    create_user_friendly_error,
    raise_missing_entity,
    raise_not_found,
    raise_validation_error,
)
from app.shared.robustness.input_validation import (
    BaseAgentInput,
    CandidateInput,
    InterviewInput,
    JobInput,
    MessageInput,
    SearchInput,
    SupportedLanguage,
    WSIInput,
    detect_language,
    is_empty_or_whitespace,
    normalize_text,
    sanitize_sql_input,
    sanitize_text,
    validate_agent_input,
)
from app.shared.robustness.intent_schemas import (
    ALL_INTENT_SCHEMAS,
    EntityImportance,
    EntityRequirement,
    EntityType,
    IntentSchema,
    get_agent_intents,
    get_intent_schema,
)
from app.shared.robustness.response_filter import (
    FORBIDDEN_PATTERNS,
    INFORMAL_TERMS,
    PROFESSIONAL_INDICATORS,
    ToneFilter,
    filter_response,
    tone_filter,
    validate_response,
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
    "ToneFilter",
    "filter_response",
    "validate_response",
    "tone_filter",
    "INFORMAL_TERMS",
    "FORBIDDEN_PATTERNS",
    "PROFESSIONAL_INDICATORS",
]
