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

from pydantic import BaseModel, Field, ConfigDict

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

    model_config = ConfigDict(extra='forbid')

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

    model_config = ConfigDict(extra='forbid')

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


class RailASuggestionMetadata(BaseModel):
    """PR-A — metadata estruturada emitida pelo Rail A (chat-workflow-reels.tsx).

    Validada strict no boundary WS (`ContextAdapter.from_ws`) para evitar
    prompt injection via context arbitrário e drift de schema entre FE/BE.

    Skill canônica: harness-engineering [sensor no boundary].
    """

    source: Literal["rail_a"] = Field(
        ..., description="Fonte da metadata. APENAS 'rail_a' é honrado."
    )
    card_id: str = Field(..., min_length=1, max_length=64, description="ID do card clicado.")
    stage: str = Field(..., min_length=1, max_length=64, description="ID do stage do card.")
    domain_hint: str | None = Field(
        default=None,
        max_length=64,
        description="Domínio sugerido pelo card. Validado contra DomainRegistry.",
    )
    intent_hint: str | None = Field(
        default=None,
        max_length=64,
        description="Action/intent sugerida dentro do domínio.",
    )

    model_config = {
        "extra": "ignore",  # campos extras são silenciosamente descartados
    }


# ─────────────────────────────────────────────────────────────────────────────
# PR-D — UIAction schemas (mirror canônico do FE `src/types/ui-action.ts`).
# Validados strict no boundary BE quando ChatResponse é construído.
# Skill: harness-engineering [sensor no boundary].
# ─────────────────────────────────────────────────────────────────────────────


class UINavigateToParams(BaseModel):
    """`navigate_to`: redireciona para uma página interna."""

    page: str = Field(..., min_length=1, max_length=512)
    query: dict[str, str] = Field(default_factory=dict)


class UIOpenModalParams(BaseModel):
    """`open_modal`: abre um modal genérico via `lia:open_modal` event."""

    modal_id: str = Field(..., min_length=1, max_length=128)
    data: dict[str, Any] | None = None


class UIOpenOfferReviewParams(BaseModel):
    """`open_offer_review`: abre o OfferReviewModal (PR-B)."""

    candidate_id: str = Field(..., min_length=1, max_length=128)
    job_id: str = Field(..., min_length=1, max_length=128)
    draft_id: str | None = Field(default=None, max_length=128)


class UIWizardStepParams(BaseModel):
    """`wizard_step`: avança um wizard ativo no FE."""

    wizard: str = Field(..., min_length=1, max_length=64)
    step: str = Field(..., min_length=1, max_length=64)


class UIOpenPanelParams(BaseModel):
    """`open_panel`: abre painel lateral (delegado ao `useUIActions` plural)."""

    panel: str = Field(..., min_length=1, max_length=64)
    entity_id: str | None = Field(default=None, max_length=128)


class UIScrollToParams(BaseModel):
    """`scroll_to`: rola viewport até `element_id`."""

    element_id: str = Field(..., min_length=1, max_length=128)


class UISettingsOpenTabParams(BaseModel):
    """`settings_open_tab`: bridge chat → SettingsPageEnhanced (WT-2022 Fase 4).

    Espelha REST path canonical. ``section`` é required mínimo; ``subsection``
    opcional pra deep-link em sub-aba (e.g., learning-loops).
    """

    section: str = Field(..., min_length=1, max_length=64)
    subsection: str | None = Field(default=None, max_length=64)


class UIApplyTableStateParams(BaseModel):
    """`apply_table_state`: filtra/busca/ordena a tabela in-page (Fase 2 slice 1).
    Espelha a variante TS GlobalUIAction.apply_table_state. patch é camelCase
    (search, sortBy, sortOrder, quickFilters, tab). `tab` (Fase 2 funil tabs)
    troca a aba do Funil no FE via setActiveTab (search/favorites/lists/
    history/saved-searches/agents). patch é dict aberto — sem mudança de
    schema. Read-only UI — não muta dados."""

    surface: Literal["candidates", "jobs", "kanban", "talent_pool", "recrutar"]
    patch: dict[str, Any] = Field(default_factory=dict)


GLOBAL_UI_ACTION_TYPES: tuple[str, ...] = (
    "navigate_to",
    "open_modal",
    "open_offer_review",
    "wizard_step",
    "open_panel",
    "scroll_to",
    "settings_open_tab",  # WT-2022 Fase 4: bridge chat → SettingsPageEnhanced
    "apply_table_state",  # Fase 2 slice 1: ponte in-page (filtra/ordena tabela)
)
"""Espelho runtime do `GLOBAL_UI_ACTION_TYPES` em `src/types/ui-action.ts`."""


_UI_ACTION_PARAMS_BY_TYPE: dict[str, type[BaseModel]] = {
    "navigate_to": UINavigateToParams,
    "open_modal": UIOpenModalParams,
    "open_offer_review": UIOpenOfferReviewParams,
    "wizard_step": UIWizardStepParams,
    "open_panel": UIOpenPanelParams,
    "scroll_to": UIScrollToParams,
    "settings_open_tab": UISettingsOpenTabParams,  # WT-2022 Fase 4
    "apply_table_state": UIApplyTableStateParams,  # Fase 2 slice 1
}


class UIAction(BaseModel):
    """Wire-format de UIAction (boundary BE→FE).

    Tipo é string aberto para permitir actions page-specific
    (ex.: ``move_candidate`` no kanban) que NÃO são tratadas pelo
    handler global e são re-emitidas via ``lia:unhandled_ui_action``
    CustomEvent no FE.

    Para actions globais (``GLOBAL_UI_ACTION_TYPES``), use o helper
    ``validate_global_ui_action_params`` para validação strict do
    schema dos params.
    """

    type: str = Field(..., min_length=1, max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "ignore"}


def validate_global_ui_action_params(
    action_type: str, params: dict[str, Any]
) -> BaseModel | None:
    """Valida params de uma UIAction global.

    Returns:
        Modelo Pydantic validado se ``action_type`` é global e params são
        válidos. ``None`` se action_type não é global (caller deve assumir
        page-specific) OU se os params falharam validação strict.

    Skill: harness-engineering [sensor no boundary] — rejeita drifts de
    schema entre FE/BE antes que cheguem ao runtime.
    """
    schema = _UI_ACTION_PARAMS_BY_TYPE.get(action_type)
    if schema is None:
        return None
    try:
        return schema.model_validate(params)
    except Exception:
        return None


class WSPingMessage(BaseModel):
    model_config = ConfigDict(extra='forbid')

    type: Literal["ping"] = "ping"


class WSAbortMessage(BaseModel):
    model_config = ConfigDict(extra='forbid')

    type: Literal["abort"] = "abort"


# ---------------------------------------------------------------------------
# Servidor → Cliente
# ---------------------------------------------------------------------------

class WSConnectedMessage(BaseModel):
    model_config = ConfigDict(extra='forbid')

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

    model_config = ConfigDict(extra='forbid')

    type: Literal["thinking"] = "thinking"
    job_id: str | None = Field(
        default=None,
        description="ID do job assíncrono (Celery task ou correlation_id RabbitMQ)",
    )
    timestamp: str = ""


class WSTokenMessage(BaseModel):
    """Chunk de streaming — enviado durante geração de token a token."""

    model_config = ConfigDict(extra='forbid')

    type: Literal["token"] = "token"
    content: str = Field(..., description="Chunk de texto gerado pelo LLM")
    timestamp: str = ""


class WSResponseMessage(BaseModel):
    """Resposta final completa do agente."""

    model_config = ConfigDict(extra='forbid')

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
    model_config = ConfigDict(extra='forbid')

    type: Literal["error"] = "error"
    message: str
    code: str | None = None
    timestamp: str = ""


class WSPongMessage(BaseModel):
    model_config = ConfigDict(extra='forbid')

    type: Literal["pong"] = "pong"
    timestamp: str = ""
