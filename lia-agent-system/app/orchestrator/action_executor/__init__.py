"""
ActionExecutor package — backward-compatible re-export.
Todos os símbolos que o codebase importa de action_executor continuam disponíveis aqui.
"""
from app.orchestrator.action_executor.action_types import ActionResult
from app.orchestrator.action_executor.executor import ActionExecutorService, action_executor
from app.orchestrator.action_executor.intents_config import (
    ACTIONABLE_INTENTS,
    CONFIRMATION_PATTERNS,
    MESSAGE_INTENT_PATTERNS,
    REJECTION_PATTERNS,
    STAGE_ALIASES,
    VALID_PIPELINE_STAGES,
)
from app.orchestrator.action_executor.utils import (
    _detect_intent_from_message,
    _extract_entities_from_message,
    _resolve_ptbr_datetime,
    is_confirmation,
    is_rejection,
    resolve_candidate_from_context,
    resolve_stage,
)

__all__ = [
    "ActionResult",
    "ACTIONABLE_INTENTS",
    "CONFIRMATION_PATTERNS",
    "REJECTION_PATTERNS",
    "VALID_PIPELINE_STAGES",
    "STAGE_ALIASES",
    "MESSAGE_INTENT_PATTERNS",
    "is_confirmation",
    "is_rejection",
    "resolve_candidate_from_context",
    "resolve_stage",
    "_detect_intent_from_message",
    "_extract_entities_from_message",
    "_resolve_ptbr_datetime",
    "ActionExecutorService",
    "action_executor",
]
