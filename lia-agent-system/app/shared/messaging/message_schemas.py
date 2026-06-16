"""
Message Schemas — Pydantic schemas para mensagens trafegadas via RabbitMQ.

AgentChatMessage  : mensagem do usuário → despachada para fila do agente.
AgentResponseMessage: resposta do agente → enviada de volta ao WS Gateway.
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentChatMessage(BaseModel):
    """Mensagem de chat despachada pelo WS Gateway para um agente via RabbitMQ."""

    model_config = ConfigDict(extra='forbid')

    session_id: str = Field(..., description="ID único da sessão WS")
    user_id: str = Field(..., description="ID do usuário")
    company_id: str = Field(..., description="ID da empresa (multi-tenant)")
    domain: str = Field(..., description="Domínio alvo (wizard, sourcing, etc.)")
    message: str = Field(..., description="Conteúdo da mensagem do usuário")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto do domínio (current_stage, collected_data, etc.)",
    )
    conversation_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Histórico recente da conversa (máx últimas 10 mensagens)",
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Prioridade da mensagem na fila (1=baixa, 10=alta)",
    )
    reply_to: str = Field(
        default="",
        description="Nome da fila de resposta para este session_id",
    )
    correlation_id: str = Field(
        default="",
        description="UUID para correlacionar request/response",
    )


class AgentResponseMessage(BaseModel):
    """Resposta do agente, publicada na fila de retorno e encaminhada ao WS Gateway."""

    model_config = ConfigDict(extra='forbid')

    session_id: str = Field(..., description="ID da sessão WS de destino")
    content: str = Field(default="", description="Texto da resposta do agente")
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confiança da resposta (0.0–1.0)",
    )
    actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ações sugeridas pelo agente",
    )
    navigation: dict[str, Any] | None = Field(
        default=None,
        description="Comando de navegação (stage transition, etc.)",
    )
    state_updates: dict[str, Any] = Field(
        default_factory=dict,
        description="Atualizações de estado para o frontend",
    )
    domain: str = Field(default="", description="Domínio que gerou a resposta")
    error: str | None = Field(default=None, description="Mensagem de erro, se houver")
    done: bool = Field(
        default=True,
        description="True = resposta final. False = chunk de streaming (futuro).",
    )
    correlation_id: str = Field(
        default="",
        description="UUID correlacionado com o request original",
    )
