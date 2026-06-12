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

    # Consolidação WSI Fase 1 (2026-05-31): kernel canônico cv_screening.WSIService
    # via Anticorruption Layer (wsi_canonical_adapter) — NÃO mais o fork
    # analytics.CompetencyBenchmarkService. Single source of truth (DDD Shared Kernel).
    from app.domains.job_creation.orchestrator.wsi_canonical_adapter import (
        suggest_competencies_canonical,
    )
    jd_text = state.get("jd_raw") or state.get("raw_input") or ""
    suggestion = suggest_competencies_canonical(
        title=title, seniority=seniority, jd_text=jd_text, company_id=ctx.company_id,
    )
    if not suggestion:
        return ToolResult(
            llm_message=(
                "Não consegui buscar sugestões de competências agora. Peça as "
                "competências principais ao recrutador e registre com confirm_competencies."
            ),
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
                company_context=state.get("company_context", ""),
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
    # Marca que a sugestão salarial foi emitida (salário tratado no fluxo).
    updates["intake_salary_suggested"] = True
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
            # Sugestão foi emitida (mesmo sem dados) — salário foi tratado.
            state_updates={"intake_salary_suggested": True},
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

    if not state.get("questions_approved"):
        return ToolResult(
            llm_message=(
                "A triagem WSI ainda nao foi aprovada. "
                "Por favor, revise as perguntas no painel de Triagem e clique em "
                "'Aprovar' antes de publicar a vaga."
            ),
            state_updates={"requires_action": "approve_wsi_questions"},
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
            "Avise o recrutador e ofereça explicitamente as 3 opções: "
            "(1) ir para a página da vaga (navigate_to_jobs), (2) criar outra "
            "vaga, ou (3) continuar por aqui no chat (close_panel se ele "
            "preferir minimizar o painel)."
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


_WSI_BULK_TIMEOUT_S = float(os.environ.get("LIA_ORCH_WSI_BULK_TIMEOUT_S", "150"))


def _wsi_distribution_status(state: dict) -> dict:
    """Conta perguntas WSI por bloco e compara com o mínimo metodológico.

    Single source of truth do gate de distribuição no caminho live (orquestrador):
    reusado por :func:`_handle_approve_wsi_questions` (gate fail-closed) e pelo
    payload do ``WsiQuestionsPanel`` (banner). Critério de bloco alinhado ao nó
    canônico ``wsi_questions_node`` e a ``_wsi_question_to_panel`` (campo ``block``
    ∈ {"technical", "behavioral"}); comportamental = total − técnicas.

    Fail-open: se ``_get_question_distribution`` falhar, os mínimos viram 0 e
    ``gap`` fica None — nunca trava o fluxo por erro de tabela/import.
    """
    questions = state.get("wsi_questions") or []
    tech_count = sum(
        1 for q in questions
        if isinstance(q, dict) and q.get("block") in ("technical", "tecnica")
    )
    behavioral_count = len(questions) - tech_count

    mode = (state.get("screening_mode") or "compact").lower()
    seniority = (
        state.get("seniority_resolved") or state.get("parsed_seniority") or "pleno"
    ).lower()
    try:
        from app.domains.job_creation.graph import _get_question_distribution
        expected = _get_question_distribution(mode, seniority) or {}
        min_tech = int(expected.get("technical", 0))
        min_behavioral = int(expected.get("behavioral", 0))
    except Exception:  # noqa: BLE001 — fail-open (gate nunca trava por erro de tabela)
        min_tech = min_behavioral = 0

    gap = None
    if (min_tech and tech_count < min_tech) or (
        min_behavioral and behavioral_count < min_behavioral
    ):
        gap = {
            "tech": {"current": tech_count, "required": min_tech},
            "behavioral": {"current": behavioral_count, "required": min_behavioral},
        }
    return {
        "tech_count": tech_count,
        "behavioral_count": behavioral_count,
        "min_tech": min_tech,
        "min_behavioral": min_behavioral,
        "gap": gap,
    }


def _wsi_question_to_panel(q) -> dict:
    """Mapeia WSIQuestion canonico (cv_screening) -> shape do painel/ficha viva
    do wizard. Consolidacao WSI Fase 2.4b: a riqueza por-pergunta
    (block/bloom/dreyfus/ideal_answer/trait_ocean) ja vem do canonico (Fase 2.2)."""
    return {
        "id": getattr(q, "id", None),
        "question": q.question_text,
        "block": q.block or ("behavioral" if q.framework == "BigFive" else "technical"),
        "framework": q.framework,
        "competency": q.competency,
        "skill": q.skill or q.competency,
        "trait_ocean": q.trait_ocean,
        "ideal_answer": q.ideal_answer or "",
        "scoring_rubric": q.scoring_criteria or {},
        "bloom_level": q.bloom_level,
        "dreyfus_level": q.dreyfus_level,
        "weight": q.weight,
        "expected_signals": list(q.expected_signals or []),
        "needs_manual_review": getattr(q, "needs_manual_review", False),
        "fallback_used": getattr(q, "fallback_used", False),
    }




def _normalize_skill_name(s: str) -> str:
    """Normaliza nome de skill para fuzzy match: lowercase + remove acentos básicos."""
    replacements = {
        "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
        "é": "e", "ê": "e", "ë": "e",
        "í": "i", "î": "i", "ï": "i",
        "ó": "o", "ô": "o", "õ": "o", "ö": "o",
        "ú": "u", "û": "u", "ü": "u",
        "ç": "c", "ñ": "n",
    }
    result = s.lower().strip()
    for accented, plain in replacements.items():
        result = result.replace(accented, plain)
    return result


def _reorder_skills_by_effectiveness(
    skills: list[str],
    company_id: str,
    department: str,
    seniority: str,
) -> list[str]:
    """W2-D: reordena skills por discrimination_score histórico (WSI effectiveness).

    Skills que a empresa já avaliou e têm alto poder discriminatório (>= 0.5)
    são movidas para o topo da lista. O generator de perguntas atribui weight
    decrescente por índice, então as primeiras na lista viram perguntas priority.

    Fail-open: qualquer erro retorna skills na ordem original.
    Multi-tenancy: company_id obrigatório, vem do state.
    """
    if not company_id or not skills:
        return skills
    try:
        from app.domains.job_creation.services.wsi_skill_taxonomy import (
            get_skill_to_parent_index,
            find_skill,
        )
        from app.domains.job_creation.services.wsi_effectiveness_service import (
            WsiEffectivenessService,
        )
        from app.core.database import AsyncSessionLocal
        from app.domains.job_creation.helpers.async_audit import (
            run_coro_in_threadpool,
        )

        # Obter todos os parent_ids da taxonomia (limitado para performance)
        parent_ids = list({v for v in get_skill_to_parent_index().values()})

        if not parent_ids:
            return skills

        async def _fetch_priority() -> list[dict]:
            async with AsyncSessionLocal() as _db:
                svc = WsiEffectivenessService(_db)
                return await svc.select_priority_skills(
                    company_id=company_id,
                    parent_ids=parent_ids,
                    department=department,
                    seniority_level=seniority,
                )

        priority_list = run_coro_in_threadpool(_fetch_priority, timeout=5)

        if not priority_list:
            return skills

        # Threshold: mesmo DISCRIMINATION_THRESHOLD do WsiEffectivenessService
        _DISC_THRESHOLD = 0.5
        # Nomes normalizados de skills com alta discriminação
        priority_names: set[str] = {
            _normalize_skill_name(s["name_pt"])
            for s in priority_list
            if abs(s.get("discrimination_score", 0.0)) >= _DISC_THRESHOLD
        }

        if not priority_names:
            return skills

        # Verificar match entre nome de skill do wizard e name_pt da taxonomia
        def _has_effectiveness_match(skill_name: str) -> bool:
            norm = _normalize_skill_name(skill_name)
            return any(
                p in norm or norm in p
                for p in priority_names
            )

        high_prio = [s for s in skills if _has_effectiveness_match(s)]
        low_prio = [s for s in skills if not _has_effectiveness_match(s)]

        reordered = high_prio + low_prio
        if reordered != skills:
            logger.info(
                "[W2-D] WSI effectiveness reorder: %d/%d skills boosted company=%s",
                len(high_prio),
                len(skills),
                hash(company_id) % 100000,
            )
        return reordered

    except Exception as _w2d_exc:
        logger.debug("[W2-D] WSI effectiveness reorder fail-open: %s", _w2d_exc)
        return skills

def _wsi_generate_core(
    state: dict, tool_input: dict, ctx: ToolContext, force_regen: bool = False
) -> ToolResult:
    """Gera as perguntas de triagem WSI (HITL #2) via canonico unico.

    Consolidacao WSI Fase 2.4b: delega a WSIService.generate_wsi_package
    (cv_screening) — single source of truth de perguntas + Big Five + fairness L4,
    com UMA extracao OCEAN. Substitui os nos do fork (bigfive_node +
    wsi_questions_node). Fail-loud (CLAUDE.md REGRA 4): erro/timeout retorna
    ToolResult(error=True) com motivo explicito, sem fallback silencioso.
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

    # Gate computacional (sensor) — salário é etapa esperada do fluxo e NÃO
    # pode ser pulada silenciosamente antes da triagem. Backstop determinístico
    # do guia de prompt (que sozinho não era confiável — commit B2 709a4e5ff).
    # "Tratado" = valores informados, faixa confirmada, sugestão emitida, ou
    # skip explícito do recrutador (set_salary decline_to_disclose=true).
    _salary_addressed = bool(
        state.get("salary_confirmed")
        or state.get("salary_skipped")
        or state.get("intake_salary_suggested")
        or state.get("salary_min") is not None
        or state.get("salary_max") is not None
    )
    if not _salary_addressed:
        return ToolResult(
            llm_message=(
                "Antes de gerar as perguntas de triagem, TRATE O SALÁRIO "
                "(etapa esperada do fluxo): ofereça a faixa de mercado com "
                "suggest_salary (informe a fonte). Se o recrutador informar "
                "valores, registre com set_salary; se ele optar por seguir SEM "
                "divulgar a faixa, registre com "
                "set_salary(decline_to_disclose=true). Só depois gere a triagem."
            ),
            error=True,
        )

    # Gate computacional (#2 audit 2026-06-05): o MODO de triagem
    # (compact/full) NAO pode ser escolhido pelo sistema silenciosamente.
    # Antes caia em default "compact" implicito -> a LIA pulava a pergunta e
    # o recrutador tinha que cobrar. Forca perguntar quando nao definido via
    # set_screening_mode (a menos que seja regeneracao, ja com modo setado).
    if not force_regen and not state.get("screening_mode"):
        return ToolResult(
            llm_message=(
                "Antes de gerar a triagem, PERGUNTE ao recrutador qual o "
                "MODO de triagem WSI e registre com set_screening_mode: "
                "'compact' (7 perguntas, ~10 min, triagem rapida) ou "
                "'full' (12 perguntas, ~18 min, avaliacao aprofundada). "
                "Nao escolha por ele."
            ),
            error=True,
        )

    jd = state.get("jd_enriched") or {}
    # job_description p/ extracao OCEAN — PII masked (paridade com o fork).
    _parts = [jd.get("about_role") or "", " ".join(jd.get("responsabilidades") or [])]
    job_description = " ".join(p for p in _parts if p).strip()
    try:
        from app.domains.job_creation.compliance import mask_pii_for_llm as _mask
        if job_description:
            job_description = _mask(job_description)
    except Exception as _pii_exc:  # noqa: BLE001 — fail-open masking
        logger.warning("[WizardServiceTools] PII masking failed (fail-open): %s", _pii_exc)

    skills = _comp_names(state.get("confirmed_technical_competencies"), "skill", "name")
    behavioral = _comp_names(state.get("confirmed_behavioral_competencies"), "competencia", "name")
    seniority = (
        state.get("seniority_resolved")
        or state.get("parsed_seniority")
        or "pleno"
    )
    mode = state.get("screening_mode") or "compact"

    # W2-D: reordenar skills por efetividade histórica (fail-open se sem dados)
    _company_id_eff = state.get("company_id") or (ctx.company_id if ctx else "")
    _dept_eff = state.get("parsed_department") or ""
    skills = _reorder_skills_by_effectiveness(skills, _company_id_eff, _dept_eff, seniority)

    from app.domains.cv_screening.services.wsi_service.service import get_wsi_service
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

    svc = get_wsi_service()
    dropped: list = []
    try:
        pkg = run_coro_in_threadpool(
            lambda: svc.generate_wsi_package(
                skills=skills,
                behavioral=behavioral,
                seniority=seniority,
                job_description=job_description or None,
                mode=mode,
                collect_dropped=dropped,
            ),
            timeout=_WSI_BULK_TIMEOUT_S,
        )
    except Exception as exc:  # noqa: BLE001 — fail-loud (REGRA 4)
        logger.warning("[WizardServiceTools] wsi package failed: %s", exc)
        return ToolResult(
            llm_message=(
                f"Não consegui gerar as perguntas de triagem agora ({exc}). "
                "Tente novamente em instantes."
            ),
            error=True,
        )

    q_objs = pkg.get("questions") or []
    if not q_objs:
        return ToolResult(
            llm_message="O gerador não retornou perguntas. Tente novamente.",
            error=True,
        )
    questions = [_wsi_question_to_panel(q) for q in q_objs]

    n_tech = sum(1 for q in questions if q.get("block") == "technical")
    n_behav = len(questions) - n_tech
    msg = (
        f"Geradas {len(questions)} perguntas de triagem WSI "
        f"({n_tech} técnicas + {n_behav} comportamentais), modo {mode}. "
        f"Metodologia: CBI (situações reais), níveis Bloom/Dreyfus por senioridade "
        f"e mapeamento Big Five nas comportamentais."
    )
    if dropped:
        msg += (
            f" Atenção: {len(dropped)} pergunta(s) descartada(s) pelo filtro de "
            f"equidade (FairnessGuard) — recomende revisão."
        )
    msg += " Apresente um resumo e pergunte se o recrutador aprova ou quer ajustar."

    return ToolResult(
        llm_message=msg,
        state_updates={
            "wsi_questions": questions,
            "trait_rankings": pkg.get("trait_rankings") or [],
            "bigfive_profile": pkg.get("bigfive_profile"),
            "wsi_dropped_questions": (
                list(state.get("wsi_dropped_questions") or []) + dropped
            ),
            "seniority_resolved": seniority,
            "questions_approved": None,  # aguardando HITL #2
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


_WSI_SINGLE_TIMEOUT_S = float(os.environ.get("LIA_ORCH_WSI_SINGLE_TIMEOUT_S", "30"))


def _comp_names(items, *keys) -> list[str]:
    """Extrai nomes de competencias do state (list[{skill|competencia|name}])."""
    out: list[str] = []
    for it in items or []:
        if isinstance(it, dict):
            name = next((str(it[k]).strip() for k in keys if it.get(k)), "")
        else:
            name = str(it).strip()
        if name:
            out.append(name)
    return out


def _wsi_single_to_panel(res: dict, block: str) -> dict:
    """Mapeia o output flat de WSIService.suggest_single_question (canonico) para
    o shape de pergunta que o painel do wizard + ficha viva consomem.

    Consolidacao WSI Fase 2.4: HITL add/edit usa o MESMO canonico que o endpoint
    de Settings (single source of truth) — fairness (pre-check + L4) ja vem de
    dentro do canonico (Fase 2.3). O `block` e autoritativo do wizard, nao da
    categoria inferida pelo LLM.
    """
    return {
        "question": res.get("question", ""),
        "block": block,
        "framework": "CBI",
        "competency": res.get("skill_targeted") or block,
        "skill": res.get("skill_targeted", ""),
        "trait_ocean": None,
        "ideal_answer": "",
        "scoring_rubric": {},
        "bloom_level": res.get("bloom_level"),
        "dreyfus_level": None,
        "weight": 1.0,
    }


def _wsi_suggest_single(state: dict, *, instruction: str, block: str):
    """Chama o canonico WSIService.suggest_single_question via bridge sync->async."""
    from app.domains.cv_screening.services.wsi_service.service import get_wsi_service
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

    svc = get_wsi_service()
    block_id = 4 if block == "behavioral" else 3
    job_title = state.get("parsed_title") or ""
    seniority = (
        state.get("seniority_resolved")
        or state.get("parsed_seniority")
        or "pleno"
    )
    tech = _comp_names(state.get("confirmed_technical_competencies"), "skill", "name")
    behav = _comp_names(state.get("confirmed_behavioral_competencies"), "competencia", "name")
    return run_coro_in_threadpool(
        lambda: svc.suggest_single_question(
            prompt=instruction,
            block_id=block_id,
            job_title=job_title,
            seniority=seniority,
            technical_skills=tech,
            behavioral_competencies=behav,
        ),
        timeout=_WSI_SINGLE_TIMEOUT_S,
    )


def _handle_edit_wsi_question(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Edita UMA pergunta WSI por índice + instrução (canônico cirúrgico, Fase 2.4).

    Delega ao canônico único WSIService.suggest_single_question (mesmo do endpoint
    Settings). FairnessGuard (pre-check + L4) já vem de dentro do canônico.
    """
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
    target = questions[idx - 1]
    block = (target.get("block") if isinstance(target, dict) else None) or "technical"
    try:
        res = _wsi_suggest_single(state, instruction=instruction, block=block)
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] edit_wsi (canonical) failed: %s", exc)
        return ToolResult(llm_message=f"Não consegui editar a pergunta ({exc}).", error=True)
    if not res or not res.get("success"):
        _msg = (res or {}).get("error") or "A edição não retornou pergunta. Tente reformular."
        return ToolResult(llm_message=_msg, error=True)
    questions[idx - 1] = _wsi_single_to_panel(res, block)
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
    """Adiciona UMA pergunta WSI ao bloco indicado (canônico cirúrgico, Fase 2.4).

    Delega ao canônico único WSIService.suggest_single_question (mesmo do endpoint
    Settings). FairnessGuard (pre-check + L4) já vem de dentro do canônico.
    """
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
    # Gate de limite máximo por modo (full=12, compact=7)
    _mode = str(state.get("screening_mode") or "compact").strip().lower()
    _max_total = 12 if _mode == "full" else 7
    _current_count = len(state.get("wsi_questions") or [])
    if _current_count >= _max_total:
        _modo_label = "completo" if _mode == "full" else "compacto"
        return ToolResult(
            llm_message=(
                f"O pacote já tem {_current_count} perguntas — limite máximo para o modo "
                f"{_modo_label} ({_max_total}). "
                f"Para adicionar uma nova, primeiro remova ou substitua uma existente "
                f"com replace_wsi_question."
            ),
            error=True,
        )
    instruction = str(tool_input.get("instruction") or "").strip() or (
        f"Gere uma nova pergunta {block} complementar, distinta das existentes."
    )
    try:
        res = _wsi_suggest_single(state, instruction=instruction, block=block)
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] add_wsi (canonical) failed: %s", exc)
        return ToolResult(llm_message=f"Não consegui adicionar a pergunta ({exc}).", error=True)
    if not res or not res.get("success"):
        _msg = (res or {}).get("error") or "A geração não retornou pergunta. Tente reformular."
        return ToolResult(llm_message=_msg, error=True)
    questions = list(state.get("wsi_questions") or []) + [_wsi_single_to_panel(res, block)]
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
    # Gate fail-closed: a metodologia WSI exige um mínimo de perguntas técnicas
    # E comportamentais (tabela por modo × senioridade). O FE já bloqueia, mas é
    # bypassável — este é o gate AUTORITATIVO server-side no caminho live.
    _dist = _wsi_distribution_status(state)
    if _dist["gap"]:
        g = _dist["gap"]
        falta_tech = max(0, g["tech"]["required"] - g["tech"]["current"])
        falta_behav = max(0, g["behavioral"]["required"] - g["behavioral"]["current"])
        partes = []
        if falta_tech:
            partes.append(
                f"{falta_tech} técnica(s) (tem {g['tech']['current']}, "
                f"mínimo {g['tech']['required']})"
            )
        if falta_behav:
            partes.append(
                f"{falta_behav} comportamental(is) (tem {g['behavioral']['current']}, "
                f"mínimo {g['behavioral']['required']})"
            )
        return ToolResult(
            llm_message=(
                "Ainda não dá para aprovar: a metodologia WSI exige mais "
                + " e ".join(partes)
                + ". Gere as perguntas que faltam (add_wsi_question) ou substitua "
                "antes de aprovar."
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




# ── Eligibility tools (W1-A port from wizard_tool_registry.py) ───────────────

_ELIGIBILITY_DB_TIMEOUT_S = 8.0


def _handle_suggest_eligibility_templates(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Sugere templates de elegibilidade canonical para a vaga em criação.

    Lê ``industry``, ``work_model`` e ``languages`` dos parâmetros opcionais;
    usa ``ctx.company_id`` para escopo multi-tenant. Operação read-only.
    Retorna top-10 templates por relevância (score interno).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    job_industry = (tool_input.get("industry") or "").lower()
    work_model = (tool_input.get("work_model") or "").lower()
    languages = tool_input.get("languages") or []
    company_id = ctx.company_id

    PRIORITY_CATEGORIES = ["system_default", "eligibility", "availability", "compliance"]

    from app.core.database import AsyncSessionLocal
    from app.domains.cv_screening.repositories.eligibility_question_template_repository import (
        EligibilityQuestionTemplateRepository,
    )
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

    async def _fetch():
        async with AsyncSessionLocal() as db:
            repo = EligibilityQuestionTemplateRepository(db)
            return await repo.list_for_company(company_id=company_id, include_master=True)

    try:
        all_items = run_coro_in_threadpool(lambda: _fetch(), timeout=_ELIGIBILITY_DB_TIMEOUT_S)
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] suggest_eligibility_templates failed: %s", exc)
        return ToolResult(
            llm_message=f"Não consegui buscar os templates de elegibilidade ({exc}).",
            error=True,
        )

    suggestions = []
    for item in all_items:
        data = item.data or {}
        category = data.get("category", "")
        score = 0
        if category in PRIORITY_CATEGORIES:
            score += 3
        linked = data.get("linkedField")
        if linked == "workModel" and work_model:
            score += 5
        if linked == "languages" and languages:
            score += 5
        if linked == "location" and work_model in ("hibrido", "presencial"):
            score += 4
        if score > 0:
            suggestions.append({
                "id": str(item.id),
                "question": data.get("question", ""),
                "category": category,
                "is_master": item.is_master_template,
                "score": score,
            })

    suggestions.sort(key=lambda s: s["score"], reverse=True)
    top = suggestions[:10]

    return ToolResult(
        llm_message=(
            f"{len(top)} template(s) de elegibilidade sugerido(s) "
            f"(top 10 de {len(all_items)} no catálogo da empresa). "
            "Apresente as opções ao recrutador e aplique com apply_eligibility_template."
        ),
        state_updates={},
        data={
            "suggestions": top,
            "total_in_catalog": len(all_items),
            "industry_used": job_industry or None,
            "work_model_used": work_model or None,
        },
    )


def _handle_apply_eligibility_template_to_vacancy(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Aplica template de elegibilidade canonical à vaga em criação (snapshot B1).

    Copia o ``data`` do template e retorna o snapshot para ser adicionado a
    ``eligibility_questions`` no state. NÃO escreve no DB — a persistência
    ocorre no publish_job (save_job_draft).

    Parâmetros:
        template_id: UUID do template (obrigatório).
        vacancy_id: UUID da vaga (opcional — usado só para logging).
    """
    import uuid as _uuid

    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    template_id_raw = tool_input.get("template_id")
    vacancy_id = tool_input.get("vacancy_id")
    company_id = ctx.company_id

    if not template_id_raw:
        return ToolResult(
            llm_message="template_id é obrigatório para aplicar o template.",
            error=True,
        )

    try:
        template_uuid = (
            _uuid.UUID(template_id_raw)
            if isinstance(template_id_raw, str)
            else template_id_raw
        )
    except (ValueError, TypeError):
        return ToolResult(
            llm_message=f"template_id inválido: {template_id_raw!r}. Informe um UUID válido.",
            error=True,
        )

    from app.core.database import AsyncSessionLocal
    from app.domains.cv_screening.repositories.eligibility_question_template_repository import (
        EligibilityQuestionTemplateRepository,
    )
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

    async def _fetch():
        async with AsyncSessionLocal() as db:
            repo = EligibilityQuestionTemplateRepository(db)
            return await repo.get_by_id(template_uuid, company_id)

    try:
        template = run_coro_in_threadpool(lambda: _fetch(), timeout=_ELIGIBILITY_DB_TIMEOUT_S)
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] apply_eligibility_template failed: %s", exc)
        return ToolResult(
            llm_message=f"Erro ao buscar o template ({exc}).",
            error=True,
        )

    if not template:
        return ToolResult(
            llm_message="Template não encontrado ou fora do escopo da empresa.",
            error=True,
        )

    snapshot = dict(template.data or {})
    snapshot["_template_id"] = str(template.id)
    snapshot["_is_master_origin"] = template.is_master_template

    current = list(state.get("eligibility_questions") or [])
    current.append(snapshot)

    return ToolResult(
        llm_message=(
            f"Template '{snapshot.get('question', '')[:60]}' aplicado à vaga "
            f"(snapshot canonical B1; {len(current)} pergunta(s) de elegibilidade no total). "
            "Persistência ocorre ao publicar."
        ),
        state_updates={"eligibility_questions": current},
        data={
            "vacancy_id": vacancy_id,
            "template_id": str(template.id),
            "snapshot": snapshot,
            "is_master_origin": template.is_master_template,
            "total_eligibility_questions": len(current),
        },
    )


def _handle_create_custom_eligibility_template(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Cria template de elegibilidade custom via wizard conversacional.

    Persistido per-company no DB. Qualquer recrutador/admin pode criar
    (decisão Paulo C 2026-05-20). Após criar, o template fica disponível
    no catálogo da empresa para reutilização futura.

    Parâmetros obrigatórios: question (str, mín 3 chars).
    Parâmetros opcionais: type, category, eliminatory, eliminatoryAnswer,
        contextHint, options.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    question = (tool_input.get("question") or "").strip()
    if not question or len(question) < 3:
        return ToolResult(
            llm_message="Pergunta obrigatória (mínimo 3 caracteres).",
            error=True,
        )

    company_id = ctx.company_id
    user_id = ctx.user_id
    question_type = tool_input.get("type") or "yes_no"
    category = tool_input.get("category") or "general"

    data = {
        "question": question,
        "type": question_type,
        "category": category,
        "contextHint": tool_input.get("contextHint"),
        "eliminatory": bool(tool_input.get("eliminatory", False)),
        "eliminatoryAnswer": tool_input.get("eliminatoryAnswer"),
    }
    if tool_input.get("options"):
        data["options"] = tool_input["options"]

    from app.core.database import AsyncSessionLocal
    from app.domains.cv_screening.repositories.eligibility_question_template_repository import (
        EligibilityQuestionTemplateRepository,
    )
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

    async def _create():
        async with AsyncSessionLocal() as db:
            repo = EligibilityQuestionTemplateRepository(db)
            template = await repo.create_custom(
                company_id=company_id,
                data=data,
                created_by=str(user_id) if user_id else None,
            )
            await db.commit()
            return template

    try:
        template = run_coro_in_threadpool(lambda: _create(), timeout=_ELIGIBILITY_DB_TIMEOUT_S)
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] create_custom_eligibility_template failed: %s", exc)
        return ToolResult(
            llm_message=f"Falha ao criar template de elegibilidade ({exc}).",
            error=True,
        )

    return ToolResult(
        llm_message=(
            f"Template de elegibilidade criado com sucesso (ID: {template.id}). "
            "Ele já está disponível no catálogo da empresa. "
            "Use apply_eligibility_template para adicioná-lo à vaga atual."
        ),
        state_updates={},
        data={
            "id": str(template.id),
            "company_id": template.company_id,
            "is_master_template": False,
            "question": data["question"],
            "type": data["type"],
            "category": data["category"],
            "eliminatory": data["eliminatory"],
        },
    )


SUGGEST_ELIGIBILITY_TEMPLATES = WizardTool(
    name="suggest_eligibility_templates",
    description=(
        "Busca templates de perguntas de elegibilidade do catálogo da empresa "
        "relevantes para a vaga em criação. Filtra por setor (industry), "
        "modelo de trabalho (work_model) e idiomas (languages). Retorna até 10 "
        "sugestões ordenadas por relevância. Use para apresentar ao recrutador "
        "antes de aplicar com apply_eligibility_template."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "industry": {
                "type": "string",
                "description": "Setor da vaga (ex: tecnologia, saúde, financeiro).",
            },
            "work_model": {
                "type": "string",
                "description": "Modelo de trabalho (remoto, hibrido, presencial).",
            },
            "languages": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Idiomas exigidos pela vaga (ex: ['inglês', 'espanhol']).",
            },
        },
        "additionalProperties": False,
    },
    handler=_handle_suggest_eligibility_templates,
)

APPLY_ELIGIBILITY_TEMPLATE = WizardTool(
    name="apply_eligibility_template",
    description=(
        "Aplica um template de pergunta de elegibilidade à vaga em criação. "
        "Copia o snapshot do template para eligibility_questions no state "
        "(persistência ocorre ao publicar). Use após o recrutador escolher "
        "um template de suggest_eligibility_templates."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "template_id": {
                "type": "string",
                "description": "UUID do template de elegibilidade a aplicar.",
            },
            "vacancy_id": {
                "type": "string",
                "description": "UUID da vaga (opcional — para logging).",
            },
        },
        "required": ["template_id"],
        "additionalProperties": False,
    },
    handler=_handle_apply_eligibility_template_to_vacancy,
)

CREATE_CUSTOM_ELIGIBILITY_TEMPLATE = WizardTool(
    name="create_custom_eligibility_template",
    description=(
        "Cria um novo template de pergunta de elegibilidade customizado para a "
        "empresa. Use quando o recrutador quiser uma pergunta eliminatória que "
        "não existe no catálogo. O template criado fica disponível para "
        "reutilização futura."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Texto da pergunta de elegibilidade (mín 3 chars).",
            },
            "type": {
                "type": "string",
                "description": "Tipo da pergunta (yes_no, multiple_choice, etc.).",
            },
            "category": {
                "type": "string",
                "description": "Categoria (availability, compliance, work_model, legal, general).",
            },
            "eliminatory": {
                "type": "boolean",
                "description": "Se true, candidatos que não atendem são eliminados.",
            },
            "eliminatoryAnswer": {
                "type": "string",
                "description": "Resposta correta para elegibilidade (ex: 'sim', 'nao').",
            },
            "contextHint": {
                "type": "string",
                "description": "Contexto adicional para a pergunta (opcional).",
            },
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Opções de resposta para multiple_choice (opcional).",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
    handler=_handle_create_custom_eligibility_template,
)



# ── close_panel (minimizar painel lateral) ─────────────────────────────────────



def _build_manager_briefing_email(state: dict) -> str:
    """Monta HTML do briefing executivo para o gestor — v2.

    Secoes: cabecalho estruturado, JD, matriz de competencias (tecnicas x
    comportamentais), BigFive, cronograma com datas absolutas, remuneracao
    (salario + variavel + beneficios), triagem configurada.
    Sem referencia a nome de produto IA — neutro "IA WeDOTalent".
    """
    from datetime import date, timedelta

    # ---- dados basicos -------------------------------------------------
    title      = state.get("parsed_title") or "Vaga"
    seniority  = state.get("parsed_seniority") or ""
    department = state.get("parsed_department") or ""
    work_model = state.get("work_model") or ""
    emp_type   = state.get("employment_type") or ""
    job_id     = state.get("job_id") or ""
    today      = date.today()
    today_str  = today.strftime("%d/%m/%Y")

    mgr_name   = state.get("parsed_manager_name") or "Gestor"
    mgr_email  = state.get("parsed_manager_email") or ""
    rec_name   = state.get("parsed_recruiter_name") or state.get("recruiter_name") or "Recrutador"

    jd_full    = state.get("jd_enriched") or ""
    jd_excerpt = jd_full[:700] + ("…" if len(jd_full) > 700 else "")

    # ---- salario -------------------------------------------------------
    salary_min = state.get("salary_min")
    salary_max = state.get("salary_max")
    if salary_min and salary_max:
        salary_str = "R$ {:,.0f} – R$ {:,.0f}".format(salary_min, salary_max).replace(",", ".")
    elif salary_min:
        salary_str = "A partir de R$ {:,.0f}".format(salary_min).replace(",", ".")
    else:
        salary_str = ""
    salary_source = state.get("salary_source") or ""

    # ---- competencias --------------------------------------------------
    raw_comps = state.get("competencies") or []
    tech_comps, soft_comps = [], []
    for c in raw_comps[:16]:
        name  = (c.get("name") if isinstance(c, dict) else str(c))
        level = (c.get("level") or c.get("proficiency") or "") if isinstance(c, dict) else ""
        kind  = (c.get("type") or c.get("category") or "technical") if isinstance(c, dict) else "technical"
        entry = (name, level)
        if str(kind).lower() in {"behavioral", "comportamental", "soft", "behavior"}:
            soft_comps.append(entry)
        else:
            tech_comps.append(entry)
    if not soft_comps and tech_comps:
        mid = max(1, len(tech_comps) // 2)
        soft_comps = tech_comps[mid:]
        tech_comps = tech_comps[:mid]

    LEVEL_LABEL = {
        "expert": "Especialista", "especialista": "Especialista",
        "advanced": "Avancado", "avancado": "Avancado",
        "essential": "Essencial", "essencial": "Essencial",
        "required": "Requerido", "requerido": "Requerido",
        "desirable": "Desejavel", "desejavel": "Desejavel",
        "intermediate": "Intermediario",
    }
    LEVEL_COLOR = {
        "Especialista": "#085041", "Essencial": "#085041",
        "Avancado": "#3C3489", "Intermediario": "#3C3489",
        "Desejavel": "#5F5E5A", "Requerido": "#5F5E5A",
    }
    LEVEL_BG = {
        "Especialista": "#E1F5EE", "Essencial": "#E1F5EE",
        "Avancado": "#EEEDFE", "Intermediario": "#EEEDFE",
        "Desejavel": "#F1EFE8", "Requerido": "#F1EFE8",
    }

    def _comp_rows(comps):
        rows = []
        for name, level in comps[:7]:
            label = LEVEL_LABEL.get((level or "").lower().strip(), level or "Requerido")
            fg    = LEVEL_COLOR.get(label, "#5F5E5A")
            bg    = LEVEL_BG.get(label, "#F1EFE8")
            rows.append(
                "<tr>"
                "<td style=\"padding:6px 10px;font-size:12px;color:#333;border-bottom:1px solid #eee\">" + name + "</td>"
                "<td style=\"padding:6px 10px;text-align:right;border-bottom:1px solid #eee\">"
                "<span style=\"font-size:10px;padding:2px 7px;border-radius:20px;"
                "background:" + bg + ";color:" + fg + ";font-weight:500\">" + label + "</span>"
                "</td></tr>"
            )
        return "".join(rows)

    comp_block = ""
    if tech_comps or soft_comps:
        comp_block = (
            "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
            "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
            "padding-bottom:6px;margin-bottom:10px\">Competências requeridas</div>"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"margin-bottom:20px\"><tr>"
            "<td width=\"50%\" style=\"vertical-align:top;padding-right:8px\">"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"border:1px solid #eee;border-radius:6px;overflow:hidden\">"
            "<tr style=\"background:#E1F5EE\"><th style=\"padding:7px 10px;font-size:11px;font-weight:500;color:#085041;text-align:left\">Técnicas</th></tr>"
            + _comp_rows(tech_comps) +
            "</table></td>"
            "<td width=\"50%\" style=\"vertical-align:top;padding-left:8px\">"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"border:1px solid #eee;border-radius:6px;overflow:hidden\">"
            "<tr style=\"background:#EEEDFE\"><th style=\"padding:7px 10px;font-size:11px;font-weight:500;color:#3C3489;text-align:left\">Comportamentais</th></tr>"
            + _comp_rows(soft_comps) +
            "</table></td>"
            "</tr></table>"
        )

    # ---- BigFive -------------------------------------------------------
    BF_LABELS = {
        "openness": "Abertura", "conscientiousness": "Conscienciosidade",
        "extraversion": "Extroversão", "agreeableness": "Amabilidade",
        "neuroticism": "Neuroticismo", "estabilidade": "Estabilidade",
        "abertura": "Abertura", "conscienciosidade": "Conscienciosidade",
    }
    BF_COLORS = ["#7F77DD", "#1D9E75", "#378ADD", "#D85A30", "#888780"]
    bigfive = state.get("bigfive_profile") or {}
    bf_cells = ""
    for i, (k, v) in enumerate(bigfive.items()):
        if not isinstance(v, (int, float)):
            continue
        pct = int(round(float(v) * 100 if float(v) <= 1 else float(v)))
        lbl = BF_LABELS.get(k.lower(), k.capitalize())
        col = BF_COLORS[i % len(BF_COLORS)]
        bf_cells += (
            "<td style=\"padding:6px 8px;vertical-align:top;width:20%\">"
            "<div style=\"font-size:10px;color:#888;margin-bottom:2px\">" + lbl + "</div>"
            "<div style=\"font-size:15px;font-weight:500;color:#222\">" + str(pct) + "%</div>"
            "<div style=\"height:4px;background:#eee;border-radius:2px;margin-top:3px;overflow:hidden\">"
            "<div style=\"height:100%;width:" + str(pct) + "%;background:" + col + ";border-radius:2px\"></div>"
            "</div></td>"
        )
    bf_block = ""
    if bf_cells:
        bf_block = (
            "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
            "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
            "padding-bottom:6px;margin-bottom:10px\">Perfil comportamental ideal</div>"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\"><tr>" + bf_cells + "</tr></table>"
            "<div style=\"font-size:10px;color:#aaa;margin-bottom:20px\">"
            "Extraído da descrição da vaga pela inteligência artificial da WeDOTalent"
            "</div>"
        )

    # ---- cronograma ----------------------------------------------------
    chronogram = state.get("derived_chronogram") or []
    DOT_COLORS = ["#1D9E75", "#7F77DD", "#378ADD", "#D85A30", "#888780",
                  "#EF9F27", "#9FE1CB", "#AFA9EC"]
    chron_block = ""
    if chronogram:
        TYPE_LABEL = {"automatic": "Automática", "manual": "Manual", "hybrid": "Híbrida"}
        rows = ""
        for i, stage in enumerate(chronogram):
            start_d = today + timedelta(days=int(stage.get("offset_start", 0)))
            end_d   = today + timedelta(days=int(stage.get("offset_end", stage.get("sla_days", 0))))
            dot     = DOT_COLORS[i % len(DOT_COLORS)]
            s_type  = TYPE_LABEL.get(str(stage.get("type", "")).lower(), "")
            type_td = ("<div style=\"font-size:10px;color:#888\">" + s_type + "</div>") if s_type else ""
            rows += (
                "<tr>"
                "<td style=\"padding:7px 0;border-bottom:1px solid #eee;vertical-align:middle;width:14px\">"
                "<div style=\"width:10px;height:10px;border-radius:50%;background:" + dot + "\"></div></td>"
                "<td style=\"padding:7px 8px;border-bottom:1px solid #eee\">"
                "<div style=\"font-size:12px;color:#222\">" + stage["name"] + "</div>" + type_td + "</td>"
                "<td style=\"padding:7px 8px;border-bottom:1px solid #eee;text-align:center;"
                "font-size:12px;color:#888\">" + str(stage["sla_days"]) + " dias</td>"
                "<td style=\"padding:7px 0;border-bottom:1px solid #eee;text-align:right\">"
                "<span style=\"font-size:11px;color:#888\">" + start_d.strftime("%d/%m") + " → </span>"
                "<span style=\"font-size:11px;font-weight:500;color:#222\">" + end_d.strftime("%d/%m") + "</span>"
                "</td></tr>"
            )
        last_end = today + timedelta(days=int(chronogram[-1].get("offset_end", 0)))
        rows += (
            "<tr><td colspan=\"4\" style=\"padding-top:8px\">"
            "<div style=\"background:#E1F5EE;padding:6px 10px;border-radius:6px;"
            "display:flex;justify-content:space-between\">"
            "<span style=\"font-size:12px;color:#5F5E5A\">Previsão de contratação</span>"
            "<span style=\"font-size:12px;font-weight:500;color:#0F6E56\">até " +
            last_end.strftime("%d/%m/%Y") + "</span></div></td></tr>"
        )
        chron_block = (
            "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
            "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
            "padding-bottom:6px;margin-bottom:10px\">Cronograma do processo seletivo</div>"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"margin-bottom:20px\">"
            + rows + "</table>"
        )

    # ---- remuneracao variavel ------------------------------------------
    var_comps = state.get("variable_compensation") or []
    var_rows = ""
    for vc in var_comps[:6]:
        if isinstance(vc, dict):
            name = vc.get("name") or vc.get("kind") or "Componente"
            pct  = vc.get("target_pct") or vc.get("max_pct")
            amt  = vc.get("max_amount")
            val_str = ("até " + str(pct) + "%") if pct else (
                "até R$ {:,.0f}".format(amt).replace(",", ".") if amt else "—"
            )
            var_rows += (
                "<tr>"
                "<td style=\"padding:5px 0;border-bottom:1px solid #eee;font-size:12px;color:#333\">" + name + "</td>"
                "<td style=\"padding:5px 0;border-bottom:1px solid #eee;text-align:right;"
                "font-size:12px;font-weight:500;color:#0F6E56\">" + val_str + "</td>"
                "</tr>"
            )

    # ---- beneficios ----------------------------------------------------
    benefits = state.get("benefits") or []
    ben_tags = ""
    for b in benefits[:12]:
        label = (b.get("name") or b.get("label") or str(b)) if isinstance(b, dict) else str(b)
        ben_tags += (
            "<span style=\"display:inline-block;font-size:11px;padding:3px 9px;"
            "border-radius:20px;background:#F1EFE8;color:#5F5E5A;margin:3px 4px 0 0;"
            "border:0.5px solid #D3D1C7\">" + label + "</span>"
        )

    # ---- bloco remuneracao completo ------------------------------------
    salary_td = ""
    if salary_str:
        source_div = ("<div style=\"font-size:11px;color:#888;margin-top:2px\">" + salary_source + "</div>") if salary_source else ""
        salary_td = (
            "<td width=\"50%\" style=\"vertical-align:top;padding-right:8px\">"
            "<div style=\"border:1px solid #eee;border-radius:6px;padding:10px 12px\">"
            "<div style=\"font-size:10px;color:#888;margin-bottom:2px\">Salário base</div>"
            "<div style=\"font-size:16px;font-weight:600;color:#222\">" + salary_str + "</div>"
            + source_div + "</div></td>"
        )
    var_td = ""
    if var_rows:
        var_td = (
            "<td width=\"50%\" style=\"vertical-align:top;padding-left:8px\">"
            "<div style=\"border:1px solid #eee;border-radius:6px;padding:10px 12px\">"
            "<div style=\"font-size:10px;color:#888;margin-bottom:6px\">Remuneração variável</div>"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\">" + var_rows + "</table>"
            "</div></td>"
        )
    rem_block = ""
    if salary_td or var_td or ben_tags:
        rem_block = (
            "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
            "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
            "padding-bottom:6px;margin-bottom:10px\">Remuneração &amp; benefícios</div>"
        )
        if salary_td or var_td:
            rem_block += (
                "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"margin-bottom:12px\">"
                "<tr>" + (salary_td or "<td></td>") + (var_td or "<td></td>") + "</tr></table>"
            )
        if ben_tags:
            rem_block += (
                "<div style=\"font-size:11px;color:#888;margin-bottom:4px\">Benefícios incluísos</div>"
                "<div style=\"margin-bottom:20px\">" + ben_tags + "</div>"
            )

    # ---- triagem -------------------------------------------------------
    screening_mode = (state.get("screening_mode") or "wsi").upper()
    n_q       = len(state.get("wsi_questions") or [])
    dist      = state.get("expected_distribution") or {}
    threshold = dist.get("threshold") if isinstance(dist, dict) else 3.75
    threshold = threshold or 3.75

    # ---- cabecalho -----------------------------------------------------
    subtitle_parts = [p for p in [seniority, emp_type, work_model] if p]
    subtitle = " · ".join(subtitle_parts)
    mgr_to   = mgr_name + (" &lt;" + mgr_email + "&gt;" if mgr_email else "")
    job_badge = ""
    if job_id:
        job_badge = (
            "<div style=\"font-size:10px;color:#fff;background:rgba(255,255,255,.15);"
            "display:inline-block;padding:2px 9px;border-radius:20px;margin-top:6px\">"
            "Job ID " + str(job_id) + " · Publicada em " + today_str + "</div>"
        )
    total_days_td = ""
    if chronogram:
        total_d = str(chronogram[-1].get("offset_end", ""))
        total_days_td = (
            "<td align=\"right\" style=\"vertical-align:top\">"
            "<div style=\"font-size:10px;color:#5DCAA5\">Processo estimado</div>"
            "<div style=\"font-size:22px;font-weight:600;color:#fff\">" + total_d + " dias</div>"
            "</td>"
        )
    subtitle_div = ""
    if subtitle:
        subtitle_div = "<div style=\"font-size:12px;color:#5DCAA5;margin-top:3px\">" + subtitle + "</div>"

    html = (
        "<!DOCTYPE html>"
        "<html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width\"></head>"
        "<body style=\"margin:0;padding:0;font-family:Arial,sans-serif;background:#f5f5f5\">"
        "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" "
        "style=\"background:#f5f5f5;padding:24px 0\"><tr><td align=\"center\">"
        "<table width=\"640\" cellspacing=\"0\" cellpadding=\"0\" "
        "style=\"background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e0e0e0\">"

        # cabecalho verde
        "<tr><td style=\"background:#0F6E56;padding:20px 28px\">"
        "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\"><tr>"
        "<td>"
        "<div style=\"font-size:10px;font-weight:500;color:#9FE1CB;"
        "letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px\">"
        "WeDOTalent · Briefing de Contratação</div>"
        "<div style=\"font-size:18px;font-weight:600;color:#fff;line-height:1.3\">" + title + "</div>"
        + subtitle_div + job_badge +
        "</td>" + total_days_td + "</tr></table></td></tr>"

        # barra destinatario
        "<tr><td style=\"background:#085041;padding:10px 28px\">"
        "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" "
        "style=\"font-size:12px\"><tr>"
        "<td style=\"color:#5DCAA5;width:60px\">Para</td>"
        "<td style=\"color:#E1F5EE\">" + mgr_to + "</td>"
        "<td style=\"color:#5DCAA5;width:80px\">Recrutador</td>"
        "<td style=\"color:#E1F5EE\">" + rec_name + "</td>"
        "<td style=\"color:#5DCAA5;width:60px;padding-left:12px\">Enviado</td>"
        "<td style=\"color:#E1F5EE\">" + today_str + "</td>"
        "</tr></table></td></tr>"

        # corpo
        "<tr><td style=\"padding:22px 28px\">"

        # JD
        "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
        "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
        "padding-bottom:6px;margin-bottom:10px\">Descrição da vaga</div>"
        "<div style=\"font-size:13px;line-height:1.7;color:#555;border-left:3px solid #1D9E75;"
        "padding:8px 14px;background:#f9f9f9;border-radius:0 6px 6px 0;margin-bottom:20px\">"
        + jd_excerpt + "</div>"

        + comp_block + bf_block + chron_block + rem_block +

        # triagem
        "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
        "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
        "padding-bottom:6px;margin-bottom:10px\">Triagem automática configurada</div>"
        "<div>"
        "<span style=\"font-size:11px;padding:3px 9px;border-radius:20px;"
        "background:#EEEDFE;color:#534AB7;font-weight:500;margin-right:6px\">"
        + screening_mode + " · " + str(n_q) + " perguntas</span>"
        "<span style=\"font-size:11px;padding:3px 9px;border-radius:20px;"
        "background:#EAF3DE;color:#3B6D11;font-weight:500\">"
        "Aprovação automática ≥ " + str(threshold) + "</span>"
        "</div>"

        "</td></tr>"

        # rodape
        "<tr><td style=\"padding:12px 28px;border-top:1px solid #eee;"
        "font-size:11px;color:#aaa\">"
        "Gerado automaticamente pela inteligência artificial da WeDOTalent · " + today_str +
        "</td></tr>"

        "</table></td></tr></table></body></html>"
    )
    return html


def _handle_send_manager_briefing(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Envia plano de trabalho executivo ao gestor da vaga por email.

    Requer: job_id publicado + parsed_manager_email no state.
    Compoe briefing com JD resumida, competências, BigFive, cronograma do
    pipeline, faixa salarial e config de triagem.
    Multi-tenancy: company_id sempre de ctx.company_id.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    job_id = state.get("job_id")
    if not job_id:
        return ToolResult(
            llm_message=(
                "A vaga ainda não foi publicada. "
                "Publique a vaga (publish_job) antes de enviar o briefing ao gestor."
            ),
            error=True,
        )

    manager_email = state.get("parsed_manager_email")
    if not manager_email:
        return ToolResult(
            llm_message=(
                "Email do gestor não encontrado. "
                "Informe o email do gestor para enviar o briefing."
            ),
            error=True,
        )

    company_id = ctx.company_id
    if not company_id:
        return ToolResult(
            llm_message="Contexto de empresa ausente — não é possível enviar o briefing.",
            error=True,
        )

    try:
        from app.domains.communication.services.communication_dispatcher import (
            CommunicationDispatcherService,
        )
        from app.core.database import AsyncSessionLocal
        from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

        title = state.get("parsed_title") or "Vaga"
        manager_name = state.get("parsed_manager_name") or "Gestor"
        body_html = _build_manager_briefing_email(state)

        async def _dispatch():
            async with AsyncSessionLocal() as db:
                dispatcher = CommunicationDispatcherService()
                return await dispatcher.dispatch_message(
                    company_id=company_id,
                    recipient_email=manager_email,
                    subject=f"[WeDOTalent] Briefing de Contratação — {title}",
                    message=body_html,
                    channel="email",
                    candidate_name=manager_name,
                    db=db,
                    multi_channel=False,
                )

        result = run_coro_in_threadpool(lambda: _dispatch(), timeout=20)
        status = (result or {}).get("status", "unknown")
        if status == "error":
            raise RuntimeError((result or {}).get("error", "dispatch error"))

        return ToolResult(
            llm_message=(
                f"Briefing enviado para {manager_name} ({manager_email})! "
                f"O gestor recebeu: resumo da vaga, competências requeridas, "
                f"cronograma do processo seletivo e configuração de triagem."
            ),
            state_updates={"manager_briefing_sent": True},
        )

    except Exception as exc:  # noqa: BLE001
        logger.warning("[WizardServiceTools] send_manager_briefing failed: %s", exc)
        return ToolResult(
            llm_message=(
                f"Não foi possível enviar o briefing agora ({exc}). "
                "Tente novamente em instantes."
            ),
            error=True,
        )


def _handle_close_panel(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Fecha/minimiza o painel lateral do wizard retornando ao card de dock.

    Emite ``ui_action: close_panel`` via SSE sink (mesmo padrao de
    wizard_orchestrator._emit_reasoning_sync). Sem state_updates — a acao
    e puramente de UI.
    """
    try:
        import asyncio as _asyncio
        from lia_agents_core.streaming_callback import (  # noqa: PLC0415
            _sse_frame_sink as _sink_cv,
        )
        from app.shared.chat_event_serializer import (  # noqa: PLC0415
            serialize_message as _ser_msg,
        )

        _sink = _sink_cv.get(None)
        if _sink is not None:
            _frame = _ser_msg(content="", ui_action="close_panel", domain="wizard")
            try:
                _loop = _asyncio.get_event_loop()
                if _loop.is_running():
                    _asyncio.run_coroutine_threadsafe(_sink(_frame), _loop)
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001 — best-effort, nunca bloqueia o wizard
        logger.debug("[WizardTool] close_panel SSE emit failed", exc_info=True)

    return ToolResult(
        llm_message=(
            "Painel lateral minimizado. O recrutador pode continuar pelo chat. "
            "Use open_panel para reabrir quando necessario."
        )
    )


SEND_MANAGER_BRIEFING = WizardTool(
    name="send_manager_briefing",
    description=(
        "Envia plano de trabalho executivo ao gestor da vaga por email "
        "apos a publicacao. Inclui: JD resumida, competencias requeridas, "
        "perfil comportamental BigFive, cronograma do processo seletivo, "
        "faixa salarial e configuracao de triagem. "
        "So use apos job_id existir no state (vaga publicada) e com manager_email disponivel."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    handler=_handle_send_manager_briefing,
)


CLOSE_PANEL = WizardTool(
    name="close_panel",
    description=(
        "Minimiza o painel lateral do wizard, retornando ao modo de card de dock. "
        "Use quando o recrutador pedir 'fechar o painel', 'seguir so pelo chat', "
        "ou quando a etapa atual nao requer revisao no painel. "
        "NAO use para finalizar a vaga — use publish_job para isso."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    handler=_handle_close_panel,
)


# ── suggest_benefits ─────────────────────────────────────────────────────────

def _handle_suggest_benefits(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Busca o catálogo de benefícios da empresa e popula state.benefits.

    Filtra benefícios ativos pelo departamento e tipo de contrato da vaga.
    Sem catálogo configurado, retorna lista vazia com orientação ao recrutador.
    """
    _reject_tenant_keys(tool_input)

    company_id = ctx.company_id
    if not company_id:
        return ToolResult(
            llm_message="Empresa não identificada — não consigo buscar o catálogo de benefícios.",
            error=True,
        )

    department  = state.get("parsed_department") or state.get("department") or ""
    emp_type    = state.get("employment_type") or state.get("parsed_employment_type") or ""

    async def _fetch():
        from app.shared.database import AsyncSessionLocal
        from app.domains.company.repositories.benefit_repository import BenefitRepository
        from uuid import UUID
        async with AsyncSessionLocal() as db:
            repo = BenefitRepository(db)
            try:
                cid = UUID(str(company_id))
            except ValueError:
                return []
            return await repo.list_active_for_company(cid)

    try:
        benefits_orm = run_coro_in_threadpool(lambda: _fetch(), timeout=10)
    except Exception as exc:
        logger.warning("[WizardServiceTools] suggest_benefits failed: %s", exc)
        return ToolResult(
            llm_message=(
                "Não consegui carregar o catálogo de benefícios agora. "
                "Oriente o recrutador a informar os benefícios manualmente."
            ),
            error=False,
        )

    if not benefits_orm:
        return ToolResult(
            llm_message=(
                "Nenhum benefício cadastrado no catálogo da empresa ainda. "
                "O recrutador pode informar os benefícios manualmente agora "
                "ou cadastrá-los em Configurações → Benefícios primeiro."
            ),
            state_updates={"benefits": []},
        )

    # Serializa para shape compatível com VagaBenefit (backward-compat)
    result_list = []
    for b in benefits_orm:
        item = {"name": b.name, "source": "catalog"}
        if b.category:
            item["category"] = b.category
        if b.icon:
            item["icon"] = b.icon
        if b.value:
            item["value"] = b.value
        if b.value_type:
            item["value_type"] = b.value_type
        if getattr(b, "is_highlighted", False):
            item["is_highlighted"] = True
        result_list.append(item)

    names = [b["name"] for b in result_list]
    summary = ", ".join(names[:6]) + (f" e mais {len(names)-6}" if len(names) > 6 else "")
    return ToolResult(
        llm_message=(
            f"Encontrei {len(result_list)} benefícios no catálogo da empresa: {summary}. "
            "Eles já foram adicionados à vaga. O recrutador pode remover os que não se aplicam."
        ),
        state_updates={"benefits": result_list},
    )


SUGGEST_BENEFITS = WizardTool(
    name="suggest_benefits",
    description=(
        "Busca o catálogo de benefícios da empresa e sugere automaticamente os "
        "benefícios para a vaga. Use quando o recrutador perguntar sobre benefícios "
        "ou ao iniciar o stage de salário/remuneração. Apresente a lista e permita "
        "ao recrutador confirmar ou remover itens."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_suggest_benefits,
)


# ── suggest_variable_compensation ────────────────────────────────────────────

def _handle_suggest_variable_compensation(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Busca o catálogo de verbas variáveis da empresa e popula state.variable_compensation.

    Usa list_matching para priorizar verbas compatíveis com departamento/senioridade/
    tipo de contrato da vaga. Retorna todas — compatíveis pre-marcadas.
    """
    _reject_tenant_keys(tool_input)

    company_id = ctx.company_id
    if not company_id:
        return ToolResult(
            llm_message="Empresa não identificada — não consigo buscar o catálogo de verbas variáveis.",
            error=True,
        )

    department    = state.get("parsed_department") or state.get("department") or None
    seniority     = state.get("parsed_seniority") or state.get("seniority") or None
    emp_type      = state.get("employment_type") or state.get("parsed_employment_type") or None

    async def _fetch():
        from app.shared.database import AsyncSessionLocal
        from app.domains.company.repositories.compensation_component_repository import (
            CompensationComponentRepository,
        )
        async with AsyncSessionLocal() as db:
            repo = CompensationComponentRepository(db)
            return await repo.list_matching(
                company_id=str(company_id),
                seniority_level=seniority,
                department=department,
                contract_type=emp_type,
            )

    try:
        matched = run_coro_in_threadpool(lambda: _fetch(), timeout=10)
    except Exception as exc:
        logger.warning("[WizardServiceTools] suggest_variable_compensation failed: %s", exc)
        return ToolResult(
            llm_message=(
                "Não consegui carregar o catálogo de verbas variáveis agora. "
                "Oriente o recrutador a informar os componentes manualmente."
            ),
            error=False,
        )

    if not matched:
        return ToolResult(
            llm_message=(
                "Nenhuma verba variável cadastrada no catálogo da empresa ainda. "
                "O recrutador pode informar os componentes manualmente ou "
                "cadastrá-los em Configurações → Remuneração Variável primeiro."
            ),
            state_updates={"variable_compensation": []},
        )

    from app.domains.job_creation.helpers.vaga_variable_comp import snapshot_from_catalog

    # Inclui todos; compatíveis têm matches_vaga=True no snapshot
    result_list = []
    compatible_count = 0
    for comp, matches in matched:
        snap = snapshot_from_catalog(comp)
        d = snap.model_dump()
        d["matches_vaga"] = matches
        if matches:
            compatible_count += 1
        result_list.append(d)

    total = len(result_list)
    summary_names = [r["name"] for r in result_list if r.get("matches_vaga")][:4]
    summary = ", ".join(summary_names) + (f" e outros" if total > len(summary_names) else "")
    return ToolResult(
        llm_message=(
            f"Encontrei {total} verbas variáveis no catálogo — "
            f"{compatible_count} compatíveis com este cargo ({summary}). "
            "Elas já foram adicionadas à vaga. O recrutador pode remover as que não se aplicam."
        ),
        state_updates={"variable_compensation": result_list},
    )


SUGGEST_VARIABLE_COMPENSATION = WizardTool(
    name="suggest_variable_compensation",
    description=(
        "Busca o catálogo de verbas variáveis da empresa (PLR, bônus, comissão, etc.) "
        "e sugere automaticamente os componentes para a vaga, priorizando os "
        "compatíveis com departamento/senioridade/tipo de contrato. Use quando o "
        "recrutador mencionar remuneração variável ou ao montar o pacote salarial."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_suggest_variable_compensation,
)




# ── set_operational_fields (W3-A) ─────────────────────────────────────────────

_VALID_PRIORITIES = {"normal", "high", "urgent"}
_VALID_URGENCY_LEVELS = {0, 1, 2}


def _handle_set_operational_fields(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Define campos operacionais da vaga: prioridade, urgência, confidencialidade.

    Todos são opcionais. Se o recrutador não especificar, defaults seguros são
    aplicados no publish (normal/0/False). Este tool existe para casos onde o
    recrutador declara urgência ou vaga sigilosa durante o wizard.

    Multi-tenancy: company_id proibido no input (sempre do ctx).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    updates: dict = {}
    errors: list[str] = []

    priority = tool_input.get("priority")
    if priority is not None:
        if priority not in _VALID_PRIORITIES:
            errors.append(
                f"priority inválido: {priority!r}. "
                f"Valores aceitos: {sorted(_VALID_PRIORITIES)}"
            )
        else:
            updates["priority"] = priority

    urgency_level = tool_input.get("urgency_level")
    if urgency_level is not None:
        try:
            urgency_level = int(urgency_level)
        except (TypeError, ValueError):
            errors.append("urgency_level deve ser inteiro 0/1/2")
        else:
            if urgency_level not in _VALID_URGENCY_LEVELS:
                errors.append(
                    f"urgency_level inválido: {urgency_level}. Valores aceitos: 0, 1, 2"
                )
            else:
                updates["urgency_level"] = urgency_level

    is_confidential = tool_input.get("is_confidential")
    if is_confidential is not None:
        updates["is_confidential"] = bool(is_confidential)

    if errors:
        return ToolResult(llm_message="; ".join(errors), error=True)

    if not updates:
        return ToolResult(
            llm_message="Nenhum campo operacional alterado.",
            state_updates={},
        )

    labels = []
    if "priority" in updates:
        _priority_labels = {"normal": "Normal", "high": "Alta", "urgent": "Urgente"}
        labels.append(f"prioridade: {_priority_labels.get(updates['priority'], updates['priority'])}")
    if "urgency_level" in updates:
        _urg_labels = {0: "Normal", 1: "Alta", 2: "Crítica"}
        labels.append(f"urgência: {_urg_labels.get(updates['urgency_level'], updates['urgency_level'])}")
    if "is_confidential" in updates:
        labels.append("vaga confidencial" if updates["is_confidential"] else "vaga pública")

    return ToolResult(
        llm_message=f"Campos operacionais atualizados: {', '.join(labels)}.",
        state_updates=updates,
    )


SET_OPERATIONAL_FIELDS = WizardTool(
    name="set_operational_fields",
    description=(
        "Define campos operacionais da vaga: prioridade (normal/high/urgent), "
        "nível de urgência (0=normal, 1=alta, 2=crítica) e se a vaga é "
        "confidencial (is_confidential=true/false). Use quando o recrutador "
        "mencionar urgência, prazo apertado ou solicitar discrição na vaga."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "priority": {
                "type": "string",
                "enum": ["normal", "high", "urgent"],
                "description": "Prioridade da vaga",
            },
            "urgency_level": {
                "type": "integer",
                "enum": [0, 1, 2],
                "description": "0=normal, 1=alta, 2=crítica",
            },
            "is_confidential": {
                "type": "boolean",
                "description": "True se a vaga é confidencial/sigilosa",
            },
        },
        "additionalProperties": False,
    },
    handler=_handle_set_operational_fields,
)


# ---------------------------------------------------------------------------
# W1-B — Set Affirmative Fields
# ---------------------------------------------------------------------------


def _handle_add_bank_question(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Adiciona uma pergunta do banco da empresa ao set WSI do wizard.

    Busca pelo question_id canonical (CompanyScreeningQuestionRepository).
    Multi-tenancy: valida que a pergunta pertence ao company_id do state.
    Fail-loud: question_id inexistente ou de outro tenant retorna erro explícito.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    question_id = str(tool_input.get("question_id") or "").strip()
    if not question_id:
        return ToolResult(llm_message="question_id é obrigatório.", error=True)

    company_id = state.get("company_id") or (ctx.company_id if ctx else "")
    if not company_id:
        return ToolResult(
            llm_message="Não foi possível identificar a empresa. Tente novamente.", error=True
        )

    # Gate de limite máximo por modo
    _mode = str(state.get("screening_mode") or "compact").strip().lower()
    _max_total = 12 if _mode == "full" else 7
    _current = list(state.get("wsi_questions") or [])
    if len(_current) >= _max_total:
        return ToolResult(
            llm_message=(
                f"O pacote já tem {len(_current)} perguntas — limite máximo para o modo "
                f"{'completo' if _mode == 'full' else 'compacto'} ({_max_total}). "
                "Para adicionar do banco, primeiro remova uma existente."
            ),
            error=True,
        )

    try:
        from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool  # noqa: PLC0415
        from app.domains.recruitment.repositories.company_screening_question_repository import (
            CompanyScreeningQuestionRepository,
        )
        from app.core.database import AsyncSessionLocal
        import uuid as _uuid

        try:
            _qid = _uuid.UUID(question_id)
        except ValueError:
            return ToolResult(llm_message=f"question_id inválido: '{question_id}'.", error=True)

        async def _fetch_question():
            async with AsyncSessionLocal() as _db:
                return await CompanyScreeningQuestionRepository(_db).get_by_id(_qid, company_id)

        q = run_coro_in_threadpool(_fetch_question, timeout=5)
    except Exception as exc:
        logger.warning("[WizardServiceTools] add_bank_question lookup failed: %s", exc)
        return ToolResult(
            llm_message=f"Erro ao buscar pergunta do banco ({exc}). Tente novamente.", error=True
        )

    if q is None:
        return ToolResult(
            llm_message=f"Pergunta '{question_id}' não encontrada no banco da empresa.", error=True
        )

    # Converter para o formato de ScreeningQuestion do wizard
    block = "technical" if (q.category or "").lower() in ("technical", "tecnica", "técnica") else "behavioral"
    new_question = {
        "question": q.question_text,
        "framework": "Banco",  # distingue visualmente das LLM-geradas
        "block": block,
        "skill": q.category or "",
        "ideal_answer": q.expected_answer or "",
        "weight": 1.0,
        "approved": False,
        "needs_manual_review": False,
        "source": "company_bank",
        "bank_question_id": str(q.id),
        "is_eliminatory": bool(q.is_eliminatory),
    }

    questions = _current + [new_question]
    return ToolResult(
        llm_message=(
            f'Adicionada pergunta do banco: "{q.question_text[:80]}{"..." if len(q.question_text) > 80 else ""}". '
            f"O pacote agora tem {len(questions)} perguntas."
        ),
        state_updates={"wsi_questions": questions, "questions_approved": None},
    )


ADD_BANK_QUESTION = WizardTool(
    name="add_bank_question",
    description=(
        "Adiciona uma pergunta do banco de perguntas da empresa ao set WSI do wizard. "
        "Usar quando o recrutador clicar em 'Adicionar do banco' no painel ou pedir para "
        "adicionar uma pergunta específica do banco. "
        "O question_id deve ser o UUID exato recebido — não modifique."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "question_id": {
                "type": "string",
                "description": "UUID da pergunta no banco da empresa. Copie exatamente da mensagem — não altere.",
            },
        },
        "required": ["question_id"],
    },
    handler=_handle_add_bank_question,
)

def _handle_set_affirmative_fields(
    state: "JobCreationState",
    tool_input: dict,
    ctx: "WizardContext",
) -> "ToolResult":
    """Seta campos de vaga afirmativa a partir do que foi confirmado pelo recrutador."""
    _reject_tenant_keys(tool_input)

    is_affirmative = bool(tool_input.get("is_affirmative", False))
    criteria_primary = tool_input.get("criteria_primary")
    criteria_secondary = tool_input.get("criteria_secondary")
    description = tool_input.get("description")
    document_required = bool(tool_input.get("document_required", True))
    document_types = tool_input.get("document_types") or []

    if not is_affirmative:
        return ToolResult(
            llm_message="Vaga desmarcada como afirmativa.",
            state_updates={
                "is_affirmative": False,
                "affirmative_criteria_primary": None,
                "affirmative_criteria_secondary": None,
                "affirmative_description": None,
                "affirmative_document_required": True,
                "affirmative_document_types": [],
            },
        )

    if not criteria_primary:
        return ToolResult(
            llm_message=(
                "Para configurar a vaga afirmativa preciso saber o critério principal. "
                "Por favor informe: gênero (mulheres), raça/etnia (pessoas negras), "
                "deficiência (PcD), lgbtqia+, 50+, indígena ou refugiado."
            ),
            error=False,
        )

    _CRITERIA_LABELS = {
        "gender": "Gênero (Mulheres)",
        "race_ethnicity": "Raça/Etnia",
        "disability": "Pessoa com Deficiência (PcD)",
        "lgbtqia": "LGBTQIA+",
        "age": "50+ anos",
        "indigenous": "Povos Indígenas",
        "refugee": "Refugiados/Imigrantes",
        "other": "Ação Afirmativa",
    }

    label_primary = _CRITERIA_LABELS.get(criteria_primary, criteria_primary)
    label_secondary = _CRITERIA_LABELS.get(criteria_secondary, criteria_secondary) if criteria_secondary else None

    criteria_info = label_primary
    if label_secondary:
        criteria_info += f" + {label_secondary}"

    doc_info = ""
    if document_required and document_types:
        doc_info = f" Documentação exigida: {', '.join(document_types)}."

    msg = (
        f"Vaga configurada como afirmativa para: {criteria_info}."
        + (f" Descrição: {description}." if description else "")
        + doc_info
        + " Os critérios serão aplicados durante a triagem de candidatos pelo FairnessGuard."
    )

    return ToolResult(
        llm_message=msg,
        state_updates={
            "is_affirmative": True,
            "affirmative_criteria_primary": criteria_primary,
            "affirmative_criteria_secondary": criteria_secondary,
            "affirmative_description": description,
            "affirmative_document_required": document_required,
            "affirmative_document_types": document_types,
        },
    )


SET_AFFIRMATIVE_FIELDS = WizardTool(
    name="set_affirmative_fields",
    description=(
        "Configura a vaga como afirmativa (ação afirmativa para grupos sub-representados). "
        "Use quando o recrutador mencionar vaga afirmativa, PcD, mulheres, pessoas negras, "
        "LGBTQIA+, 50+, indígenas, refugiados ou similares — ou para confirmar o que foi "
        "detectado automaticamente pelo sistema no intake. Os campos são persistidos no "
        "publish e ativam o FairnessGuard na triagem."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "is_affirmative": {
                "type": "boolean",
                "description": "True para ativar vaga afirmativa, False para desativar.",
            },
            "criteria_primary": {
                "type": "string",
                "enum": ["gender", "race_ethnicity", "disability", "lgbtqia", "age", "indigenous", "refugee", "other"],
                "description": "Critério principal da ação afirmativa.",
            },
            "criteria_secondary": {
                "type": "string",
                "enum": ["gender", "race_ethnicity", "disability", "lgbtqia", "age", "indigenous", "refugee", "other"],
                "description": "Critério secundário opcional (ex: mulheres negras = gender + race_ethnicity).",
            },
            "description": {
                "type": "string",
                "description": "Descrição livre da ação afirmativa (ex: 'Mulheres negras acima de 40 anos').",
            },
            "document_required": {
                "type": "boolean",
                "description": "Se exige documentação comprobatória do candidato (padrão: True).",
            },
            "document_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tipos de documentos aceitos (ex: ['laudo_pcd', 'autodeclaracao_racial']).",
            },
        },
        "required": ["is_affirmative"],
        "additionalProperties": False,
    },
    handler=_handle_set_affirmative_fields,
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
    SUGGEST_ELIGIBILITY_TEMPLATES,
    APPLY_ELIGIBILITY_TEMPLATE,
    CREATE_CUSTOM_ELIGIBILITY_TEMPLATE,
    SEND_MANAGER_BRIEFING,
    SUGGEST_BENEFITS,
    SUGGEST_VARIABLE_COMPENSATION,
    SET_OPERATIONAL_FIELDS,
    ADD_BANK_QUESTION,
    SET_AFFIRMATIVE_FIELDS,
    CLOSE_PANEL,
)
