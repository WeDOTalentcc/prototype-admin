"""
Error Handling - Standardized error management for all agents.

This module provides:
- Standardized error codes and responses
- User-friendly error messages in Portuguese

W1-002 cleanup (2026-05-22): removido o decorator `handle_agent_errors`
(linhas 163-246 do legado) — tinha ZERO callers reais e era único
consumer de `AgentResponse` legacy. Pre-audit:
sprint_logs/sprint_1.2/W1-002_AUDIT.md.
"""
import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


logger = logging.getLogger(__name__)


class AgentErrorCode(StrEnum):
    """Standard error codes for agent operations."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_ENTITY = "MISSING_REQUIRED_ENTITY"
    INVALID_INPUT = "INVALID_INPUT"
    NOT_FOUND = "NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMITED = "RATE_LIMITED"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    LLM_ERROR = "LLM_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    CONTEXT_MISSING = "CONTEXT_MISSING"
    CANCELLED = "CANCELLED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"


@dataclass
class AgentErrorResponse:
    """Standardized error response structure."""
    code: AgentErrorCode
    user_message: str
    technical_message: str = ""
    retryable: bool = False
    suggested_action: str | None = None
    missing_entities: list = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "error": True,
            "code": self.code.value,
            "message": self.user_message,
            "technical_message": self.technical_message,
            "retryable": self.retryable,
            "suggested_action": self.suggested_action,
            "missing_entities": self.missing_entities,
            "context": self.context
        }


class AgentError(Exception):
    """Base exception for agent errors."""

    def __init__(
        self,
        code: AgentErrorCode,
        user_message: str,
        technical_message: str = "",
        retryable: bool = False,
        suggested_action: str | None = None,
        missing_entities: list = None,
        context: dict[str, Any] = None
    ):
        self.code = code
        self.user_message = user_message
        self.technical_message = technical_message or user_message
        self.retryable = retryable
        self.suggested_action = suggested_action
        self.missing_entities = missing_entities or []
        self.context = context or {}
        super().__init__(user_message)

    def to_response(self) -> AgentErrorResponse:
        """Convert exception to AgentErrorResponse."""
        return AgentErrorResponse(
            code=self.code,
            user_message=self.user_message,
            technical_message=self.technical_message,
            retryable=self.retryable,
            suggested_action=self.suggested_action,
            missing_entities=self.missing_entities,
            context=self.context
        )


USER_FRIENDLY_MESSAGES = {
    AgentErrorCode.VALIDATION_ERROR: "Alguns dados parecem incorretos. Por favor, verifique as informações.",
    AgentErrorCode.MISSING_REQUIRED_ENTITY: "Preciso de mais informações para continuar.",
    AgentErrorCode.INVALID_INPUT: "O formato da informação não está correto.",
    AgentErrorCode.NOT_FOUND: "Não encontrei o que você está procurando.",
    AgentErrorCode.PERMISSION_DENIED: "Você não tem permissão para realizar esta ação.",
    AgentErrorCode.RATE_LIMITED: "Muitas requisições. Por favor, aguarde um momento.",
    AgentErrorCode.EXTERNAL_SERVICE_ERROR: "Houve um problema com um serviço externo. Tente novamente em alguns segundos.",
    AgentErrorCode.LLM_ERROR: "Houve um problema ao processar sua solicitação. Tente novamente.",
    AgentErrorCode.DATABASE_ERROR: "Houve um problema ao acessar os dados. Tente novamente.",
    AgentErrorCode.TIMEOUT: "A operação demorou muito. Tente novamente.",
    AgentErrorCode.INTERNAL_ERROR: "Ocorreu um erro inesperado. Nossa equipe foi notificada.",
    AgentErrorCode.UNSUPPORTED_OPERATION: "Esta operação não é suportada no momento.",
    AgentErrorCode.CONTEXT_MISSING: "Preciso de mais contexto. Qual vaga ou candidato você está trabalhando?",
    AgentErrorCode.CANCELLED: "Operação cancelada conforme solicitado.",
    AgentErrorCode.PARTIAL_SUCCESS: "Algumas operações foram concluídas, mas houve problemas em outras.",
}

SUGGESTED_ACTIONS = {
    AgentErrorCode.MISSING_REQUIRED_ENTITY: "Por favor, forneça as informações que faltam.",
    AgentErrorCode.NOT_FOUND: "Verifique se o ID está correto ou tente uma busca diferente.",
    AgentErrorCode.RATE_LIMITED: "Aguarde 30 segundos e tente novamente.",
    AgentErrorCode.EXTERNAL_SERVICE_ERROR: "Aguarde alguns segundos e tente novamente.",
    AgentErrorCode.TIMEOUT: "Tente com menos dados ou divida a operação.",
    AgentErrorCode.CONTEXT_MISSING: "Selecione uma vaga ou candidato primeiro.",
}


def create_user_friendly_error(
    code: AgentErrorCode,
    technical_message: str = "",
    missing_entities: list = None,
    context: dict[str, Any] = None
) -> AgentErrorResponse:
    """Create a user-friendly error response."""
    user_message = USER_FRIENDLY_MESSAGES.get(code, "Ocorreu um erro. Por favor, tente novamente.")
    suggested_action = SUGGESTED_ACTIONS.get(code)

    if missing_entities:
        entity_names = ", ".join(missing_entities)
        user_message = f"Preciso que você informe: {entity_names}"

    retryable = code in [
        AgentErrorCode.RATE_LIMITED,
        AgentErrorCode.EXTERNAL_SERVICE_ERROR,
        AgentErrorCode.LLM_ERROR,
        AgentErrorCode.DATABASE_ERROR,
        AgentErrorCode.TIMEOUT
    ]

    return AgentErrorResponse(
        code=code,
        user_message=user_message,
        technical_message=technical_message,
        retryable=retryable,
        suggested_action=suggested_action,
        missing_entities=missing_entities or [],
        context=context or {}
    )


def raise_missing_entity(entity_name: str, description: str = "") -> None:
    """Raise an error for a missing required entity."""
    raise AgentError(
        code=AgentErrorCode.MISSING_REQUIRED_ENTITY,
        user_message=f"Por favor, informe: {description or entity_name}",
        technical_message=f"Missing required entity: {entity_name}",
        missing_entities=[entity_name],
        suggested_action=f"Forneça o valor para '{entity_name}'"
    )


def raise_not_found(resource_type: str, resource_id: str) -> None:
    """Raise a not found error."""
    raise AgentError(
        code=AgentErrorCode.NOT_FOUND,
        user_message=f"Não encontrei {resource_type} com ID '{resource_id}'.",
        technical_message=f"{resource_type} not found: {resource_id}",
        suggested_action="Verifique se o ID está correto."
    )


def raise_validation_error(message: str, field: str = "") -> None:
    """Raise a validation error."""
    raise AgentError(
        code=AgentErrorCode.VALIDATION_ERROR,
        user_message=message,
        technical_message=f"Validation error on {field}: {message}" if field else message
    )
