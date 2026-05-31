"""Wizard Orchestrator — deterministic tool layer.

Camada de capacidades determinísticas do orquestrador conversacional de
criação de vaga (strangler-fig migration do pipeline LangGraph rígido para
um tool-calling agent state-aware, decisão Paulo 2026-05-31).

## Princípio canônico (Agent = Model + Harness)

O LLM (cérebro) decide QUAL capacidade invocar; estas tools são o HARNESS
determinístico onde vivem os invariantes não-negociáveis:

  - **Multi-tenancy fail-closed**: ``company_id`` vem SEMPRE de ``ToolContext``
    (derivado do JWT no caller), NUNCA dos args gerados pela LLM. Toda tool
    que recebe ``company_id`` no ``tool_input`` o rejeita explicitamente
    (defesa contra prompt injection cross-tenant — ver CLAUDE.md REGRA 2/R6).
  - **Validação no boundary**: o ``tool_input`` é input de LLM = boundary não
    confiável. Validamos tipo/forma/allowlist antes de mutar state.
  - **Sem ação livre**: nenhuma tool faz ``eval``/``exec`` sobre output do LLM.
    A mutação de state é determinística baseada apenas em campos validados.

## Contrato

Cada tool é um :class:`WizardTool` com schema Anthropic (``name`` +
``description`` + ``input_schema``) e um ``handler``
``(state, tool_input, ctx) -> ToolResult``. O handler NUNCA levanta exceção
para o loop do orquestrador — falhas viram ``ToolResult(error=True, ...)``
com mensagem acionável para o LLM (otimizada para consumo do modelo, não só
humano — harness-engineering).

Este módulo é PURO (sem I/O, sem DB, sem rede) para as 4 tools de increment 1.
Tools service-backed (enrich_jd, suggest_competencies, ...) vivem em
``wizard_service_tools.py`` (increment 2) e fazem I/O via os serviços canônicos.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ── Contratos ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ToolContext:
    """Contexto de execução de tool — fonte canônica de identidade do tenant.

    ``company_id`` e ``user_id`` vêm do JWT no caller (WizardSessionService),
    NUNCA dos args da LLM. Frozen para impedir mutação acidental durante o loop.
    """

    company_id: str
    user_id: Optional[str] = None
    workspace_id: Optional[int] = None
    language: str = "pt-BR"


@dataclass
class ToolResult:
    """Resultado determinístico de uma tool.

    Attributes:
        state_updates: campos a fazer merge no ``JobCreationState``. Vazio
            para tools read-only (ex.: ``get_wizard_status``).
        llm_message: conteúdo do ``tool_result`` realimentado ao LLM no
            próximo passo do loop. Deve ser conciso e factual.
        error: ``True`` quando a tool falhou validação/execução. O
            ``llm_message`` então contém instrução de correção para o LLM.
    """

    llm_message: str
    state_updates: dict[str, Any] = field(default_factory=dict)
    error: bool = False


ToolHandler = Callable[[dict, dict, ToolContext], ToolResult]


@dataclass(frozen=True)
class WizardTool:
    """Definição de uma tool: schema Anthropic + handler determinístico."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler

    def anthropic_schema(self) -> dict[str, Any]:
        """Schema no formato esperado pela API Anthropic (``tools=[...]``)."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


# Defesa-em-profundidade: NENHUM tool_input pode carregar identidade de tenant.
# Multi-tenancy canonical — company_id vem só do ToolContext (JWT).
_TENANT_FORBIDDEN_KEYS: frozenset[str] = frozenset({
    "company_id", "workspace_id", "user_id", "tenant_id", "x_company_id",
})


def _reject_tenant_keys(tool_input: dict) -> Optional[str]:
    """Retorna mensagem de erro se o tool_input tentar setar identidade de tenant.

    Vetor de prompt injection cross-tenant: a LLM (potencialmente influenciada
    por conteúdo do recrutador) tenta passar ``company_id`` de outra empresa.
    Rejeitamos fail-loud. Ver CLAUDE.md REGRA 2/R6.
    """
    offending = [k for k in tool_input if k.lower() in _TENANT_FORBIDDEN_KEYS]
    if offending:
        return (
            f"Campos de identidade de tenant não são permitidos no input: "
            f"{', '.join(sorted(offending))}. A empresa é determinada pelo "
            f"contexto de autenticação, não pelo argumento da tool."
        )
    return None


# ── Validação de campos de intake ──────────────────────────────────────────

# Normalização de modelo de trabalho (PT-BR livre → canonical).
_MODEL_NORMALIZE: dict[str, str] = {
    "remoto": "remote", "remote": "remote", "home office": "remote",
    "home-office": "remote", "100% remoto": "remote",
    "híbrido": "hybrid", "hibrido": "hybrid", "hybrid": "hybrid",
    "presencial": "onsite", "onsite": "onsite", "on-site": "onsite",
    "escritório": "onsite", "escritorio": "onsite",
}

_EMPLOYMENT_NORMALIZE: dict[str, str] = {
    "clt": "CLT", "pj": "PJ", "estágio": "estagio", "estagio": "estagio",
    "temporário": "temporario", "temporario": "temporario",
    "freelancer": "freelancer", "freela": "freelancer",
}

# Campos de intake que set_job_fields aceita. Cada um mapeia para a chave
# canonical do JobCreationState.
_SETTABLE_JOB_FIELDS: frozenset[str] = frozenset({
    "title", "department", "seniority", "location", "model",
    "employment_type", "manager_name", "manager_email",
})

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_MAX_FIELD_LEN = 200


def _normalize_field(name: str, value: str) -> tuple[Optional[str], Optional[str]]:
    """Normaliza/valida um campo. Retorna (valor_canonical, erro)."""
    v = (value or "").strip()
    if not v:
        return None, f"Campo '{name}' veio vazio."
    if len(v) > _MAX_FIELD_LEN:
        return None, f"Campo '{name}' excede {_MAX_FIELD_LEN} caracteres."

    if name == "model":
        norm = _MODEL_NORMALIZE.get(v.lower())
        if not norm:
            return None, (
                f"Modelo de trabalho '{v}' não reconhecido. Use: remoto, "
                f"híbrido ou presencial."
            )
        return norm, None

    if name == "employment_type":
        norm = _EMPLOYMENT_NORMALIZE.get(v.lower())
        if not norm:
            return None, (
                f"Tipo de contrato '{v}' não reconhecido. Use: CLT, PJ, "
                f"estágio, temporário ou freelancer."
            )
        return norm, None

    if name == "manager_email":
        if not _EMAIL_RE.match(v):
            return None, f"Email do gestor '{v}' é inválido."
        return v, None

    return v, None


# Mapeamento campo da tool → chave canonical do JobCreationState.
_FIELD_TO_STATE_KEY: dict[str, str] = {
    "title": "parsed_title",
    "department": "parsed_department",
    "seniority": "parsed_seniority",
    "location": "parsed_location",
    "model": "parsed_model",
    "employment_type": "parsed_employment_type",
    "manager_name": "parsed_manager_name",
    "manager_email": "parsed_manager_email",
}


# ── Handlers ─────────────────────────────────────────────────────────────


def _handle_set_job_fields(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Seta um ou mais campos de intake da vaga (parsed_*). Validado."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    unknown = [k for k in tool_input if k not in _SETTABLE_JOB_FIELDS]
    if unknown:
        return ToolResult(
            llm_message=(
                f"Campos desconhecidos: {', '.join(sorted(unknown))}. "
                f"Campos válidos: {', '.join(sorted(_SETTABLE_JOB_FIELDS))}."
            ),
            error=True,
        )

    updates: dict[str, Any] = {}
    applied: list[str] = []
    for name, raw in tool_input.items():
        norm, err = _normalize_field(name, str(raw))
        if err:
            return ToolResult(llm_message=err, error=True)
        updates[_FIELD_TO_STATE_KEY[name]] = norm
        applied.append(f"{name}={norm!r}")

    if not updates:
        return ToolResult(
            llm_message="Nenhum campo fornecido para atualizar.", error=True
        )

    return ToolResult(
        llm_message=f"Campos atualizados: {', '.join(applied)}.",
        state_updates=updates,
    )


def _handle_set_screening_mode(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Define o modo de triagem WSI: compact (7 perguntas) ou full (12)."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    mode = str(tool_input.get("mode") or "").strip().lower()
    if mode not in ("compact", "full"):
        return ToolResult(
            llm_message=(
                "Modo inválido. Use 'compact' (7 perguntas, ~10min) ou "
                "'full' (12 perguntas, ~18min)."
            ),
            error=True,
        )
    label = "Compacto (7 perguntas)" if mode == "compact" else "Completo (12 perguntas)"
    return ToolResult(
        llm_message=f"Modo de triagem definido: {label}.",
        state_updates={"screening_mode": mode},
    )


def _handle_confirm_competencies(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Confirma as competências técnicas e comportamentais da vaga.

    Aceita ``technical`` e ``behavioral`` como listas de strings (nomes das
    competências). Persiste no formato canonical consumido pelo jd_enrichment
    invertido (Fase 4): técnicas = [{"skill": ...}], comportamentais =
    [{"competencia": ...}].
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    technical = tool_input.get("technical")
    behavioral = tool_input.get("behavioral")
    if technical is None and behavioral is None:
        return ToolResult(
            llm_message=(
                "Forneça ao menos uma lista: 'technical' e/ou 'behavioral' "
                "com os nomes das competências."
            ),
            error=True,
        )

    def _coerce(items: Any, key: str) -> tuple[list[dict], Optional[str]]:
        if items is None:
            return [], None
        if not isinstance(items, list):
            return [], f"'{key}' deve ser uma lista de strings."
        out: list[dict] = []
        for it in items:
            name = (str(it).strip() if not isinstance(it, dict)
                    else str(it.get("skill") or it.get("competencia") or it.get("name") or "").strip())
            if name:
                out.append({key: name})
        return out, None

    tech, err1 = _coerce(technical, "skill")
    if err1:
        return ToolResult(llm_message=err1, error=True)
    behav, err2 = _coerce(behavioral, "competencia")
    if err2:
        return ToolResult(llm_message=err2, error=True)

    updates: dict[str, Any] = {
        "confirmed_technical_competencies": tech,
        "confirmed_behavioral_competencies": behav,
        "intake_competencies_suggested": True,
    }
    return ToolResult(
        llm_message=(
            f"Competências confirmadas: {len(tech)} técnicas, "
            f"{len(behav)} comportamentais."
        ),
        state_updates=updates,
    )


def _handle_get_wizard_status(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Read-only: retorna a ficha viva (o que está preenchido vs faltante).

    Reusa ``_build_wizard_state_summary`` (single source of truth para a
    ficha viva — também usada pelo meta-helper state-aware).
    """
    try:
        from app.domains.job_creation.internal.utils import (
            _build_wizard_state_summary,
        )
        summary = _build_wizard_state_summary(state)
    except Exception as exc:  # noqa: BLE001 — fail-soft, status é informativo
        logger.warning("[WizardTools] status summary failed: %s", exc)
        summary = "(não foi possível montar o status agora)"
    return ToolResult(llm_message=summary)


# ── Registry ─────────────────────────────────────────────────────────────


SET_JOB_FIELDS = WizardTool(
    name="set_job_fields",
    description=(
        "Define ou atualiza um ou mais campos básicos da vaga. Use sempre que "
        "o recrutador fornecer ou corrigir: título, departamento, senioridade, "
        "localização, modelo de trabalho, tipo de contrato, nome ou email do "
        "gestor. Pode ser chamada a qualquer momento, inclusive para CORRIGIR "
        "um campo já preenchido (ex.: recrutador muda a senioridade no meio do "
        "fluxo)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Título do cargo."},
            "department": {"type": "string", "description": "Departamento/área."},
            "seniority": {"type": "string", "description": "Senioridade (júnior, pleno, sênior, etc.)."},
            "location": {"type": "string", "description": "Localização (cidade/estado)."},
            "model": {"type": "string", "description": "Modelo: remoto, híbrido ou presencial."},
            "employment_type": {"type": "string", "description": "Contrato: CLT, PJ, estágio, temporário, freelancer."},
            "manager_name": {"type": "string", "description": "Nome do gestor responsável."},
            "manager_email": {"type": "string", "description": "Email do gestor responsável."},
        },
        "additionalProperties": False,
    },
    handler=_handle_set_job_fields,
)

SET_SCREENING_MODE = WizardTool(
    name="set_screening_mode",
    description=(
        "Define o modo de triagem WSI da vaga. 'compact' = 7 perguntas (~10 "
        "min, triagem rápida). 'full' = 12 perguntas (~18 min, avaliação "
        "aprofundada). Use quando o recrutador escolher o modo."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["compact", "full"]},
        },
        "required": ["mode"],
        "additionalProperties": False,
    },
    handler=_handle_set_screening_mode,
)

CONFIRM_COMPETENCIES = WizardTool(
    name="confirm_competencies",
    description=(
        "Confirma as competências técnicas e comportamentais que serão usadas "
        "na vaga e na geração da descrição. Use depois que o recrutador revisar "
        "ou ajustar as competências sugeridas. Forneça os nomes em 'technical' "
        "e 'behavioral'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "technical": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Nomes das competências técnicas.",
            },
            "behavioral": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Nomes das competências comportamentais.",
            },
        },
        "additionalProperties": False,
    },
    handler=_handle_confirm_competencies,
)

GET_WIZARD_STATUS = WizardTool(
    name="get_wizard_status",
    description=(
        "Retorna o estado atual da vaga em construção: campos preenchidos, "
        "campos faltantes, status da descrição, competências e modo de triagem. "
        "Use quando o recrutador perguntar 'o que falta?', 'onde estamos?', "
        "'o que você precisa?' ou antes de avançar para uma etapa que exige "
        "campos anteriores."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_get_wizard_status,
)


# Tools puras de increment 1. Service-backed tools são adicionadas via
# ``register_service_tools`` (increment 2) para manter este módulo I/O-free.
PURE_TOOLS: tuple[WizardTool, ...] = (
    SET_JOB_FIELDS,
    SET_SCREENING_MODE,
    CONFIRM_COMPETENCIES,
    GET_WIZARD_STATUS,
)


def build_tool_registry(
    extra_tools: tuple[WizardTool, ...] = (),
) -> dict[str, WizardTool]:
    """Constrói o registry name→WizardTool (puras + extras service-backed)."""
    registry: dict[str, WizardTool] = {t.name: t for t in PURE_TOOLS}
    for t in extra_tools:
        registry[t.name] = t
    return registry
