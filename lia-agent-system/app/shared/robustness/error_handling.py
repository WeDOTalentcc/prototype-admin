"""
Error Handling - Standardized error management for all agents.

This module provides:
- Standardized error codes and responses
- Error wrapping decorator for agent methods
- User-friendly error messages in Portuguese
"""
import logging
import traceback
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from functools import wraps
from typing import Any, TypeVar


logger = logging.getLogger(__name__)

T = TypeVar('T')


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


def handle_agent_errors(
    agent_name: str = "Agent",
    default_error_code: AgentErrorCode = AgentErrorCode.INTERNAL_ERROR
):
    """
    Decorator to handle errors in agent methods.
    
    Wraps async methods with try/except and converts exceptions to AgentErrorResponse.
    
    Usage:
        @handle_agent_errors("JobIntakeAgent")
        async def process(self, intent, entities, context):
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AgentError as e:
                logger.warning(f"{agent_name}: AgentError - {e.code.value}: {e.technical_message}")
                from app.agents.base_agent import AgentResponse
                return AgentResponse(
                    success=False,
                    message=e.user_message,
                    data=e.to_response().to_dict()
                )
            except ValueError as e:
                logger.warning(f"{agent_name}: ValidationError - {str(e)}")
                error = create_user_friendly_error(
                    AgentErrorCode.VALIDATION_ERROR,
                    technical_message=str(e)
                )
                from app.agents.base_agent import AgentResponse
                return AgentResponse(
                    success=False,
                    message=error.user_message,
                    data=error.to_dict()
                )
            except KeyError as e:
                logger.warning(f"{agent_name}: MissingEntity - {str(e)}")
                error = create_user_friendly_error(
                    AgentErrorCode.MISSING_REQUIRED_ENTITY,
                    technical_message=f"Missing key: {str(e)}",
                    missing_entities=[str(e)]
                )
                from app.agents.base_agent import AgentResponse
                return AgentResponse(
                    success=False,
                    message=error.user_message,
                    data=error.to_dict(),
                    requires_user_input=True
                )
            except TimeoutError as e:
                logger.error(f"{agent_name}: Timeout - {str(e)}")
                error = create_user_friendly_error(
                    AgentErrorCode.TIMEOUT,
                    technical_message=str(e)
                )
                from app.agents.base_agent import AgentResponse
                return AgentResponse(
                    success=False,
                    message=error.user_message,
                    data=error.to_dict()
                )
            except Exception as e:
                logger.error(f"{agent_name}: UnexpectedError - {str(e)}\n{traceback.format_exc()}")
                error = create_user_friendly_error(
                    default_error_code,
                    technical_message=str(e)
                )
                from app.agents.base_agent import AgentResponse
                return AgentResponse(
                    success=False,
                    message=error.user_message,
                    data=error.to_dict()
                )
        return wrapper
    return decorator


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
