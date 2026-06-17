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

from app.domains.job_creation.services.seniority_resolver import (
    _infer_from_title,
    SENIORITY_DISPLAY_NAMES,
)


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
# Campos de responsáveis (T9): manager_name, manager_email, recruiter,
# recruiter_email são settáveis pelo LLM. PII masking em emails preservada
# (placeholder ignorado silenciosamente quando mascarado).
_SETTABLE_JOB_FIELDS: frozenset[str] = frozenset({
    "title", "department", "seniority", "location", "model",
    "employment_type", "manager_name", "manager_email",
    "recruiter", "recruiter_email",
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

    if name == "recruiter_email":
        if not _EMAIL_RE.match(v):
            return None, f"Email do recrutador '{v}' é inválido."
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
    "recruiter": "parsed_recruiter",
    "recruiter_email": "parsed_recruiter_email",
}


# ── Handlers ─────────────────────────────────────────────────────────────


def _is_masked_pii(value: str) -> bool:
    """Detecta o placeholder de PII mascarada (LGPD strip no inbound).

    O email do gestor é apagado pelo c3b/pii_masking ('[EMAIL REMOVIDO]')
    ANTES de chegar ao LLM. Se o LLM tentar setar manager_email com o
    placeholder, ignoramos — o email é capturado deterministicamente do
    texto cru no servidor (wizard layer), nunca pelo LLM.
    """
    v = (value or "").upper()
    return "REMOVIDO" in v or v.strip().startswith("[")


def _handle_set_job_fields(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Seta um ou mais campos de intake da vaga (parsed_*). Validado."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    # Campos de responsáveis (T9): manager_name, manager_email, recruiter,
    # recruiter_email são todos settáveis pelo LLM.
    _server_managed_note = None

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
    notes: list[str] = []
    for name, raw in tool_input.items():
        # Email mascarado (LGPD strip no inbound): ignorar placeholder.
        if name in ("manager_email", "recruiter_email") and _is_masked_pii(str(raw)):
            _label = "gestor" if name == "manager_email" else "recrutador"
            notes.append(
                f"O email do {_label} é capturado automaticamente do texto — "
                "não precisa pedir nem validar formato; se o recrutador "
                "mencionou um email, já está registrado."
            )
            continue
        norm, err = _normalize_field(name, str(raw))
        if err:
            return ToolResult(llm_message=err, error=True)
        updates[_FIELD_TO_STATE_KEY[name]] = norm
        applied.append(f"{name}={norm!r}")

    # T4: Seniority inference from title (deterministic, no DB)
    if "parsed_title" in updates and "parsed_seniority" not in updates:
        _title = updates["parsed_title"]
        _inferred_level, _inferred_conf = _infer_from_title(_title)
        if _inferred_level and _inferred_conf >= 0.8:
            _display = SENIORITY_DISPLAY_NAMES.get(_inferred_level, _inferred_level)
            updates["parsed_seniority"] = _inferred_level
            applied.append(
                f"seniority={_inferred_level!r} (inferido do titulo, "
                f"confianca {_inferred_conf:.0%})"
            )
            notes.append(
                f"Senioridade inferida do titulo: {_display}. "
                f"Confirme ou ajuste se necessario."
            )

    if _server_managed_note:
        notes.append(_server_managed_note)
    if not updates:
        if notes:
            return ToolResult(llm_message=" ".join(notes))
        return ToolResult(
            llm_message="Nenhum campo fornecido para atualizar.", error=True
        )

    msg = f"Campos atualizados: {', '.join(applied)}."
    if notes:
        msg += " " + " ".join(notes)
    return ToolResult(llm_message=msg, state_updates=updates)


def _handle_confirm_responsibilities(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Confirma as responsabilidades da vaga (lista de strings).

    Não-obrigatório: se o recrutador não fornecer, o jd_enrichment gera (e ele
    revisa na JD). Se confirmar, são usadas verbatim na descrição (Fase 4).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    items = tool_input.get("responsibilities")
    if not isinstance(items, list) or not items:
        return ToolResult(
            llm_message=(
                "Forneça 'responsibilities' como uma lista de frases de "
                "responsabilidade."
            ),
            error=True,
        )
    cleaned = [str(r).strip() for r in items if str(r).strip()]
    if not cleaned:
        return ToolResult(llm_message="Nenhuma responsabilidade válida fornecida.", error=True)
    return ToolResult(
        llm_message=(
            f"Responsabilidades confirmadas: {len(cleaned)}. Serão usadas na "
            f"descrição da vaga."
        ),
        state_updates={"confirmed_responsibilities": cleaned},
    )


def _handle_confirm_languages(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Confirma os idiomas exigidos pela vaga + nível.

    Não-obrigatório. Captura o que o recrutador mencionar (ex.: "inglês avançado")
    para a coluna `languages` da vaga. Shape canonical: [{language, level, required}].
    Nível normalizado p/ FE (Básico/Intermediário/Avançado/Fluente/Nativo).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    items = tool_input.get("languages")
    if not isinstance(items, list) or not items:
        return ToolResult(
            llm_message="Forneça 'languages' como lista de {language, level}.",
            error=True,
        )
    from app.domains.job_creation.helpers.vacancy_vocab import (
        to_canonical_language_level,
    )
    out: list[dict[str, Any]] = []
    for it in items:
        if isinstance(it, dict):
            lang = str(it.get("language") or it.get("idioma") or it.get("name") or "").strip()
            level = it.get("level") or it.get("nivel")
            required = bool(it.get("required", False))
        else:
            lang, level, required = str(it).strip(), None, False
        if lang:
            out.append({
                "language": lang[:60],
                "level": to_canonical_language_level(level),
                "required": required,
            })
    if not out:
        return ToolResult(llm_message="Nenhum idioma válido fornecido.", error=True)
    _names = ", ".join(f"{x['language']} ({x['level']})" for x in out)
    return ToolResult(
        llm_message=f"Idiomas confirmados: {_names}.",
        state_updates={"confirmed_languages": out},
    )


def _handle_approve_job_description(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Registra a aprovação da descrição (JD) pelo recrutador (jd_approved=True).

    Pré-requisito: a JD precisa ter sido gerada (enrich_job_description). Sem
    esta tool, o publish_job nunca destrava — era a causa do loop de
    'publicação alucinada'. Só chame quando o recrutador aprovar explicitamente.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    if not state.get("jd_enriched"):
        return ToolResult(
            llm_message=(
                "Não há descrição gerada para aprovar. Gere a JD primeiro "
                "(enrich_job_description)."
            ),
            error=True,
        )
    return ToolResult(
        llm_message=(
            "Descrição aprovada pelo recrutador. Agora você pode publicar a "
            "vaga (publish_job com confirm=true) quando ele confirmar."
        ),
        state_updates={"jd_approved": True},
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



def _handle_set_screening_deadline(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Define o prazo de triagem em horas. Default da empresa: 48h."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    hours = tool_input.get("hours")
    if not hours or not isinstance(hours, (int, float)):
        return ToolResult(
            llm_message="Erro: informe o prazo em horas (ex: 48).",
            error=True,
        )
    hours = int(hours)
    if hours < 12 or hours > 720:
        return ToolResult(
            llm_message="Erro: prazo deve ser entre 12h e 720h (30 dias).",
            error=True,
        )
    if hours <= 24:
        display = f"{hours}h"
    elif hours % 24 == 0:
        days = hours // 24
        display = f"{days} dia{'s' if days > 1 else ''}"
    else:
        display = f"{hours}h (~{hours // 24} dias)"
    return ToolResult(
        llm_message=f"Prazo de triagem definido: {display} a partir da publicacao.",
        state_updates={"screening_deadline_hours": hours},
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


def _handle_update_competencies(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Adiciona/remove competências via DELTAS (sem reenviar a lista inteira).

    Lê as listas atuais do state (confirmadas, com fallback para as sugeridas —
    mesmo padrão de ``_competency_tree_for_panel``), aplica remoções (match
    case-insensitive por nome) e adições (append sem duplicar), e grava as
    listas completas em ``confirmed_*`` via ``state_updates`` — o que faz o
    painel lateral refletir a mudança no mesmo turno.

    Shape canonical (igual a ``_handle_confirm_competencies``): técnicas =
    [{"skill": ...}], comportamentais = [{"competencia": ...}]. Preserva
    ``contexto``/``trait_big_five`` de itens já existentes em formato dict.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    def _coerce_delta(items: Any, label: str) -> tuple[list[str], Optional[str]]:
        if items is None:
            return [], None
        if not isinstance(items, list):
            return [], f"'{label}' deve ser uma lista de nomes (strings)."
        out: list[str] = []
        for it in items:
            if not isinstance(it, str):
                return [], f"'{label}' deve conter apenas nomes (strings)."
            name = it.strip()
            if name:
                out.append(name)
        return out, None

    add_tech, e1 = _coerce_delta(tool_input.get("add_technical"), "add_technical")
    if e1:
        return ToolResult(llm_message=e1, error=True)
    rem_tech, e2 = _coerce_delta(tool_input.get("remove_technical"), "remove_technical")
    if e2:
        return ToolResult(llm_message=e2, error=True)
    add_behav, e3 = _coerce_delta(tool_input.get("add_behavioral"), "add_behavioral")
    if e3:
        return ToolResult(llm_message=e3, error=True)
    rem_behav, e4 = _coerce_delta(tool_input.get("remove_behavioral"), "remove_behavioral")
    if e4:
        return ToolResult(llm_message=e4, error=True)

    if not (add_tech or rem_tech or add_behav or rem_behav):
        return ToolResult(
            llm_message="Informe ao menos uma competência para adicionar ou remover.",
            error=True,
        )

    sugg = state.get("suggested_competencies") or {}
    # Base das listas para o delta: distinguir "chave ausente" (nunca confirmada
    # → fallback para sugeridas) de "chave presente porém vazia" (recrutador
    # removeu tudo → base permanece vazia). Usar ``or`` direto sobre as listas
    # confirmadas trataria ``[]`` como falsy e ressuscitaria as sugeridas,
    # quebrando a semântica de delta (item removido voltava no próximo turno).
    if "confirmed_technical_competencies" in state:
        cur_tech = state.get("confirmed_technical_competencies") or []
    else:
        cur_tech = sugg.get("technical") or []
    if "confirmed_behavioral_competencies" in state:
        cur_behav = state.get("confirmed_behavioral_competencies") or []
    else:
        cur_behav = sugg.get("behavioral") or []

    def _name_of(item: Any) -> str:
        if isinstance(item, dict):
            return str(
                item.get("skill")
                or item.get("competencia")
                or item.get("name")
                or ""
            ).strip()
        return str(item).strip()

    def _normalize_tech(item: Any) -> dict:
        if isinstance(item, dict):
            d = {"skill": _name_of(item)}
            if item.get("contexto"):
                d["contexto"] = item["contexto"]
            return d
        return {"skill": str(item).strip(), "contexto": ""}

    def _normalize_behav(item: Any) -> dict:
        if isinstance(item, dict):
            d = {"competencia": _name_of(item)}
            d["contexto"] = item.get("contexto", "") or ""
            d["trait_big_five"] = (
                item.get("trait_big_five", "")
                or item.get("trait_ocean", "")
                or ""
            )
            return d
        return {"competencia": str(item).strip(), "contexto": "", "trait_big_five": ""}

    def _apply(current, removals, additions, normalize, new_item):
        rem_lc = {r.lower() for r in removals}
        result = [
            normalize(it)
            for it in current
            if _name_of(it) and _name_of(it).lower() not in rem_lc
        ]
        existing_lc = {d.get("skill") or d.get("competencia") for d in result}
        existing_lc = {str(x).lower() for x in existing_lc if x}
        for name in additions:
            if name.lower() not in existing_lc:
                result.append(new_item(name))
                existing_lc.add(name.lower())
        return result

    tech = _apply(
        cur_tech, rem_tech, add_tech, _normalize_tech,
        lambda n: {"skill": n, "contexto": ""},
    )
    behav = _apply(
        cur_behav, rem_behav, add_behav, _normalize_behav,
        lambda n: {"competencia": n, "contexto": "", "trait_big_five": ""},
    )

    return ToolResult(
        llm_message=(
            f"Competências atualizadas: +{len(add_tech)}/-{len(rem_tech)} "
            f"técnicas, +{len(add_behav)}/-{len(rem_behav)} comportamentais. "
            f"Agora: {len(tech)} técnicas, {len(behav)} comportamentais."
        ),
        state_updates={
            "confirmed_technical_competencies": tech,
            "confirmed_behavioral_competencies": behav,
            "intake_competencies_suggested": True,
        },
    )


def _handle_set_salary(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Define a faixa salarial manualmente (quando o recrutador informa valores).

    Aceita salary_min / salary_max (inteiros em BRL) e currency opcional.
    Use quando o recrutador disser a faixa (ex.: '12 a 18k' → min=12000,
    max=18000). Converta 'k' em milhares ANTES de chamar.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    # Skip explícito: recrutador optou por seguir SEM divulgar a faixa.
    # Registra o skip (conta como salário tratado no gate de triagem) sem
    # exigir min/max.
    if tool_input.get("decline_to_disclose"):
        return ToolResult(
            llm_message=(
                "Registrado: a vaga seguirá sem divulgar a faixa salarial. "
                "Podemos avançar para as competências/triagem."
            ),
            state_updates={"salary_skipped": True},
        )

    smin = tool_input.get("salary_min")
    smax = tool_input.get("salary_max")
    currency = (tool_input.get("currency") or "BRL").strip().upper()[:8] or "BRL"

    def _coerce_int(v):
        if v is None:
            return None
        try:
            return int(round(float(v)))
        except (TypeError, ValueError):
            return "ERR"

    smin_i = _coerce_int(smin)
    smax_i = _coerce_int(smax)
    if smin_i == "ERR" or smax_i == "ERR":
        return ToolResult(
            llm_message="salary_min/salary_max devem ser números (em reais, ex.: 12000).",
            error=True,
        )
    if smin_i is None and smax_i is None:
        return ToolResult(
            llm_message="Forneça ao menos salary_min ou salary_max.", error=True
        )
    if smin_i is not None and smax_i is not None and smin_i > smax_i:
        return ToolResult(
            llm_message="salary_min não pode ser maior que salary_max.", error=True
        )

    updates: dict[str, Any] = {"salary_currency": currency, "salary_confirmed": True}
    if smin_i is not None:
        updates["salary_min"] = smin_i
    if smax_i is not None:
        updates["salary_max"] = smax_i
    if smin_i is not None and smax_i is not None:
        updates["salary_range"] = {"min": smin_i, "max": smax_i, "currency": currency}
    return ToolResult(
        llm_message=(
            f"Faixa salarial definida: {currency} {smin_i or '?'} – {currency} {smax_i or '?'}."
        ),
        state_updates=updates,
    )



def _handle_open_fullscreen_chat(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Navega o recrutador para o chat em tela cheia (/pt/oi ou /pt/chat).

    P0-E fix (2026-06-14): wizard nao tinha essa tool; LLM dizia 'vou expandir
    o painel' quando usuario pedia 'me leve para chat full'.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    return ToolResult(
        llm_message=(
            "Redirecionando para o chat em tela cheia. "
            "Confirme ao recrutador que ele sera levado para la."
        ),
        state_updates={"_navigate_to_fullscreen_chat": True},
    )


def _handle_navigate_to_jobs(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Sinaliza ao frontend para navegar até a página de vagas.

    Use quando o recrutador pedir 'me leve para vagas', 'abrir a vaga',
    'ver a tabela de vagas'. O frontend auto-navega quando o stage do wizard
    vira 'handoff' (ponte ui_action canonical).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    return ToolResult(
        llm_message=(
            "Navegação solicitada — o sistema vai abrir a página de vagas. "
            "Confirme ao recrutador que está levando-o para lá."
        ),
        state_updates={"_navigate_to_jobs": True},
    )



def _handle_open_panel(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Expande o painel lateral (ficha viva) no frontend."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    return ToolResult(
        llm_message=(
            "Painel lateral aberto -- confirme ao recrutador que a ficha viva "
            "esta visivel ao lado."
        ),
        state_updates={"panel_pref": "expanded"},
    )


def _handle_close_panel(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Minimiza o painel lateral para o dock acima do input."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    return ToolResult(
        llm_message=(
            "Painel minimizado para o card acima do campo de mensagem -- "
            "confirme ao recrutador que ele pode reabrir clicando no card."
        ),
        state_updates={"panel_pref": "docked"},
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
    except Exception as exc:  # noqa: BLE001  # REGRA-4-EXEMPT: status summary é informativo, falha retorna mensagem neutra ao LLM
        logger.warning("[WizardTools] status summary failed: %s", type(exc).__name__)
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
            "manager_name": {"type": "string", "description": "Nome do gestor/hiring manager da vaga."},
            "manager_email": {"type": "string", "description": "Email do gestor responsável."},
            "recruiter": {"type": "string", "description": "Nome do recrutador responsável pelo processo."},
            "recruiter_email": {"type": "string", "description": "Email do recrutador responsável."},
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

SET_SCREENING_DEADLINE = WizardTool(
    name="set_screening_deadline",
    description=(
        "Define o prazo de triagem (em horas) a partir da publicacao da vaga. "
        "Default da empresa: 48h. Presets comuns: 24, 48, 72, 96, 120, 168 (7 dias). "
        "O recrutador pode ajustar livremente entre 12h e 720h (30 dias)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "hours": {
                "type": "integer",
                "description": "Prazo em horas (12-720). Ex: 48 = 2 dias, 168 = 7 dias.",
            },
        },
        "required": ["hours"],
        "additionalProperties": False,
    },
    handler=_handle_set_screening_deadline,
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

UPDATE_COMPETENCIES = WizardTool(
    name="update_competencies",
    description=(
        "Adiciona ou remove competências específicas SEM precisar reenviar a "
        "lista inteira. Use quando o recrutador pedir para ADICIONAR ('inclua "
        "X', 'adicione Y') ou REMOVER ('tira Z', 'remove W') competências. "
        "Forneça apenas os deltas: add_technical, remove_technical, "
        "add_behavioral, remove_behavioral (listas de nomes). Para confirmar a "
        "lista inteira do zero, use confirm_competencies."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "add_technical": {"type": "array", "items": {"type": "string"}, "description": "Competências técnicas a adicionar."},
            "remove_technical": {"type": "array", "items": {"type": "string"}, "description": "Competências técnicas a remover (match por nome)."},
            "add_behavioral": {"type": "array", "items": {"type": "string"}, "description": "Competências comportamentais a adicionar."},
            "remove_behavioral": {"type": "array", "items": {"type": "string"}, "description": "Competências comportamentais a remover (match por nome)."},
        },
        "additionalProperties": False,
    },
    handler=_handle_update_competencies,
)

CONFIRM_RESPONSIBILITIES = WizardTool(
    name="confirm_responsibilities",
    description=(
        "Confirma as responsabilidades/atribuições da vaga (lista de frases). "
        "Peça as responsabilidades ao recrutador JUNTO com as competências. "
        "NÃO é obrigatório — se ele não tiver, sugira algumas com base no cargo "
        "e confirme; ou siga sem (a descrição gera responsabilidades e ele revisa). "
        "Se confirmadas, são usadas exatamente na descrição."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "responsibilities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Frases de responsabilidade da vaga.",
            },
        },
        "required": ["responsibilities"],
        "additionalProperties": False,
    },
    handler=_handle_confirm_responsibilities,
)

CONFIRM_LANGUAGES = WizardTool(
    name="confirm_languages",
    description=(
        "Registra os idiomas exigidos pela vaga e o nível (ex.: recrutador diz "
        "'inglês avançado' → language='Inglês', level='Avançado'). NÃO é "
        "obrigatório, mas capture sempre que um idioma for mencionado — senão o "
        "dado se perde. Níveis: Básico/Intermediário/Avançado/Fluente/Nativo."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "languages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "language": {"type": "string"},
                        "level": {"type": "string"},
                        "required": {"type": "boolean"},
                    },
                    "required": ["language"],
                },
            },
        },
        "required": ["languages"],
        "additionalProperties": False,
    },
    handler=_handle_confirm_languages,
)

APPROVE_JOB_DESCRIPTION = WizardTool(
    name="approve_job_description",
    description=(
        "Registra a aprovação da descrição da vaga pelo recrutador. Chame "
        "SOMENTE quando o recrutador aprovar explicitamente a JD gerada "
        "('aprovo', 'pode seguir', 'está ótima'). É pré-requisito para "
        "publicar — sem aprovar, publish_job não funciona."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_approve_job_description,
)

SET_SALARY = WizardTool(
    name="set_salary",
    description=(
        "Define a faixa salarial da vaga quando o recrutador informa os "
        "valores (ex.: 'entre 12 e 18 mil' → salary_min=12000, salary_max=18000). "
        "Converta 'k'/'mil' em milhares antes. Use também quando o recrutador "
        "ajustar a faixa sugerida pelo benchmark."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "salary_min": {"type": "number", "description": "Mínimo em reais (ex.: 12000)."},
            "salary_max": {"type": "number", "description": "Máximo em reais (ex.: 18000)."},
            "currency": {"type": "string", "description": "Moeda (default BRL)."},
            "decline_to_disclose": {"type": "boolean", "description": "true quando o recrutador opta por seguir SEM divulgar a faixa salarial (registra o skip; dispensa min/max)."},
        },
        "additionalProperties": False,
    },
    handler=_handle_set_salary,
)

NAVIGATE_TO_JOBS = WizardTool(
    name="navigate_to_jobs",
    description=(
        "Leva o recrutador para a página de vagas (abre a lista/tabela de "
        "vagas no frontend). Use quando ele pedir para 'ir para vagas', 'abrir "
        "a vaga', 'ver as vagas' ou após publicar, se ele quiser conferir."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_navigate_to_jobs,
)



OPEN_FULLSCREEN_CHAT = WizardTool(
    name="open_fullscreen_chat",
    description=(
        "Leva o recrutador para o chat em tela cheia (pagina dedicada de chat). "
        "Use quando ele pedir 'me leve para o chat full', 'abrir chat em tela "
        "cheia', 'quero ir pro chat completo', 'chat full', 'chat dedicado'."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_open_fullscreen_chat,
)


OPEN_PANEL = WizardTool(
    name="open_panel",
    description=(
        "Expande o painel lateral (ficha viva da vaga) no frontend. Use quando "
        "o recrutador pedir para 'abrir o painel', 'mostrar o painel', 'ver a "
        "ficha ao lado'."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_open_panel,
)

CLOSE_PANEL = WizardTool(
    name="close_panel",
    description=(
        "Minimiza o painel lateral para um card compacto acima do campo de "
        "mensagem. Use quando o recrutador pedir para 'fechar o painel', "
        "'esconder o painel', 'continuar so pelo chat'."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_close_panel,
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
    SET_SCREENING_DEADLINE,
    CONFIRM_COMPETENCIES,
    UPDATE_COMPETENCIES,
    CONFIRM_RESPONSIBILITIES,
    CONFIRM_LANGUAGES,
    APPROVE_JOB_DESCRIPTION,
    SET_SALARY,
    NAVIGATE_TO_JOBS,
    OPEN_FULLSCREEN_CHAT,
    OPEN_PANEL,
    CLOSE_PANEL,
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
