"""
Tool Adapter — ToolContract (canônico) e tool_definition_to_langchain_tool.

ToolContract é o contrato enterprise canônico para tools LIA.
Declara explicitamente:
  - Contratos de entrada/saída (parameters + output_schema)
  - Efeitos colaterais (side_effects)
  - PII / LGPD (touches_pii, pii_output_fields, lgpd_legal_basis)
  - Fairness / Governança (affects_candidate_decision, requires_human_review)
  - Observabilidade (sla_ms)

ToolDefinition é mantido como alias para backward compatibility com os 223
tool registries existentes — sem quebrar nenhum import.

Uso:
    from lia_agents_core.tool_adapter import ToolContract, tool_definition_to_langchain_tool

    tc = ToolContract(
        name="move_candidate_stage",
        description="Move candidato de etapa no pipeline",
        function=_wrap_move,
        side_effects=["write"],
        affects_candidate_decision=True,
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "data": {"type": "object"},
                "message": {"type": "string"},
            },
            "required": ["success"],
        },
    )
"""
from typing import Any, Callable, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ToolOutput(BaseModel):
    """R-004 (Sprint 1): contrato canonical para output de tools.

    Disambiguado em relacao a app/tools/executor.py::ToolResult (semantica
    diferente: ToolResult = wrapper de execucao do executor, ToolOutput =
    schema do retorno funcional do tool).

    Uso (canonical em tool_registries):

        ToolDefinition(
            name="send_email",
            description="...",
            function=_wrap_send_email,
            output_schema=ToolOutput,
        )

    Tools podem subclassar ToolOutput para enriquecer o contrato com campos
    especificos do dominio (ex: SendEmailOutput(ToolOutput): message_id: str).

    NOTA: classe restaurada em integration branch — foi perdida no cherry-pick
    de ad21517c9 (ToolContract canonical) que reescreveu este arquivo. Lib
    aceita esta classe como output_schema declarado em todas ToolDefinitions.
    """

    success: bool = Field(..., description="Tool executou com sucesso?")
    message: str = Field(..., description="Mensagem human-readable do resultado")
    data: dict[str, Any] | None = Field(
        default=None,
        description="Payload opcional com dados estruturados retornados pelo tool",
    )


class ToolContract(BaseModel):
    """
    Contrato enterprise canônico para tools LIA.

    Harness Engineering (Hashimoto):
      Guide (feedforward): campos obrigatórios declaram intenção antes da execução.
      Sensor (feedback): ToolExecutor valida output_schema e aplica fairness/PII/audit.

    Todos os campos de governança têm defaults seguros (fail-closed):
      - requires_company_id=True  → rejeita tool sem tenant
      - side_effects=["read"]     → conservador por padrão
      - touches_pii=False         → mascaramento opt-in
      - affects_candidate_decision=False → fairness guard opt-in
    """

    # ── Identidade ────────────────────────────────────────────────────────────
    name: str = Field(..., description="Nome único do tool")
    description: str = Field(..., description="O que o tool faz (visível ao LLM)")
    version: str = Field("1.0.0", description="Versão semântica do contrato")
    owner_team: str = Field("backend", description="Time responsável")

    # ── Contratos de dados ────────────────────────────────────────────────────
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema descrevendo os parâmetros de entrada",
    )
    output_schema: Any = Field(
        default_factory=dict,
        description="JSON Schema (dict) ou classe Pydantic (BaseModel) do output do tool.",
    )

    # ── Efeitos colaterais ────────────────────────────────────────────────────
    side_effects: List[Literal["read", "write", "send", "delete"]] = Field(
        default_factory=lambda: ["read"],
        description="Efeitos colaterais declarados. Default conservador: ['read'].",
    )

    # ── Multi-tenancy ─────────────────────────────────────────────────────────
    requires_company_id: bool = Field(
        True,
        description="Rejeita execução sem company_id. Default: True (fail-closed).",
    )

    # ── PII / LGPD ────────────────────────────────────────────────────────────
    touches_pii: bool = Field(
        False,
        description="True se o output contém campos PII (nome, e-mail, CPF, telefone...).",
    )
    pii_output_fields: List[str] = Field(
        default_factory=list,
        description="Campos do output que contêm PII (ex: ['name','email','phone']).",
    )
    lgpd_legal_basis: Optional[str] = Field(
        None,
        description="Base legal LGPD para acesso a dados pessoais (ex: 'legitimate_interest').",
    )

    # ── Fairness / Governança ─────────────────────────────────────────────────
    affects_candidate_decision: bool = Field(
        False,
        description="True se o tool afeta o destino do candidato. Ativa FairnessGuard.",
    )
    requires_human_review: bool = Field(
        False,
        description="True se o output requer revisão humana (HITL gate).",
    )

    # ── Observabilidade ───────────────────────────────────────────────────────
    sla_ms: int = Field(
        5000,
        description="SLA de latência esperado em ms. Usado para alertas de timeout.",
    )

    # ── Função ────────────────────────────────────────────────────────────────
    function: Callable = Field(
        ...,
        description="Função async ou sync executada quando o tool é chamado",
    )

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("side_effects", mode="before")
    @classmethod
    def validate_side_effects(cls, v: Any) -> Any:
        allowed = {"read", "write", "send", "delete"}
        if isinstance(v, list):
            invalid = [e for e in v if e not in allowed]
            if invalid:
                raise ValueError(
                    f"side_effects inválidos: {invalid}. "
                    f"Valores permitidos: {sorted(allowed)}. "
                    "Corrija o ToolContract declarando apenas efeitos reais do tool."
                )
        return v


# Alias backward-compatible: os 223 tool registries existentes importam
# ToolDefinition — mantemos o nome funcionando sem nenhuma migração.
ToolDefinition = ToolContract



def _parameters_to_args_schema(name: str, parameters: Dict[str, Any]) -> Any:
    """Convert ToolContract.parameters (JSON Schema dict) to a Pydantic model
    suitable for StructuredTool.args_schema.

    Without args_schema, LangChain infers schema from the function signature.
    Since tee wrappers have ``*args, **kwargs``, it creates a single ``kwargs``
    field — causing double-nesting: the LLM sends ``{"kwargs": {"field": val}}``
    instead of ``{"field": val}``, and handlers that read ``kwargs.get("field")``
    get None.
    """
    from pydantic import create_model as _create_model
    from pydantic import Field as _Field

    if not parameters or not isinstance(parameters, dict):
        return None
    props = parameters.get("properties")
    if not props:
        return None

    required = set(parameters.get("required", []))
    _TYPE_MAP = {
        "string": str, "integer": int, "number": float,
        "boolean": bool, "array": list, "object": dict,
    }

    fields: Dict[str, Any] = {}
    for fname, fschema in props.items():
        raw_type = fschema.get("type", "string")
        if isinstance(raw_type, list):
            raw_type = next((t for t in raw_type if t != "null"), "string")
        py_type = _TYPE_MAP.get(raw_type, str)
        desc = fschema.get("description", "")
        extra: Dict[str, Any] = {}
        if "enum" in fschema:
            extra["enum"] = fschema["enum"]
        if fname in required:
            fields[fname] = (
                py_type,
                _Field(description=desc, **({"json_schema_extra": extra} if extra else {})),
            )
        else:
            fields[fname] = (
                Optional[py_type],
                _Field(default=None, description=desc, **({"json_schema_extra": extra} if extra else {})),
            )

    try:
        return _create_model(f"{name}_args", **fields)
    except Exception:
        return None


def tool_definition_to_langchain_tool(td: ToolContract) -> Any:
    """
    Converte um ToolContract em LangChain StructuredTool compatível com
    LangGraph create_react_agent.

    Suporta funções async e sync automaticamente.

    Uso em agentes (_get_tools()):
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        lc_tools = [tool_definition_to_langchain_tool(tc) for tc in get_my_tools()]
    """
    import inspect

    try:
        from langchain_core.tools import StructuredTool
    except ImportError as exc:
        raise ImportError(
            "langchain-core não instalado — necessário para LangGraph"
        ) from exc

    fn = td.function
    # wire-B canonical (2026-06-06): tee response_blocks de TODA tool pro
    # rrp_block_sink ANTES da stringificacao do StructuredTool, p/ que os
    # domain agents (talent/jobs/kanban) — nao so o federado — preservem os
    # blocks. Defensivo: tee_tool_function nunca levanta nem altera o retorno.
    try:
        from app.shared.rrp_block_sink import tee_tool_function
        fn = tee_tool_function(fn)
    except Exception:
        pass
    # HITL surfacing (AUD-4 1b, 2026-06-07): tee needs_confirmation pro
    # hitl_pending_sink (irmao do rrp). Mesmo ponto, defensivo, passthrough.
    try:
        from app.shared.hitl_pending_sink import tee_tool_function as _hitl_tee
        fn = _hitl_tee(fn)
    except Exception:
        pass
    # Fase 2 (2026-06-09): tee da diretiva ui_action (open_modal/navigate_to/
    # apply_table_state) pro ui_action_sink (irmao do rrp/hitl). Sem isso a
    # diretiva morre na stringificacao do ToolMessage no caminho federado
    # (ReAct) — open_ui/apply_table_state nao chegavam ao FE. Defensivo.
    try:
        from app.shared.ui_action_sink import tee_tool_function as _uia_tee
        fn = _uia_tee(fn)
    except Exception:
        pass
    # STL-GATE (Stop-The-Lie): reescreve resultado de ghost tools
    # (side_effect_executed=False + success=True) ANTES da stringificacao.
    # Outermost tee = primeiro a processar o resultado.
    try:
        from app.shared.stl_gate_sink import tee_tool_function as _stl_tee
        fn = _stl_tee(fn)
    except Exception:
        pass
    name = td.name
    description = td.description or f"Executa {name}"

    _schema = _parameters_to_args_schema(name, td.parameters)

    if inspect.iscoroutinefunction(fn):
        return StructuredTool.from_function(
            coroutine=fn,
            name=name,
            description=description,
            args_schema=_schema,
            infer_schema=_schema is None,
        )
    return StructuredTool.from_function(
        func=fn,
        name=name,
        description=description,
        args_schema=_schema,
        infer_schema=_schema is None,
    )


# ── Compatibility stubs ────────────────────────────────────────────────────
# ReActState and ReActConfig are legacy types from the removed ReActLoop.
# Kept here (canonical module) so that internal lib files can import them
# without touching react_loop.py shim.


class ReActState(BaseModel):
    """Stub de compatibilidade pós-migração LangGraph.

    Usado por learning_extractor, enhanced_agent_mixin e langgraph_react_base
    para sintetizar estado após execução LangGraph.
    Em produção, o estado real é gerenciado pelo LangGraph MessagesState.
    """

    messages: List[Dict[str, Any]] = Field(default_factory=list)
    current_reasoning: str = Field(default="")
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    should_respond: bool = Field(default=False)
    final_response: Optional[str] = Field(default=None)
    iteration: int = Field(default=0)
    tool_calls_made: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)
    failed_tool_calls: List[str] = Field(default_factory=list)
    consecutive_duplicate_count: int = Field(default=0)
    last_tool_call_key: Optional[str] = Field(default=None)
    tokens_used_estimate: int = Field(default=0)
    session_id: Optional[str] = Field(default=None)
    confidence_score: float = Field(default=0.5)
    streaming_callback: Optional[Any] = Field(default=None)

    model_config = {"arbitrary_types_allowed": True}


class ReActConfig(BaseModel):
    """Stub de compatibilidade — parâmetros do antigo ReActLoop.

    Mantido para enhanced_agent_mixin, conftest e testes que referenciam
    ReActConfig como tipo. Novos agentes devem usar LangGraphReActBase
    diretamente (configuração via create_react_agent).
    """

    system_prompt: str = ""
    available_tools: List[Any] = Field(default_factory=list)
    domain: str = ""
    max_iterations: int = 5
    model_provider: str = "claude"
    temperature: float = 0.3
    guardrails: List[Any] = Field(default_factory=list)
    active_scope: Optional[str] = None
