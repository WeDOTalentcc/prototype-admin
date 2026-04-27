"""
WebSocket Message Schemas — Pydantic schemas para mensagens do protocolo WS.

Define o contrato de mensagens entre cliente e servidor:

Cliente → Servidor:
  WSHelloMessage    : handshake inicial (negocia protocol_version)
  WSUserMessage     : mensagem de chat do usuário
  WSPingMessage     : keepalive ping
  WSAbortMessage    : abortar processamento

Servidor → Cliente:
  WSConnectedMessage    : confirmação de conexão (anuncia protocol_version)
  WSThinkingMessage     : agente iniciou processamento
  WSTokenMessage        : chunk de streaming (LangGraph .astream_events("v2"))
  WSResponseMessage     : resposta final completa
  WSErrorMessage        : erro
  WSPongMessage         : resposta ao ping

Versionamento (PM-03, Auditoria Rev 4):
  `LIA_WS_PROTOCOL_VERSION` é o contrato canônico (semver MAJOR.MINOR).
  Mudanças MAJOR são incompatíveis (ex.: rename de campo obrigatório);
  MINOR são aditivas (ex.: novo campo opcional). O servidor envia a versão
  no `WSConnectedMessage`; o cliente pode mandar `WSHelloMessage` com a
  versão que entende — divergência MAJOR fecha o socket com 4400.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# PM-03 (Audit Rev 4) — versão canônica do contrato WS.
# Bump MAJOR quando houver breaking change; MINOR quando for aditivo.
# ─────────────────────────────────────────────────────────────────────────────
LIA_WS_PROTOCOL_VERSION: str = "1.0"


def is_protocol_compatible(client_version: str | None) -> bool:
    """Retorna True se `client_version` é compatível com o servidor.

    Regras (semver simples):
      * `None` ou string vazia → True (cliente legacy, assume MAJOR atual).
      * MAJOR igual ao do servidor → True.
      * MAJOR diferente → False (servidor deve fechar com 4400).
    """
    if not client_version:
        return True
    try:
        client_major = client_version.split(".", 1)[0]
        server_major = LIA_WS_PROTOCOL_VERSION.split(".", 1)[0]
    except Exception:
        return False
    return client_major == server_major

# ---------------------------------------------------------------------------
# Cliente → Servidor
# ---------------------------------------------------------------------------

class WSHelloMessage(BaseModel):
    """Handshake inicial cliente → servidor (PM-03).

    Permite ao cliente anunciar a versão do contrato WS que ele entende.
    Servidor responde com `WSConnectedMessage` carregando sua versão e
    fecha a conexão (close 4400) se houver mismatch de MAJOR.
    """

    type: Literal["hello"] = "hello"
    protocol_version: str = Field(
        default=LIA_WS_PROTOCOL_VERSION,
        description="Versão do contrato WS que o cliente entende (semver).",
    )
    client: str = Field(
        default="",
        description="Identificador do cliente (ex.: 'web@1.4.2').",
    )


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
    protocol_version: str = Field(
        default=LIA_WS_PROTOCOL_VERSION,
        description="Versão do contrato WS suportada pelo servidor (PM-03).",
    )


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
