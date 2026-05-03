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
    name = td.name
    description = td.description or f"Executa {name}"

    if inspect.iscoroutinefunction(fn):
        return StructuredTool.from_function(
            coroutine=fn,
            name=name,
            description=description,
        )
    return StructuredTool.from_function(
        func=fn,
        name=name,
        description=description,
    )
