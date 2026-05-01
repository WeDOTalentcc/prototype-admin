"""
WebSocket Message Schemas — Pydantic schemas para mensagens do protocolo WS.

Define o contrato de mensagens entre cliente e servidor:

Cliente → Servidor:
  WSUserMessage     : mensagem de chat do usuário
  WSPingMessage     : keepalive ping
  WSAbortMessage    : abortar processamento

Servidor → Cliente:
  WSConnectedMessage    : confirmação de conexão
  WSThinkingMessage     : agente iniciou processamento
  WSTokenMessage        : chunk de streaming (LangGraph .astream())
  WSResponseMessage     : resposta final completa
  WSErrorMessage        : erro
  WSPongMessage         : resposta ao ping
"""
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Cliente → Servidor
# ---------------------------------------------------------------------------

class WSUserMessage(BaseModel):
    """Mensagem de chat enviada pelo cliente ao servidor."""

    type: Literal["message"] = "message"
    content: str = Field(..., description="Texto da mensagem do usuário")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto do domínio (current_stage, collected_data, etc.)",
    )
    domain: str = Field(
        default="recruiter_assistant",
        description="Domínio alvo da mensagem (wizard, sourcing, etc.)",
    )


class WSPingMessage(BaseModel):
    type: Literal["ping"] = "ping"


class WSAbortMessage(BaseModel):
    type: Literal["abort"] = "abort"


# ---------------------------------------------------------------------------
# Servidor → Cliente
# ---------------------------------------------------------------------------

class WSConnectedMessage(BaseModel):
    type: Literal["connected"] = "connected"
    session_id: str
    domain: str
    timestamp: str = ""


class WSThinkingMessage(BaseModel):
    """Indica que o agente está processando. Pode incluir job_id para tarefas async."""

    type: Literal["thinking"] = "thinking"
    job_id: str | None = Field(
        default=None,
        description="ID do job assíncrono (Celery task ou correlation_id RabbitMQ)",
    )
    timestamp: str = ""


class WSTokenMessage(BaseModel):
    """Chunk de streaming — enviado durante geração de token a token."""

    type: Literal["token"] = "token"
    content: str = Field(..., description="Chunk de texto gerado pelo LLM")
    timestamp: str = ""


class WSResponseMessage(BaseModel):
    """Resposta final completa do agente."""

    type: Literal["message"] = "message"
    content: str = Field(..., description="Texto completo da resposta")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    navigation: dict[str, Any] | None = Field(default=None)
    state_updates: dict[str, Any] = Field(default_factory=dict)
    domain: str = ""
    source: str = Field(
        default="direct",
        description="'direct' = síncrono, 'celery_worker' = async via fila",
    )
    timestamp: str = ""


class WSErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    message: str
    code: str | None = None
    timestamp: str = ""


class WSPongMessage(BaseModel):
    type: Literal["pong"] = "pong"
    timestamp: str = ""
