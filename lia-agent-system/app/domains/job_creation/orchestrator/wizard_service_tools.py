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
    confirmed_resp = state.get("confirmed_responsibilities") or None
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
                confirmed_responsibilities=confirmed_resp,
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
                confirmed_responsibilities=confirmed_resp,
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
                confirmed_responsibilities=confirmed_resp,
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
                "faixa salarial ao recrutador e registre com set_salary "
                "(ou confirme prosseguir sem faixa)."
            ),
        )
    # Fonte/confiança do benchmark — transparência para o recrutador (ele
    # perguntou 'qual a fonte?'). O benchmark combina dados internos da
    # empresa + mercado (MarketBenchmarkService).
    bench = result.get("salary_benchmark") or {}
    source = bench.get("source") or "mercado + base interna"
    confidence = bench.get("confidence")
    sample = bench.get("sample_size")
    src_parts = [f"fonte: {source}"]
    if confidence:
        src_parts.append(f"confiança: {confidence}")
    if sample:
        src_parts.append(f"amostra: {sample}")
    src_str = " (" + ", ".join(src_parts) + ")"
    return ToolResult(
        llm_message=(
            f"Faixa salarial de mercado para {state.get('parsed_title')}: "
            f"{currency} {smin:,.0f} – {currency} {smax:,.0f}{src_str}. "
            f"É uma referência — se o recrutador achar fora do mercado, ele "
            f"pode informar a faixa desejada (use set_salary)."
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


# ── generate_wsi_questions (F2+F3+F6 — metodologia WSI completa) ──────────


def _wsi_generate_core(
    state: dict, tool_input: dict, ctx: ToolContext, force_regen: bool = False
) -> ToolResult:
    """Gera as perguntas de triagem WSI (HITL #2), metodologia completa.

    Reusa os nós canônicos (DRY): bigfive_node (F2+F3 → trait_rankings Big Five)
    + wsi_questions_node (F6 → perguntas CBI com bloom_level/dreyfus_level/
    trait_ocean + fairness filter + skill classification).

    Frameworks aplicados pelo gerador canônico:
      - CBI (Competency-Based Interview): situações reais passadas.
      - Bloom: bloom_level 1-6, calibrado por senioridade.
      - Dreyfus: dreyfus_level 1-5, calibrado por senioridade.
      - Big Five: trait_ocean + afinidade trait↔competência (via trait_rankings).

    distribution (nº técnicas/comportamentais) vem das competências confirmadas
    ou da tabela canônica por senioridade (_get_question_distribution).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    if not state.get("jd_enriched"):
        return ToolResult(
            llm_message=(
                "Preciso da descrição gerada (enrich_job_description) antes de "
                "criar as perguntas de triagem."
            ),
            error=True,
        )

    node_state = dict(state)
    if ctx.company_id and not node_state.get("company_id"):
        node_state["company_id"] = ctx.company_id
    # Regenerar: força o nó a re-gerar mesmo com wsi_questions/questions_approved
    # já no state (senão ele short-circuita e devolve o pacote atual).
    if force_regen:
        node_state["wsi_regenerate_pending"] = True
        node_state["questions_approved"] = None

    seniority = (
        node_state.get("seniority_resolved")
        or node_state.get("parsed_seniority")
        or "pleno"
    )
    node_state["seniority_resolved"] = seniority

    # F2+F3 — Big Five profile + trait_rankings (metodologia completa, decisão
    # Paulo). Fail-soft: se falhar, segue sem ponderação Big Five (trait_rankings=[]).
    try:
        from app.domains.job_creation.nodes.bigfive import bigfive_node
        _bf = bigfive_node(node_state)
        for _k in ("bigfive_profile", "trait_rankings"):
            if _k in _bf:
                node_state[_k] = _bf[_k]
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning("[WizardServiceTools] bigfive failed (sem trait weighting): %s", exc)
        node_state.setdefault("trait_rankings", [])

    # F4+F5 — distribution: das competências confirmadas OU tabela canônica.
    _tech = node_state.get("confirmed_technical_competencies") or []
    _behav = node_state.get("confirmed_behavioral_competencies") or []
    if _tech or _behav:
        distribution = {"technical": len(_tech), "behavioral": len(_behav)}
    else:
        try:
            from app.domains.job_creation.graph import _get_question_distribution
            distribution = _get_question_distribution(
                node_state.get("screening_mode") or "compact", seniority
            )
        except Exception:  # noqa: BLE001
            distribution = {"technical": 5, "behavioral": 2}
    node_state["question_distribution"] = distribution

    # F6 — gera via nó canônico (inclui fairness filter + skill classification).
    try:
        from app.domains.job_creation.nodes.wsi_questions import wsi_questions_node
        out = wsi_questions_node(node_state)
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] wsi_questions_node failed: %s", exc)
        return ToolResult(
            llm_message=f"Não consegui gerar as perguntas de triagem agora ({exc}).",
            error=True,
        )

    if out.get("error"):
        return ToolResult(
            llm_message=f"Geração de perguntas bloqueada: {out.get('error')}.",
            error=True,
        )
    questions = out.get("wsi_questions") or []
    if not questions:
        return ToolResult(
            llm_message="O gerador não retornou perguntas. Tente novamente.",
            error=True,
        )

    n_tech = sum(1 for q in questions if (q.get("block") == "technical"))
    n_behav = len(questions) - n_tech
    used_fallback = bool(out.get("wsi_questions_used_fallback"))
    msg = (
        f"Geradas {len(questions)} perguntas de triagem WSI "
        f"({n_tech} técnicas + {n_behav} comportamentais), modo "
        f"{node_state.get('screening_mode') or 'compact'}. Metodologia: CBI "
        f"(situações reais), níveis Bloom/Dreyfus por senioridade e mapeamento "
        f"Big Five nas comportamentais."
    )
    if used_fallback:
        msg += (
            f" Atenção: usei perguntas de reserva (motivo: "
            f"{out.get('wsi_questions_fallback_reason')}) — recomende revisão extra."
        )
    msg += " Apresente um resumo e pergunte se o recrutador aprova ou quer ajustar."

    return ToolResult(
        llm_message=msg,
        state_updates={
            "wsi_questions": questions,
            "question_distribution": distribution,
            "trait_rankings": node_state.get("trait_rankings") or [],
            "bigfive_profile": node_state.get("bigfive_profile"),
            "seniority_resolved": seniority,
            "questions_approved": None,  # aguardando HITL #2
            "wsi_questions_used_fallback": used_fallback,
        },
    )


def _handle_generate_wsi_questions(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Gera as perguntas WSI (primeira vez)."""
    return _wsi_generate_core(state, tool_input, ctx, force_regen=False)


def _handle_regenerate_wsi_questions(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Regenera TODAS as perguntas WSI do zero (paridade com regenerate_all)."""
    if not state.get("wsi_questions"):
        # Sem perguntas ainda — gerar normalmente.
        return _wsi_generate_core(state, tool_input, ctx, force_regen=False)
    return _wsi_generate_core(state, tool_input, ctx, force_regen=True)


def _wsi_enriched_seniority_traits(state: dict):
    """Reconstrói EnrichedJobDescription + seniority + trait_rankings do state."""
    from app.domains.job_creation.schemas import EnrichedJobDescription
    jd = state.get("jd_enriched") or {}
    enriched = EnrichedJobDescription(**jd) if jd else None
    seniority = (
        state.get("seniority_resolved") or state.get("parsed_seniority") or "pleno"
    )
    trait_rankings = state.get("trait_rankings") or []
    return enriched, seniority, trait_rankings


def _valid_q_index(idx, total: int):
    """Índice 1-based válido (1..total). None se inválido."""
    try:
        i = int(idx)
    except (TypeError, ValueError):
        return None
    return i if 1 <= i <= total else None


def _handle_remove_wsi_question(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Remove uma pergunta WSI por índice (1-based). Determinístico, sem LLM."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    questions = list(state.get("wsi_questions") or [])
    if not questions:
        return ToolResult(llm_message="Não há perguntas para remover.", error=True)
    idx = _valid_q_index(tool_input.get("question_index"), len(questions))
    if idx is None:
        return ToolResult(
            llm_message=(
                f"Índice inválido. Informe um número de 1 a {len(questions)} "
                f"(question_index)."
            ),
            error=True,
        )
    new_questions = questions[: idx - 1] + questions[idx:]
    return ToolResult(
        llm_message=(
            f"Removida a pergunta {idx}. O pacote ficou com {len(new_questions)} "
            f"perguntas. Confirme se posso seguir ou ajuste mais."
        ),
        state_updates={"wsi_questions": new_questions, "questions_approved": None},
    )


def _handle_edit_wsi_question(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Edita UMA pergunta WSI por índice + instrução (geração cirúrgica CBI)."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    questions = list(state.get("wsi_questions") or [])
    idx = _valid_q_index(tool_input.get("question_index"), len(questions))
    if idx is None:
        return ToolResult(
            llm_message=f"Índice inválido. Informe de 1 a {len(questions)} (question_index).",
            error=True,
        )
    instruction = str(tool_input.get("instruction") or "").strip()
    if not instruction:
        return ToolResult(
            llm_message="Diga o que ajustar na pergunta (instruction).", error=True
        )
    enriched, seniority, traits = _wsi_enriched_seniority_traits(state)
    if enriched is None:
        return ToolResult(llm_message="Descrição da vaga indisponível.", error=True)
    target = questions[idx - 1]
    block = target.get("block") or "technical"
    try:
        from app.domains.job_creation.services.wsi_question_generator import (
            WSIQuestionGenerator, GeneratedQuestion,
        )
        gen = WSIQuestionGenerator()
        base = GeneratedQuestion(**target) if not isinstance(target, GeneratedQuestion) else target
        new_q = gen.generate_single_question(
            block=block, enriched=enriched, seniority=seniority,
            directive=instruction, base_question=base, trait_rankings=traits,
        )
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] edit_wsi failed: %s", exc)
        return ToolResult(llm_message=f"Não consegui editar a pergunta ({exc}).", error=True)
    if new_q is None:
        return ToolResult(llm_message="A edição não retornou pergunta. Tente reformular.", error=True)
    questions[idx - 1] = new_q.model_dump()
    return ToolResult(
        llm_message=(
            f"Pergunta {idx} reescrita conforme pedido. Apresente a nova versão e "
            f"confirme se está boa."
        ),
        state_updates={"wsi_questions": questions, "questions_approved": None},
    )


def _handle_add_wsi_question(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Adiciona UMA pergunta WSI (geração cirúrgica CBI) ao bloco indicado."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    if not state.get("wsi_questions"):
        return ToolResult(
            llm_message="Gere as perguntas primeiro (generate_wsi_questions).", error=True
        )
    block = str(tool_input.get("block") or "technical").strip().lower()
    if block not in ("technical", "behavioral"):
        return ToolResult(
            llm_message="block deve ser 'technical' ou 'behavioral'.", error=True
        )
    instruction = str(tool_input.get("instruction") or "").strip() or (
        f"Gere uma nova pergunta {block} complementar, distinta das existentes."
    )
    enriched, seniority, traits = _wsi_enriched_seniority_traits(state)
    if enriched is None:
        return ToolResult(llm_message="Descrição da vaga indisponível.", error=True)
    try:
        from app.domains.job_creation.services.wsi_question_generator import (
            WSIQuestionGenerator,
        )
        gen = WSIQuestionGenerator()
        new_q = gen.generate_single_question(
            block=block, enriched=enriched, seniority=seniority,
            directive=instruction, base_question=None, trait_rankings=traits,
        )
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] add_wsi failed: %s", exc)
        return ToolResult(llm_message=f"Não consegui adicionar a pergunta ({exc}).", error=True)
    if new_q is None:
        return ToolResult(llm_message="A geração não retornou pergunta. Tente reformular.", error=True)
    questions = list(state.get("wsi_questions") or []) + [new_q.model_dump()]
    return ToolResult(
        llm_message=(
            f"Adicionada uma pergunta {block}. O pacote agora tem {len(questions)} "
            f"perguntas. Confirme se posso seguir."
        ),
        state_updates={"wsi_questions": questions, "questions_approved": None},
    )


def _handle_approve_wsi_questions(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Registra a aprovação das perguntas WSI pelo recrutador (HITL #2)."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    if not state.get("wsi_questions"):
        return ToolResult(
            llm_message=(
                "Não há perguntas geradas para aprovar. Gere primeiro com "
                "generate_wsi_questions."
            ),
            error=True,
        )
    return ToolResult(
        llm_message=(
            "Perguntas de triagem aprovadas pelo recrutador. Serão salvas na "
            "vaga ao publicar."
        ),
        state_updates={"questions_approved": True},
    )


GENERATE_WSI_QUESTIONS = WizardTool(
    name="generate_wsi_questions",
    description=(
        "Gera as perguntas de triagem WSI da vaga (entrevista por competências). "
        "Use depois da descrição gerada e das competências confirmadas. Aplica a "
        "metodologia WSI completa: CBI (situações reais), níveis Bloom e Dreyfus "
        "por senioridade, e mapeamento Big Five nas comportamentais. O número de "
        "perguntas segue o modo de triagem (compacto/completo). Após gerar, "
        "apresente ao recrutador para aprovação."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_generate_wsi_questions,
)

REGENERATE_WSI_QUESTIONS = WizardTool(
    name="regenerate_wsi_questions",
    description=(
        "Regenera TODAS as perguntas de triagem WSI do zero (quando o recrutador "
        "não gostou do conjunto e quer um novo). Mantém modo/metodologia."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_regenerate_wsi_questions,
)

REMOVE_WSI_QUESTION = WizardTool(
    name="remove_wsi_question",
    description=(
        "Remove uma pergunta de triagem específica pelo número (question_index, "
        "1 = primeira). Use quando o recrutador pedir para tirar uma pergunta."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "question_index": {"type": "integer", "description": "Número da pergunta (1-based)."},
        },
        "required": ["question_index"],
        "additionalProperties": False,
    },
    handler=_handle_remove_wsi_question,
)

EDIT_WSI_QUESTION = WizardTool(
    name="edit_wsi_question",
    description=(
        "Reescreve UMA pergunta de triagem (por question_index, 1-based) seguindo "
        "uma instrução do recrutador (ex.: 'deixe mais específica sobre hedge'). "
        "Mantém a metodologia CBI."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "question_index": {"type": "integer", "description": "Número da pergunta (1-based)."},
            "instruction": {"type": "string", "description": "O que ajustar na pergunta."},
        },
        "required": ["question_index", "instruction"],
        "additionalProperties": False,
    },
    handler=_handle_edit_wsi_question,
)

ADD_WSI_QUESTION = WizardTool(
    name="add_wsi_question",
    description=(
        "Adiciona UMA nova pergunta de triagem ao bloco técnico ou comportamental "
        "(CBI). Use quando o recrutador pedir mais uma pergunta. Opcionalmente "
        "passe uma instrução do que ela deve avaliar."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "block": {"type": "string", "enum": ["technical", "behavioral"]},
            "instruction": {"type": "string", "description": "O que a pergunta deve avaliar (opcional)."},
        },
        "required": ["block"],
        "additionalProperties": False,
    },
    handler=_handle_add_wsi_question,
)

APPROVE_WSI_QUESTIONS = WizardTool(
    name="approve_wsi_questions",
    description=(
        "Registra a aprovação das perguntas de triagem WSI pelo recrutador "
        "(HITL #2). Chame SOMENTE quando ele aprovar explicitamente. As perguntas "
        "aprovadas são salvas na vaga ao publicar."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_approve_wsi_questions,
)


SERVICE_TOOLS: tuple[WizardTool, ...] = (
    SUGGEST_COMPETENCIES,
    ENRICH_JOB_DESCRIPTION,
    SUGGEST_SALARY,
    PUBLISH_JOB,
    GENERATE_WSI_QUESTIONS,
    REGENERATE_WSI_QUESTIONS,
    REMOVE_WSI_QUESTION,
    EDIT_WSI_QUESTION,
    ADD_WSI_QUESTION,
    APPROVE_WSI_QUESTIONS,
)
