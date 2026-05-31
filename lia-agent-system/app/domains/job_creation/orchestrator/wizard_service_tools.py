"""Wizard Orchestrator — service-backed tools (I/O via serviços canônicos).

Increment 2 do orquestrador (decisão Paulo 2026-05-31). Tools que fazem I/O
(LLM, DB) envolvendo os MESMOS serviços canônicos que os nós LangGraph usam —
DRY, single source of truth. Não reimplementam lógica de negócio.

Mantidas separadas das tools puras (:mod:`wizard_tools`) para que o módulo
puro continue I/O-free e testável sem mocks pesados.

## Invariantes

  - **Multi-tenancy**: ``company_id`` vem de ``ToolContext`` (JWT), passado aos
    serviços. NUNCA dos args da LLM (tools rejeitam via ``_reject_tenant_keys``).
  - **Fail-loud, nunca silent**: timeout/erro de LLM → ``ToolResult(error=True)``
    com motivo explícito realimentado ao modelo (CLAUDE.md REGRA 4). Quando há
    fallback determinístico canonical (JD enrichment), ele é usado mas a flag
    ``used_fallback`` é propagada ao state.
  - **Sync por contrato**: serviços async são chamados via
    ``run_coro_in_threadpool`` / ``ThreadPoolExecutor`` (graph/orchestrator
    nodes são sync).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext,
    ToolResult,
    WizardTool,
    _reject_tenant_keys,
)

logger = logging.getLogger(__name__)


_COMPETENCY_TIMEOUT_S = float(os.environ.get("LIA_ORCH_COMPETENCY_TIMEOUT_S", "12"))
_JD_TIMEOUT_S = float(os.environ.get("LIA_ORCH_JD_TIMEOUT_S", "60"))


# ── suggest_competencies ─────────────────────────────────────────────────


def _handle_suggest_competencies(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Sugere competências via CompetencyBenchmarkService (canonical, Fase 2).

    Lê título/senioridade/departamento/modo do state; ``company_id`` do ctx.
    Armazena as sugestões em ``suggested_competencies`` (NÃO confirma — o
    recrutador revisa e o LLM chama ``confirm_competencies`` depois).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    title = state.get("parsed_title") or ""
    if not title:
        return ToolResult(
            llm_message=(
                "Preciso do título do cargo antes de sugerir competências. "
                "Pergunte o título ao recrutador e registre com set_job_fields."
            ),
            error=True,
        )
    seniority = state.get("parsed_seniority")
    department = state.get("parsed_department")
    screening_mode = state.get("screening_mode") or "compact"

    try:
        from app.domains.job_creation.helpers.async_audit import (
            run_coro_in_threadpool,
        )

        async def _fetch() -> dict[str, Any]:
            from app.domains.analytics.services.competency_benchmark_service import (
                get_competency_benchmark_service,
            )
            svc = get_competency_benchmark_service()
            return await svc.suggest_competencies(
                title=title,
                seniority=seniority,
                department=department,
                screening_mode=screening_mode,
                company_id=ctx.company_id,
            )

        suggestion = run_coro_in_threadpool(_fetch, timeout=_COMPETENCY_TIMEOUT_S)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[WizardServiceTools] suggest_competencies failed: %s", exc)
        return ToolResult(
            llm_message=(
                f"Não consegui buscar sugestões de competências agora ({exc}). "
                f"Você pode pedir ao recrutador as competências principais e "
                f"registrar com confirm_competencies."
            ),
            error=True,
        )

    if not suggestion:
        return ToolResult(
            llm_message="O serviço não retornou sugestões. Peça as competências ao recrutador.",
            error=True,
        )

    technical = list(suggestion.get("technical") or [])
    behavioral = list(suggestion.get("behavioral") or [])
    tech_names = [c.get("skill") or c.get("name") or "" for c in technical]
    behav_names = [c.get("competencia") or c.get("name") or "" for c in behavioral]
    is_estimate = bool(suggestion.get("is_estimate"))

    summary = (
        f"Sugestões de competências para {title}"
        f"{' (' + seniority + ')' if seniority else ''}:\n"
        f"- Técnicas: {', '.join(n for n in tech_names if n) or '(nenhuma)'}\n"
        f"- Comportamentais: {', '.join(n for n in behav_names if n) or '(nenhuma)'}"
    )
    if is_estimate:
        summary += "\n(Estimativa — confiança baixa; vale revisar com o recrutador.)"
    summary += (
        "\nApresente ao recrutador para revisão. Ao confirmar/ajustar, chame "
        "confirm_competencies."
    )

    return ToolResult(
        llm_message=summary,
        state_updates={
            "suggested_competencies": {
                "technical": technical,
                "behavioral": behavioral,
            },
        },
    )


# ── enrich_job_description ───────────────────────────────────────────────


def _handle_enrich_job_description(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Gera a descrição enriquecida via JdEnrichmentService (canonical, F1/Fase 4).

    Usa as competências CONFIRMADas (Fase 4 inversão) quando presentes, para a
    JD ser consistente com elas. Lê ``jd_raw`` do state (ou ``raw_input``).
    Aplica timeout + fallback determinístico canonical (nunca silent: propaga
    ``jd_enrichment_used_fallback``).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    title = state.get("parsed_title") or ""
    if not title:
        return ToolResult(
            llm_message=(
                "Preciso ao menos do título do cargo para gerar a descrição. "
                "Registre com set_job_fields primeiro."
            ),
            error=True,
        )

    jd_raw = (
        state.get("jd_raw")
        or state.get("raw_input")
        or tool_input.get("jd_raw")
        or ""
    )
    seniority = state.get("parsed_seniority") or ""
    department = state.get("parsed_department") or ""
    confirmed_tech = state.get("confirmed_technical_competencies") or None
    confirmed_behav = state.get("confirmed_behavioral_competencies") or None
    screening_mode = state.get("screening_mode")

    import concurrent.futures as _cf

    try:
        from app.domains.job_creation.internal.services import _get_jd_service
        from app.domains.job_creation.services.jd_enrichment import (
            calculate_quality_score as _calc_q,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[WizardServiceTools] jd service import failed: %s", exc)
        return ToolResult(
            llm_message=f"Serviço de descrição indisponível agora ({exc}).",
            error=True,
        )

    service = _get_jd_service()
    used_fallback = False
    fallback_reason: Optional[str] = None

    try:
        with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
            _fut = _ex.submit(
                service.enrich,
                jd_raw=jd_raw,
                title=title,
                seniority=seniority,
                department=department,
                confirmed_technical=confirmed_tech,
                confirmed_behavioral=confirmed_behav,
                screening_mode=screening_mode,
            )
            enriched_obj, quality_score, warnings = _fut.result(timeout=_JD_TIMEOUT_S)
    except _cf.TimeoutError:
        logger.warning("[WizardServiceTools] JD enrich timeout — fallback")
        try:
            enriched_obj = service._fallback_enrichment(
                jd_raw, title, seniority,
                confirmed_technical=confirmed_tech,
                confirmed_behavioral=confirmed_behav,
            )
            quality_score, warnings = _calc_q(enriched_obj)
            used_fallback = True
            fallback_reason = "timeout"
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                llm_message=f"A geração da descrição expirou e o fallback falhou ({exc}).",
                error=True,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[WizardServiceTools] JD enrich failed (%s) — fallback", exc)
        try:
            enriched_obj = service._fallback_enrichment(
                jd_raw, title, seniority,
                confirmed_technical=confirmed_tech,
                confirmed_behavioral=confirmed_behav,
            )
            quality_score, warnings = _calc_q(enriched_obj)
            used_fallback = True
            fallback_reason = type(exc).__name__
        except Exception as exc2:  # noqa: BLE001
            return ToolResult(
                llm_message=f"Não consegui gerar a descrição agora ({exc2}).",
                error=True,
            )

    try:
        enriched_dict = enriched_obj.model_dump()
    except Exception:  # noqa: BLE001 — defensive
        enriched_dict = dict(enriched_obj) if isinstance(enriched_obj, dict) else {}

    msg = (
        f"Descrição gerada para {title} (qualidade {quality_score:.0f}/100)."
    )
    if used_fallback:
        msg += (
            f" Atenção: usei o gerador de reserva (motivo: {fallback_reason}) — "
            f"recomende ao recrutador uma revisão extra antes de aprovar."
        )
    msg += " Apresente um resumo e pergunte se ele aprova ou quer ajustar."

    return ToolResult(
        llm_message=msg,
        state_updates={
            "jd_enriched": enriched_dict,
            "jd_quality_score": quality_score,
            "jd_quality_warnings": list(warnings or []),
            "jd_enrichment_used_fallback": used_fallback,
            "jd_enrichment_fallback_reason": fallback_reason,
            "jd_approved": None,  # gerada → aguardando aprovação
        },
    )


# ── Tool defs ────────────────────────────────────────────────────────────


SUGGEST_COMPETENCIES = WizardTool(
    name="suggest_competencies",
    description=(
        "Busca sugestões de competências técnicas e comportamentais para a vaga, "
        "dimensionadas pelo modo de triagem, usando o benchmark da plataforma. "
        "Use DEPOIS de ter ao menos o título (idealmente título + senioridade). "
        "As sugestões NÃO são confirmadas automaticamente — apresente ao "
        "recrutador e chame confirm_competencies quando ele aprovar/ajustar."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_suggest_competencies,
)

ENRICH_JOB_DESCRIPTION = WizardTool(
    name="enrich_job_description",
    description=(
        "Gera a descrição de vaga (JD) enriquecida e completa a partir dos "
        "dados coletados e das competências CONFIRMADAS. Use somente depois de "
        "ter título, senioridade e competências confirmadas (confirm_competencies). "
        "A descrição gerada fica aguardando aprovação do recrutador."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "jd_raw": {
                "type": "string",
                "description": "Texto bruto opcional fornecido pelo recrutador como base.",
            },
        },
        "additionalProperties": False,
    },
    handler=_handle_enrich_job_description,
)


# ── suggest_salary ───────────────────────────────────────────────────────


# Chaves de salário extraídas do output do salary_node (evita poluir o state
# do orquestrador com current_stage/stage_history/ws_stage_payload do nó).
_SALARY_RESULT_KEYS = (
    "salary_min", "salary_max", "salary_currency", "salary_benchmark",
)


def _handle_suggest_salary(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Sugere faixa salarial via benchmark (interno + mercado), DRY pelo salary_node.

    Reusa o ``salary_node`` canonical (benchmark interno via JobInsightsService +
    mercado via MarketBenchmarkService, combine 70/30). Extrai apenas os campos
    de salário do output (não importa current_stage/payload do nó). company_id
    vem do state (workspace_id/company_id), que o caller populou do JWT.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    if not (state.get("parsed_title")):
        return ToolResult(
            llm_message="Preciso do título do cargo para buscar a faixa salarial.",
            error=True,
        )

    try:
        from app.domains.job_creation.nodes.salary import salary_node
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_message=f"Serviço de salário indisponível agora ({exc}).",
            error=True,
        )

    # Garante company_id no state para o benchmark interno (multi-tenancy).
    node_state = dict(state)
    if ctx.company_id and not node_state.get("company_id"):
        node_state["company_id"] = ctx.company_id

    try:
        result = salary_node(node_state)
    except Exception as exc:  # noqa: BLE001 — fail-loud, nunca silent
        logger.warning("[WizardServiceTools] salary_node failed: %s", exc)
        return ToolResult(
            llm_message=(
                f"Não consegui buscar o benchmark salarial agora ({exc}). "
                f"Você pode pedir a faixa ao recrutador e registrar depois."
            ),
            error=True,
        )

    updates = {k: result.get(k) for k in _SALARY_RESULT_KEYS if result.get(k) is not None}
    smin = updates.get("salary_min")
    smax = updates.get("salary_max")
    currency = updates.get("salary_currency", "BRL")
    if smin is None and smax is None:
        return ToolResult(
            llm_message=(
                "Não há dados de mercado disponíveis para esse cargo. Peça a "
                "faixa salarial ao recrutador e registre com set_job_fields "
                "(ou confirme prosseguir sem faixa)."
            ),
        )
    return ToolResult(
        llm_message=(
            f"Faixa salarial de mercado para {state.get('parsed_title')}: "
            f"{currency} {smin:,.0f} – {currency} {smax:,.0f}. Apresente ao "
            f"recrutador e pergunte se ele aceita ou quer ajustar."
        ).replace(",", "."),
        state_updates=updates,
    )


# ── publish_job ──────────────────────────────────────────────────────────


def _handle_publish_job(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Publica a vaga (AÇÃO IRREVERSÍVEL) — DRY pelo publish_node canonical.

    Gate de confirmação: exige ``confirm=true`` no tool_input. Sem confirmação
    explícita, NÃO publica — instrui o LLM a obter o "sim" do recrutador. Com
    confirmação, seta ``policy_confirmed_publish=True`` (destrava o PolicyGate
    HITL do nó) e chama ``publish_node``, que cria a vaga + screening config +
    publica + gera share link + audit (SOX). Pré-requisito: JD gerada e aprovada.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    if not state.get("jd_enriched"):
        return ToolResult(
            llm_message=(
                "Não posso publicar sem uma descrição gerada. Gere a JD "
                "(enrich_job_description) e obtenha a aprovação do recrutador antes."
            ),
            error=True,
        )
    if state.get("jd_approved") is not True:
        return ToolResult(
            llm_message=(
                "A descrição ainda não foi aprovada pelo recrutador. Confirme a "
                "aprovação da JD antes de publicar."
            ),
            error=True,
        )

    confirmed = bool(tool_input.get("confirm"))
    if not confirmed:
        title = state.get("parsed_title") or "a vaga"
        return ToolResult(
            llm_message=(
                f"Publicar é uma ação irreversível. Confirme explicitamente com "
                f"o recrutador que ele quer publicar '{title}' agora. Quando ele "
                f"confirmar, chame publish_job novamente com confirm=true."
            ),
        )

    try:
        from app.domains.job_creation.nodes.publish import publish_node
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            llm_message=f"Serviço de publicação indisponível agora ({exc}).",
            error=True,
        )

    node_state = dict(state)
    if ctx.company_id and not node_state.get("company_id"):
        node_state["company_id"] = ctx.company_id
    # Destrava o PolicyGate HITL do publish_node (confirmação já obtida acima).
    node_state["policy_confirmed_publish"] = True

    try:
        result = publish_node(node_state)
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] publish_node failed: %s", exc)
        return ToolResult(
            llm_message=f"Falha ao publicar a vaga ({exc}). Tente novamente.",
            error=True,
        )

    error = result.get("error")
    job_id = result.get("job_id")
    share_link = result.get("share_link")

    if error or not job_id:
        return ToolResult(
            llm_message=(
                f"A publicação não foi concluída: {error or 'sem job_id retornado'}. "
                f"Informe o recrutador e ofereça tentar de novo."
            ),
            state_updates={
                "error": error,
                "policy_confirmed_publish": True,
            },
            error=True,
        )

    share_part = f" Link de compartilhamento: {share_link}." if share_link else ""
    return ToolResult(
        llm_message=(
            f"Vaga publicada com sucesso! ID {job_id}.{share_part} "
            f"Avise o recrutador e ofereça os próximos passos (ver candidatos, etc.)."
        ),
        state_updates={
            "job_id": job_id,
            "job_uid": result.get("job_uid"),
            "share_link": share_link,
            "current_stage": "done",
            "policy_confirmed_publish": True,
            "error": None,
        },
    )


SUGGEST_SALARY = WizardTool(
    name="suggest_salary",
    description=(
        "Busca a faixa salarial de mercado para a vaga (benchmark interno da "
        "empresa + mercado). Use quando o recrutador perguntar sobre salário ou "
        "ao montar a oferta. Requer ao menos o título. Apresente a faixa e deixe "
        "o recrutador aceitar ou ajustar (set_job_fields não cobre salário — a "
        "faixa fica no state do benchmark)."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_suggest_salary,
)

PUBLISH_JOB = WizardTool(
    name="publish_job",
    description=(
        "Publica a vaga. AÇÃO IRREVERSÍVEL — só chame após o recrutador APROVAR "
        "a descrição e CONFIRMAR explicitamente que quer publicar. Passe "
        "confirm=true apenas quando tiver a confirmação explícita do recrutador "
        "no turno. Sem confirm=true, a tool apenas orienta a obter a confirmação."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "confirm": {
                "type": "boolean",
                "description": "True somente com confirmação explícita do recrutador.",
            },
        },
        "additionalProperties": False,
    },
    handler=_handle_publish_job,
)


SERVICE_TOOLS: tuple[WizardTool, ...] = (
    SUGGEST_COMPETENCIES,
    ENRICH_JOB_DESCRIPTION,
    SUGGEST_SALARY,
    PUBLISH_JOB,
)
