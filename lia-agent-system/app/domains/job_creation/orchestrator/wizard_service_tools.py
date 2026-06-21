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
import re
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



def _handle_confirm_competencies(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Registra a confirmação/ajuste das competências pelo recrutador.

    O recrutador pode aprovar as sugestões como estão ou fornecer uma lista
    ajustada. O state ``competencies_confirmed`` grava a decisão.
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    confirmed_technical = tool_input.get("technical") or []
    confirmed_behavioral = tool_input.get("behavioral") or []

    if not confirmed_technical and not confirmed_behavioral:
        suggested = state.get("suggested_competencies") or {}
        confirmed_technical = [
            c.get("skill") or c.get("name") or ""
            for c in (suggested.get("technical") or [])
        ]
        confirmed_behavioral = [
            c.get("competencia") or c.get("name") or ""
            for c in (suggested.get("behavioral") or [])
        ]

    if not confirmed_technical and not confirmed_behavioral:
        return ToolResult(
            llm_message=(
                "Nenhuma competência para confirmar. Primeiro chame "
                "suggest_competencies ou peça ao recrutador quais competências "
                "são relevantes para o cargo."
            ),
            error=True,
        )

    from app.domains.job_creation.internal.audit import _emit_wizard_step_audit
    _emit_wizard_step_audit(
        stage="competencies_confirm",
        state=state,
        before={
            "competencies_confirmed": bool(state.get("competencies_confirmed")),
            "confirmed_competencies": state.get("confirmed_competencies"),
        },
        after={
            "competencies_confirmed": True,
            "confirmed_competencies": {
                "technical": confirmed_technical,
                "behavioral": confirmed_behavioral,
            },
        },
        reasoning_extra=[
            f"Técnicas confirmadas: {len(confirmed_technical)}",
            f"Comportamentais confirmadas: {len(confirmed_behavioral)}",
        ],
        criteria_used=["recruiter_explicit_confirmation", "wizard_competency_review"],
    )

    tech_str = ", ".join(str(c) for c in confirmed_technical[:10]) or "(nenhuma)"
    behav_str = ", ".join(str(c) for c in confirmed_behavioral[:10]) or "(nenhuma)"

    return ToolResult(
        llm_message=(
            f"Competências confirmadas pelo recrutador.\n"
            f"Técnicas: {tech_str}\n"
            f"Comportamentais: {behav_str}"
        ),
        state_updates={
            "competencies_confirmed": True,
            "confirmed_competencies": {
                "technical": confirmed_technical,
                "behavioral": confirmed_behavioral,
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

    # ── T5: Learning loop — inject similar past JDs as context ──────────
    _company_context = state.get("company_context", "")
    _company_id_enrich = state.get("company_id") or (ctx.company_id if ctx else "")
    if _company_id_enrich and title:
        try:
            from app.domains.job_creation.helpers.async_audit import (
                run_coro_in_threadpool,
            )
            from app.core.database import AsyncSessionLocal
            from app.domains.job_creation.repositories.jd_similar_history_repository import (
                JdSimilarHistoryRepository,
            )
            from app.domains.job_creation.services.jd_similar_service import (
                JdSimilarService,
            )
            from app.shared.intelligence.embedding_service import EmbeddingService

            async def _fetch_similar_jds():
                async with AsyncSessionLocal() as _db:
                    _repo = JdSimilarHistoryRepository(_db)
                    _emb_svc = EmbeddingService()
                    _svc = JdSimilarService(repository=_repo, embedding_service=_emb_svc)
                    return await _svc.find_similar(
                        company_id=_company_id_enrich,
                        title=title,
                        department=department or None,
                        limit=3,
                    )

            _similar_jds = run_coro_in_threadpool(
                lambda: _fetch_similar_jds(), timeout=8,
            )
            if _similar_jds:
                _parts = []
                for _sj in _similar_jds:
                    _line = f"- **{_sj.get('title', '?')}**"
                    if _sj.get("department"):
                        _line += f" ({_sj['department']}"
                        if _sj.get("seniority_level"):
                            _line += f", {_sj['seniority_level']}"
                        _line += ")"
                    elif _sj.get("seniority_level"):
                        _line += f" ({_sj['seniority_level']})"
                    if _sj.get("was_filled"):
                        _fill = _sj.get("time_to_fill_days")
                        _cands = _sj.get("candidates_count", 0)
                        _line += f" — preenchida"
                        if _fill:
                            _line += f" em {_fill} dias"
                        if _cands:
                            _line += f", {_cands} candidatos"
                    sim = _sj.get("similarity")
                    if sim is not None:
                        _line += f" [similaridade: {sim:.0%}]"
                    _parts.append(_line)
                _similar_ctx = (
                    "\n\n## Vagas similares anteriores desta empresa\n"
                    + "\n".join(_parts)
                )
                _company_context = (_company_context + _similar_ctx) if _company_context else _similar_ctx.lstrip()
                logger.info(
                    "[WizardServiceTools:T5] Injected %d similar JDs into enrich context",
                    len(_similar_jds),
                )
        except Exception as exc:  # noqa: BLE001 — fail-soft (learning loop is non-critical)
            logger.warning(
                "[WizardServiceTools:T5] Similar JD fetch failed (continuing without): %s",
                str(exc)[:200],
            )

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
                company_context=_company_context,
            )
            enriched_obj, quality_score, warnings = _fut.result(timeout=_JD_TIMEOUT_S)
    except _cf.TimeoutError:  # REGRA-4-EXEMPT: fallback explícito — jd_enrichment_used_fallback=True no retorno
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
    except Exception as exc:  # noqa: BLE001  # REGRA-4-EXEMPT: fallback explícito — jd_enrichment_used_fallback=True + fallback_reason no retorno
        logger.warning("[WizardServiceTools] JD enrich failed (%s) — fallback", type(exc).__name__)
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
    except Exception:  # noqa: BLE001  # REGRA-4-EXEMPT: fallback de serialização defensivo — enriched_obj sempre é válido aqui
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

CONFIRM_COMPETENCIES = WizardTool(
    name="confirm_competencies",
    description=(
        "Registra a confirmação das competências pelo recrutador. "
        "Chame quando o recrutador aprovar ou ajustar as competências "
        "sugeridas por suggest_competencies."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "technical": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de competências técnicas confirmadas.",
            },
            "behavioral": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de competências comportamentais confirmadas.",
            },
        },
        "required": [],
    },
    handler=_handle_confirm_competencies,
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



async def _publish_job_fastapi(state: dict, company_id: str) -> dict:
    """FastAPI-native publish — substitui publish_node (RAILS_API_URL ausente).

    Cria JobVacancy com status=Ativa + persiste question_set WSI aprovado.
    Retorna {"job_id": str, "share_link": str}.
    """
    import hashlib as _hashlib
    import json as _json
    from app.core.database import AsyncSessionLocal
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCRUDRepository,
    )
    from app.domains.job_creation.helpers.vacancy_vocab import (
        to_canonical_work_model,
        to_canonical_seniority,
    )
    from libs.models.lia_models.job_vacancy import JobVacancy as _JobVacancyModel

    jd = state.get("jd_enriched") or {}
    title = jd.get("titulo_padronizado") or state.get("parsed_title") or "Nova Vaga"
    description = jd.get("about_role") or ""
    responsibilities = jd.get("responsabilidades") or []
    skills_obrigatorias = jd.get("skills_obrigatorias") or []
    department = state.get("parsed_department") or None
    location = state.get("parsed_location") or state.get("parsed_city") or None

    raw_seniority = state.get("parsed_seniority") or state.get("seniority_resolved") or None
    seniority = to_canonical_seniority(raw_seniority) if raw_seniority else None
    raw_work_model = state.get("parsed_work_model") or None
    work_model = to_canonical_work_model(raw_work_model) if raw_work_model else None

    salary_min = state.get("salary_min")
    salary_max = state.get("salary_max")
    salary_range = (
        {
            "min": salary_min,
            "max": salary_max,
            "currency": state.get("salary_currency") or "BRL",
        }
        if salary_min is not None or salary_max is not None
        else None
    )

    async with AsyncSessionLocal() as db:
        repo = JobVacancyCRUDRepository(db)
        # H1+H3+H4: identidade do recrutador/gestor, stakeholders e audit created_by.
        # Fonte unica: state (unica disponivel dentro de _publish_job_fastapi).
        # "anonymous" e "" sao filtrados — created_by=None significa "sem autor identificado".
        _uid = state.get("user_id") or ""
        vacancy = _JobVacancyModel(
            company_id=company_id,
            title=title,
            description=description,
            responsibilities=responsibilities if isinstance(responsibilities, list) else [],
            technical_requirements=skills_obrigatorias if isinstance(skills_obrigatorias, list) else [],
            department=department,
            location=location,
            seniority_level=seniority,
            work_model=work_model,
            salary_range=salary_range,
            status="Ativa",
            recruiter=state.get("parsed_recruiter_name") or "",
            recruiter_email=state.get("parsed_recruiter_email") or "",
            manager=state.get("parsed_manager_name") or "",
            manager_email=state.get("parsed_manager_email") or "",
            stakeholders=state.get("parsed_stakeholders") or [],
            created_by=_uid if _uid not in ("", "anonymous") else None,
            eligibility_questions=state.get("eligibility_questions") or [],
        )
        vacancy = await repo.create_vacancy(vacancy)
        job_id = str(vacancy.id)

        # Persiste question_set WSI aprovado (triagem lê desta tabela — evita
        # regeneração e descarta calibrações HITL do recrutador).
        questions = state.get("wsi_questions") or []
        if questions and state.get("questions_approved"):
            try:
                from app.domains.cv_screening.repositories.screening_question_set_repository import (
                    ScreeningQuestionSetRepository,
                )

                qs_repo = ScreeningQuestionSetRepository(db)
                questions_hash = _hashlib.sha256(
                    _json.dumps(questions, sort_keys=True, default=str).encode()
                ).hexdigest()[:32]
                block_dist: dict = {}
                for q in questions:
                    b = str(q.get("block") or "other")
                    block_dist[b] = block_dist.get(b, 0) + 1
                if not state.get("screening_mode"):
                    logger.warning(
                        "[WizardServiceTools] screening_mode ausente em publish (question_set) "
                        "— coercindo para 'compact'. Chamar set_screening_mode."
                    )
                await qs_repo.insert_set(
                    job_vacancy_id=job_id,
                    version=1,
                    questions_hash=questions_hash,
                    questions=questions,
                    questions_count=len(questions),
                    block_distribution=block_dist,
                    metadata={
                        "source": "wizard_orchestrator",
                        "mode": state.get("screening_mode") or "compact",
                    },
                    source="wizard_approved",
                    created_by=_uid if _uid not in ("", "anonymous") else None,
                    difficulty_coefficient=0.5,
                )
            except Exception as _qset_err:
                logger.warning(
                    "[publish_fastapi] question_set save failed — triagem regenerara: %s",
                    _qset_err,
                )

        await db.commit()

    # ── Fase A — calibration sourcing ──────────────────────────────────────
    # Executado FORA do async with (db já fechado); sourcing abre _src_db próprio.
    # _tenant_container NÃO propaga pelo run_coro_in_threadpool (ThreadPoolExecutor
    # + asyncio.run cria contexto isolado — confirmado empiricamente 2026-06-20).
    # LLM proibido neste path; query determinística rica é a primária.
    # V2: mover síntese LLM para acima do threadpool com copy_context().
    _cal_candidates: list = []
    _cal_fingerprint: str = ""
    _sourcing_ok: bool = False
    try:
        from app.domains.sourcing.services.pearch_service import (
            pearch_service as _pearch_svc,
        )
        from app.api.v1.candidate_search._shared import _generate_search_fingerprint
        from libs.models.lia_models.pearch import HybridSearchRequest as _HybridReq

        # A2 — query local limpa: tokens de título + senioridade + skills + work_model.
        # REGRA: sem prosa de responsabilidades — geram stopwords 'do'/'de' que casam
        #        em 'Advogado'/'Coordenador' via ILIKE OR (bug pré-D2 confirmado).
        # REGRA: space-join, não ', '.join — vírgulas produziam tokens 'python,' que
        #        nunca casavam em nenhuma coluna do DB.
        # Responsabilidades já vão para Pearch via search_spec.required_skills.
        # D2-NOTE: location fora do query (ILIKE OR corromperia ranking — removida).
        _jd_title = jd.get("titulo_padronizado") or state.get("parsed_title") or ""
        _jd_seniority = (
            state.get("seniority_resolved") or state.get("parsed_seniority") or ""
        )
        _jd_work_model = state.get("parsed_work_model") or ""
        _jd_skills = [
            (x.get("skill", "") if isinstance(x, dict) else str(x))
            for x in (jd.get("skills_obrigatorias") or [])
            if x
        ]
        # Tokens limpos: palavras individuais, strip de pontuacao, sem stopwords <= 2 chars
        _raw_terms = (
            [_jd_title, _jd_seniority]
            + _jd_skills[:5]
            + ([_jd_work_model] if _jd_work_model else [])
        )
        _PUNCT = ',.;:()"\''
        _clean_words = [
            w.strip(_PUNCT)
            for part in _raw_terms if part
            for w in part.split()
            if len(w.strip(_PUNCT)) > 2
        ]
        _search_query = " ".join(_clean_words) or "profissional"

        # A4 — fingerprint: mesmo _generate_search_fingerprint de candidate_search._shared
        # que apply_feedback_boost usa -> boost da Fase C funciona com este fingerprint
        _cal_fingerprint = _generate_search_fingerprint(
            _search_query, {"job_id": job_id, "source": "wizard_calibration_v1"}
        )

        # A1 — sourcing_mode: "local" (default) -> include_pearch=False
        _sourcing_mode = state.get("sourcing_mode") or "local"
        _include_pearch = _sourcing_mode != "local"

        # D2 — search_spec: location, seniority, work_model, skills, languages -> Pearch
        from app.domains.job_creation.helpers.search_spec_builder import (
            build_search_spec_from_jd as _build_search_spec,
        )
        _search_spec = _build_search_spec(jd, state) or None

        # A3 — busca real: 5 candidatos (amostra de calibração; sample 3-10)
        async with AsyncSessionLocal() as _src_db:
            _search_req = _HybridReq(
                query=_search_query,
                search_spec=_search_spec,
                search_local_first=True,
                include_pearch=_include_pearch,
                local_limit=5,
                pearch_limit=5 if _include_pearch else 0,
                require_emails=True,
                show_emails=False,
                exclude_candidate_ids=[],
            )
            _search_resp = await _pearch_svc.hybrid_search(_src_db, _search_req)

        # A5 — adapter CandidateProfile -> CalibrationCandidate + extras FE
        _cal_candidates = [
            {
                "id": p.docid or "",
                "name": (
                    p.name
                    or f"{p.first_name or ''} {p.last_name or ''}".strip()
                    or ""
                ),
                "current_title": p.current_title or getattr(p, "title", "") or "",
                "current_company": p.current_company or "",
                "match_score": p.get_score_percentage() / 100.0,
                "match_criteria": [{"criterion": s, "score": 1.0, "met": True} for s in (p.skills or [])[:5]],
                "decision": None,
                "reason": None,
                "avatar_url": p.picture_url or None,
                "auto_tags": list((p.skills or p.expertise or [])[:3]),
                "has_email": True,
                "snapshot_skills": list(p.skills or []),
            }
            for p in _search_resp.get_all_candidates()
            if (p.docid or "").strip()
        ]
        _sourcing_ok = True
        logger.info(
            "[publish_fastapi] calibration sourcing ok: query=%r mode=%s total=%d (local=%d pearch=%d)",
            _search_query,
            _sourcing_mode,
            len(_cal_candidates),
            _search_resp.local_count,
            _search_resp.pearch_count,
        )
    except Exception as _src_err:
        logger.error(
            "[publish_fastapi] calibration sourcing FALHOU — candidates=[]: %s",
            _src_err,
            exc_info=True,
        )

    return {
        "job_id": job_id,
        "share_link": f"/pt/jobs/{job_id}",
        "calibration_candidates": _cal_candidates,
        "calibration_search_fingerprint": _cal_fingerprint,
        "sourcing_ok": _sourcing_ok,
    }



# ── publish_job ──────────────────────────────────────────────────────────


def _handle_publish_job(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Publica a vaga (AÇÃO IRREVERSÍVEL) via _publish_job_fastapi (FastAPI-native).

    Gate de confirmação: exige ``confirm=true`` no tool_input. Sem confirmação
    explícita, NÃO publica — instrui o LLM a obter o "sim" do recrutador. Com
    confirmação, chama ``_publish_job_fastapi`` (via run_coro_in_threadpool):
    cria a vaga no banco FastAPI + persiste question_set WSI aprovado.
    Pré-requisito: JD gerada, aprovada e WSI aprovado.
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
        from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool
        _cid = ctx.company_id or state.get("company_id") or ""
        result = run_coro_in_threadpool(
            lambda: _publish_job_fastapi(dict(state), _cid),
            timeout=60.0,
        )
    except Exception as exc:  # noqa: BLE001 — fail-loud
        logger.warning("[WizardServiceTools] publish_fastapi failed: %s", exc)
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

    _sourcing_note = (
        " (Não foi possível buscar candidatos automaticamente — "
        "o painel de calibração estará vazio.)"
        if not result.get("sourcing_ok", True)
        else ""
    )
    share_part = f" Link: {share_link}." if share_link else ""
    return ToolResult(
        llm_message=(
            f"Vaga publicada! ID {job_id}.{share_part}{_sourcing_note} "
            "Oriente o recrutador a avaliar os candidatos no painel de "
            "calibração que abriu ao lado — ele pode aprovar, rejeitar ou pular cada um."
        ),
        state_updates={
            "job_id": job_id,
            "job_uid": result.get("job_uid"),
            "share_link": share_link,
            "current_stage": "calibration",
            "calibration_candidates": result.get("calibration_candidates") or [],
            "calibration_search_fingerprint": result.get("calibration_search_fingerprint") or "",
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

    _raw_mode = state.get("screening_mode")
    if not _raw_mode:
        logger.warning(
            "[WizardServiceTools] screening_mode ausente em _wsi_distribution_status "
            "— coercindo para 'compact'. Chamar set_screening_mode."
        )
    mode = (_raw_mode or "compact").lower()
    seniority = (
        state.get("seniority_resolved") or state.get("parsed_seniority") or "pleno"
    ).lower()
    try:
        from app.domains.job_creation.graph import _get_question_distribution
        expected = _get_question_distribution(mode, seniority) or {}
        min_tech = int(expected.get("technical", 0))
        min_behavioral = int(expected.get("behavioral", 0))
    except Exception:  # noqa: BLE001  # REGRA-4-EXEMPT: fail-open intencional — gate nunca trava por erro de lookup de tabela de distribuição
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

    # Gate computacional (#2 audit 2026-06-05 — enforced Fase 4): o MODO de
    # triagem (compact/full) NAO pode ser escolhido pelo sistema silenciosamente.
    # Fase 4: fail-closed incondicional — force_regen sem mode definido tambem
    # retorna error=True roteando o LLM a CHAMAR set_screening_mode (auto-cura).
    if not state.get("screening_mode"):
        return ToolResult(
            llm_message=(
                "O modo de triagem WSI nao esta definido. CHAME set_screening_mode "
                "antes de gerar as perguntas: "
                "set_screening_mode(mode='compact') para 7 perguntas (~10 min) ou "
                "set_screening_mode(mode='full') para 12 perguntas (~18 min). "
                "Se o recrutador ja indicou preferencia, use essa; caso contrario, "
                "pergunte e depois chame set_screening_mode."
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
    mode = state.get("screening_mode")  # garantido pelo guard acima

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
    _raw_mode = state.get("screening_mode")
    if not _raw_mode:
        logger.warning(
            "[WizardServiceTools] screening_mode ausente em add_wsi_question "
            "— coercindo para 'compact'. Chamar set_screening_mode."
        )
    _mode = str(_raw_mode or "compact").strip().lower()
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
    # Emite close_panel via SSE sink para fechar o painel lateral WSI
    # apos aprovacao bem-sucedida (mesmo padrao de _handle_close_panel).
    # FE chain: ui_action="close_panel" -> useUIAction.ts -> lia:close_panel
    # -> lia-float-context.tsx handleClosePanel -> closeDynamicPanel().
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
    except Exception:  # noqa: BLE001 -- best-effort, nunca bloqueia a aprovacao
        logger.debug("[WizardTool] approve_wsi close_panel SSE emit failed", exc_info=True)

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


# ─── Fairness guard para perguntas de elegibilidade ─────────────────────────
_FAIRNESS_ELIGIBILITY_REPLY = (
    "Esta pergunta contém critério discriminatório e não pode ser usada como pergunta "
    "de triagem. Por favor, reformule para focar em requisitos técnicos ou de experiência."
)


def _check_question_fairness(question_text: str):
    """Retorna ToolResult bloqueante se FairnessGuard detectar texto discriminatório.

    Fail-closed: exception do guard também bloqueia (fail-loud com logger.error).
    Retorna None se o texto for aprovado pelo guard.
    """
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard  # local: evita circular
        fg = FairnessGuard().check(question_text)
        if fg.is_blocked:
            logger.warning(
                "[WizardServiceTools] FairnessGuard BLOCK eligibility cat=%s q=%r",
                fg.category,
                question_text[:80],
            )
            return ToolResult(
                llm_message=(
                    f"Pergunta bloqueada (critério discriminatório — {fg.category}): "
                    f"{fg.educational_message or _FAIRNESS_ELIGIBILITY_REPLY}"
                ),
                error=True,
            )
    except Exception:
        logger.error(
            "[WizardServiceTools] FairnessGuard check falhou em pergunta de elegibilidade",
            exc_info=True,
        )
        return ToolResult(
            llm_message="Verificação de compliance indisponível. Tente novamente em instantes.",
            error=True,
        )
    return None


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

    snapshot_question = (
        snapshot.get("question") or snapshot.get("question_text") or ""
    ).strip()
    if snapshot_question:
        fairness_block = _check_question_fairness(snapshot_question)
        if fairness_block:
            return fairness_block

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

    fairness_block = _check_question_fairness(question)
    if fairness_block:
        return fairness_block

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





# ── confirm_skip_eligibility (Bug 5 — Fase 7) ───────────────────────────

def _handle_confirm_skip_eligibility(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Registra a decisão explícita de prosseguir SEM critérios de elegibilidade.

    Grava ``eligibility_skip_confirmed=True`` no state e emite audit row
    via ``_emit_wizard_step_audit`` (caminho existente — EU AI Act Art.13).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    current_qs = list(state.get("eligibility_questions") or [])
    if current_qs:
        return ToolResult(
            llm_message=(
                f"Já existem {len(current_qs)} critério(s) de elegibilidade configurados. "
                "Esta tool é para confirmar avanço SEM critérios."
            ),
            error=True,
        )

    reason = tool_input.get("reason", "").strip()

    from app.domains.job_creation.internal.audit import _emit_wizard_step_audit
    _emit_wizard_step_audit(
        stage="eligibility_skip",
        state=state,
        before={"eligibility_questions": [], "eligibility_skip_confirmed": False},
        after={"eligibility_questions": [], "eligibility_skip_confirmed": True},
        reasoning_extra=[
            "Recrutador confirmou explicitamente: avançar sem critérios de elegibilidade.",
            f"Motivo informado: {reason or '(nenhum)'}",
        ],
        criteria_used=["recruiter_explicit_confirmation", "wizard_eligibility_gate"],
        human_review_required=False,
    )

    return ToolResult(
        llm_message=(
            "Decisão registrada: prosseguir sem critérios de elegibilidade. "
            "Este registro fica na trilha de auditoria da vaga."
        ),
        state_updates={"eligibility_skip_confirmed": True},
    )


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
        from app.domains.job_creation.helpers.manager_briefing import (
            build_manager_briefing_html,
        )
        body_html = build_manager_briefing_html(state)

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


CONFIRM_SKIP_ELIGIBILITY = WizardTool(
    name="confirm_skip_eligibility",
    description=(
        "Registra a decisão explícita do recrutador de avançar SEM nenhum "
        "critério de elegibilidade. Chame SOMENTE quando o recrutador "
        "confirmar que deseja prosseguir sem perguntas eliminatórias."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Motivo informado pelo recrutador para pular elegibilidade (opcional).",
            },
        },
        "required": [],
    },
    handler=_handle_confirm_skip_eligibility,
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



# -- suggest_managers ---------------------------------------------------------

def _handle_suggest_managers(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    _reject_tenant_keys(tool_input)

    company_id = ctx.company_id
    if not company_id:
        return ToolResult(
            llm_message="Empresa nao identificada -- nao consigo buscar gestores.",
            error=True,
        )

    department = state.get("parsed_department") or state.get("department") or ""

    async def _fetch():
        from app.domains.company.services.manager_inference_service import ManagerInferenceService
        svc = ManagerInferenceService()
        if department:
            return await svc.get_managers_by_department(
                department_name=department,
                company_id=str(company_id),
            )
        return await svc.list_managers(company_id=str(company_id), limit=20)

    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool
    try:
        managers = run_coro_in_threadpool(lambda: _fetch(), timeout=10)
    except Exception as exc:
        logger.warning("[WizardServiceTools] suggest_managers failed: %s", exc)
        return ToolResult(
            llm_message=(
                "Nao consegui carregar os gestores agora. "
                "Oriente o recrutador a informar o gestor manualmente."
            ),
            error=True,
        )

    if not managers:
        return ToolResult(
            llm_message=(
                "Nenhum gestor encontrado"
                + (f" para o departamento {department!r}" if department else "")
                + ". O recrutador pode informar o gestor manualmente."
            ),
            state_updates={"suggested_managers": []},
        )

    result_list = []
    for m in managers:
        if isinstance(m, dict):
            result_list.append(m)
        else:
            result_list.append({
                "id": str(getattr(m, "id", "")),
                "name": getattr(m, "name", "") or getattr(m, "full_name", ""),
                "email": getattr(m, "email", ""),
                "role": getattr(m, "role", ""),
                "department_name": getattr(m, "department_name", ""),
            })

    names = [m.get("name", "") for m in result_list[:5]]
    summary = ", ".join(names) + (f" e mais {len(result_list)-5}" if len(result_list) > 5 else "")
    dept_ctx = f" do departamento {department!r}" if department else ""
    return ToolResult(
        llm_message=(
            f"Encontrei {len(result_list)} gestor(es){dept_ctx}: {summary}. "
            "Qual deles sera o gestor desta vaga?"
        ),
        state_updates={"suggested_managers": result_list},
    )


SUGGEST_MANAGERS = WizardTool(
    name="suggest_managers",
    description=(
        "Busca e sugere gestores disponiveis na empresa para a vaga. "
        "Use quando o recrutador precisar escolher ou confirmar o gestor da vaga, "
        "especialmente durante o intake ou apos definir o departamento. "
        "Prioriza gestores do mesmo departamento. Retorna lista com nome, email e cargo."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_suggest_managers,
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
        from app.core.database import AsyncSessionLocal
        from app.domains.company.repositories.benefit_repository import BenefitRepository
        from uuid import UUID
        async with AsyncSessionLocal() as db:
            repo = BenefitRepository(db)
            try:
                cid = UUID(str(company_id))
            except ValueError:
                return []
            return await repo.list_active_for_company(cid)

    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool  # noqa: PLC0415
    try:
        benefits_orm = run_coro_in_threadpool(lambda: _fetch(), timeout=10)
    except Exception as exc:
        logger.warning("[WizardServiceTools] suggest_benefits failed: %s", exc)
        return ToolResult(
            llm_message=(
                "Não consegui carregar o catálogo de benefícios agora. "
                "Oriente o recrutador a informar os benefícios manualmente."
            ),
            error=True,
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
        from app.core.database import AsyncSessionLocal
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

    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool  # noqa: PLC0415
    try:
        matched = run_coro_in_threadpool(lambda: _fetch(), timeout=10)
    except Exception as exc:
        logger.warning("[WizardServiceTools] suggest_variable_compensation failed: %s", exc)
        return ToolResult(
            llm_message=(
                "Não consegui carregar o catálogo de verbas variáveis agora. "
                "Oriente o recrutador a informar os componentes manualmente."
            ),
            error=True,
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

    masked_company_name = tool_input.get("masked_company_name")
    if masked_company_name is not None:
        val = str(masked_company_name).strip()
        if len(val) < 2 or len(val) > 120:
            errors.append("masked_company_name deve ter entre 2 e 120 caracteres")
        else:
            updates["masked_company_name"] = val

    visibility = tool_input.get("visibility")
    _VALID_VISIBILITY = {"public", "internal", "unlisted"}
    if visibility is not None:
        if visibility not in _VALID_VISIBILITY:
            errors.append(f"visibility invalido: {visibility!r}. Valores aceitos: public, internal, unlisted")
        else:
            updates["visibility"] = visibility

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
            "masked_company_name": {
                "type": "string",
                "description": "Nome mascarado da empresa quando is_confidential=True (ex: empresa de tecnologia de medio porte)",
            },
            "visibility": {
                "type": "string",
                "enum": ["public", "internal", "unlisted"],
                "description": "Visibilidade da vaga: public (padrao), internal (apenas colaboradores), unlisted (link direto)",
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
    _raw_mode = state.get("screening_mode")
    if not _raw_mode:
        logger.warning(
            "[WizardServiceTools] screening_mode ausente em add_bank_question "
            "— coercindo para 'compact'. Chamar set_screening_mode."
        )
    _mode = str(_raw_mode or "compact").strip().lower()
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

# ---------------------------------------------------------------------------
# T11 — Infer Department from Title (DB-backed fuzzy match)
# ---------------------------------------------------------------------------


def _handle_infer_department(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Infere o departamento a partir do titulo da vaga, usando fuzzy match
    contra os departamentos REAIS da empresa (DepartmentRepository).

    SERVICE_TOOL: precisa de DB access (via run_coro_in_threadpool) para
    buscar departamentos do tenant. Mantido fora de wizard_tools.py (PURE).
    """
    _reject_tenant_keys(tool_input)

    title = state.get("parsed_title") or state.get("title") or ""
    if not title:
        return ToolResult(
            llm_message=(
                "Nenhum titulo definido ainda. Defina primeiro com "
                "set_job_fields antes de inferir o departamento."
            ),
            error=True,
        )

    # Skip se departamento ja foi setado pelo recrutador
    existing_dept = state.get("parsed_department") or ""
    if existing_dept:
        return ToolResult(
            llm_message=(
                f"Departamento ja definido: '{existing_dept}'. "
                "Se quiser alterar, use set_job_fields com department=novo_valor."
            ),
        )

    company_id = ctx.company_id
    if not company_id:
        return ToolResult(
            llm_message="Empresa nao identificada. Nao consigo buscar departamentos.",
            error=True,
        )

    # Fetch departamentos ativos da empresa via repo canonical
    try:
        from app.domains.job_creation.helpers.async_audit import (
            run_coro_in_threadpool,
        )
        from app.core.database import AsyncSessionLocal
        from app.domains.company.repositories.department_repository import (
            DepartmentRepository,
        )
        from uuid import UUID as _UUID

        async def _fetch_departments():
            async with AsyncSessionLocal() as _db:
                repo = DepartmentRepository(_db)
                try:
                    cid = _UUID(str(company_id))
                except ValueError:
                    return []
                return await repo.list_active_for_company(cid)

        depts_orm = run_coro_in_threadpool(
            lambda: _fetch_departments(), timeout=5,
        )
    except Exception as exc:
        logger.warning(
            "[WizardServiceTools] infer_department fetch failed: %s", exc,
        )
        return ToolResult(
            llm_message=(
                "Erro ao buscar departamentos da empresa. "
                "Pergunte o departamento diretamente ao recrutador."
            ),
            error=True,
        )

    dept_names = [d.name for d in depts_orm if d.name]
    if not dept_names:
        return ToolResult(
            llm_message=(
                "A empresa nao tem departamentos cadastrados. "
                "Pergunte o departamento diretamente ao recrutador."
            ),
        )

    # Fuzzy match usando a mesma logica de intake.py (single source of truth)
    from app.domains.job_creation.nodes.intake import _match_department

    matched = _match_department(title, dept_names, threshold=0.7)

    if matched:
        return ToolResult(
            llm_message=(
                f"Inferi departamento '{matched}' pelo titulo '{title}'. "
                "Confirme com o recrutador ou ajuste com set_job_fields."
            ),
            state_updates={"parsed_department": matched},
        )

    # Sem match — listar departamentos disponiveis para o LLM perguntar
    display = ", ".join(dept_names[:15])
    suffix = f" (e mais {len(dept_names) - 15})" if len(dept_names) > 15 else ""
    return ToolResult(
        llm_message=(
            f"Nao consegui inferir o departamento pelo titulo '{title}'. "
            f"Departamentos da empresa: {display}{suffix}. "
            "Pergunte ao recrutador em qual departamento a vaga se encaixa."
        ),
    )


INFER_DEPARTMENT = WizardTool(
    name="infer_department_from_title",
    description=(
        "Infere o departamento da vaga a partir do titulo, usando fuzzy match "
        "contra os departamentos REAIS cadastrados na empresa. Chame apos "
        "definir o titulo com set_job_fields, quando o departamento ainda nao "
        "foi informado. Se a confianca for alta, sugira ao recrutador; senao, "
        "liste os departamentos disponiveis e pergunte."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    handler=_handle_infer_department,
)




# ---------------------------------------------------------------------------
# T10 — Set Stakeholders (envolvidos adicionais)
# ---------------------------------------------------------------------------

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_VALID_STAKEHOLDER_ROLES = {
    "ta_lead", "area_manager", "area_director", "technical_interviewer",
    "hr_bp", "dept_head", "committee_member", "interviewer", "other",
}


def _handle_calibration_action(state: dict, args: dict, ctx: "ToolContext") -> ToolResult:
    """Bug 13: registra decisão do recrutador sobre candidato na calibração.

    Threshold: like + dislike contam; skip NÃO conta (decisão 2026-06-19).
    can_advance é nudge — NÃO seta calibration_complete (sem auto-eject).
    """
    candidate_id = (args.get("candidate_id") or "").strip()
    signal = (args.get("signal") or "").strip()
    reason = args.get("reason")

    if not candidate_id:
        return ToolResult(
            llm_message="candidate_id é obrigatório para registrar ação de calibração.",
            state_updates={},
            error=True,
        )

    _VALID_SIGNALS = {"like", "dislike", "skip"}
    if signal not in _VALID_SIGNALS:
        return ToolResult(
            llm_message=f"signal inválido: {signal!r}. Valores aceitos: like, dislike, skip.",
            state_updates={},
            error=True,
        )

    _SIGNAL_TO_DECISION = {"like": "approved", "dislike": "rejected", "skip": "skip"}
    decision = _SIGNAL_TO_DECISION[signal]

    candidates = list(state.get("calibration_candidates") or [])
    updated = False
    for c in candidates:
        if str(c.get("id", "")) == candidate_id or str(c.get("candidate_id", "")) == candidate_id:
            c["decision"] = decision
            if reason:
                c["recruiter_decision_reason"] = reason
            updated = True
            break

    if not updated:
        return ToolResult(
            llm_message=f"Candidato {candidate_id!r} não encontrado na lista de calibração.",
            state_updates={},
            error=True,
        )

    threshold = state.get("calibration_threshold", 5)
    # like e dislike contam; skip NÃO (decisão Paulo 2026-06-19)
    signal_count = sum(1 for c in candidates if c.get("decision") in ("approved", "rejected"))
    can_advance = signal_count >= threshold

    _action_label = {"approved": "aprovado", "rejected": "rejeitado", "skip": "pulado"}[decision]
    msg = f"Candidato {candidate_id} {_action_label}. Sinais registrados: {signal_count}/{threshold}."
    if can_advance:
        msg += " Mínimo atingido — recrutador pode avançar."

    # ── Fase B — persistir like/dislike em SearchFeedback (skip não persiste) ────
    # Reutiliza _persist_search_feedback_internal (feedback.py) — fonte única de
    # escrita em SearchFeedback. feedback_type=signal ("like"/"dislike") — é isso
    # que apply_feedback_boost lê. ctx.company_id/user_id chegam diretamente (não ContextVar).
    _fb_persist_error = False
    if signal in ("like", "dislike"):
        from app.core.database import AsyncSessionLocal as _FBSL
        from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool as _rcitp
        from app.api.v1.candidate_search.feedback import (
            _persist_search_feedback_internal as _psfb,
        )

        _fingerprint = state.get("calibration_search_fingerprint") or ""
        _job_id_fb = state.get("job_id") or ""
        _cand_dict = next(
            (c for c in candidates if str(c.get("id", "")) == candidate_id), {}
        )
        _cand_name_fb: "str | None" = _cand_dict.get("name") or None
        _cand_score_raw = _cand_dict.get("match_score")
        _cand_score_fb: "float | None" = (
            float(_cand_score_raw) if _cand_score_raw is not None else None
        )
        _company_id_fb = ctx.company_id
        _user_id_fb = ctx.user_id or ""

        async def _persist_calibration_signal() -> None:
            async with _FBSL() as _fb_db:
                await _psfb(
                    _fb_db,
                    company_id=_company_id_fb,
                    user_id=_user_id_fb,
                    candidate_id=candidate_id,
                    feedback_type=signal,
                    job_id=_job_id_fb or None,
                    candidate_score=_cand_score_fb,
                    candidate_name=_cand_name_fb,
                    search_fingerprint=_fingerprint or None,
                    reason=reason,
                )
                await _fb_db.commit()

        try:
            _rcitp(lambda: _persist_calibration_signal(), timeout=5.0)
            logger.info(
                "[calibration_action] SearchFeedback persisted: "
                "candidate=%s signal=%s fingerprint=%s",
                candidate_id, signal, _fingerprint or "(none)",
            )
        except Exception as _fb_err:
            _fb_persist_error = True
            logger.error(
                "[calibration_action] SearchFeedback persist FALHOU — "
                "boost Fase C pode ser afetado: candidate=%s signal=%s err=%s",
                candidate_id, signal, _fb_err, exc_info=True,
            )

    _state_updates: dict = {
        "calibration_candidates": candidates,
        "can_advance": can_advance,
    }
    if _fb_persist_error:
        _state_updates["calibration_feedback_persist_error"] = True

    return ToolResult(llm_message=msg, state_updates=_state_updates)



def _handle_advance_calibration(state: dict, args: dict, ctx: "ToolContext") -> ToolResult:
    """Fase C: valida sinais, adiciona aprovados à vaga, sinaliza navigate_to.

    ÚNICO setter de calibration_complete — separa nudge (can_advance)
    de ejeção (calibration_complete). Acionado por [calibration_complete].
    """
    candidates = state.get("calibration_candidates") or []
    threshold = state.get("calibration_threshold", 5)
    signal_count = sum(
        1 for c in candidates if c.get("decision") in ("approved", "rejected")
    )

    # STEP 1 — fail-loud se sinais insuficientes
    if signal_count < threshold:
        return ToolResult(
            llm_message=(
                f"Avalie ao menos {threshold} candidatos antes de avançar "
                f"({signal_count}/{threshold} avaliados). "
                "Aprovação e rejeição contam; pular não conta."
            ),
            error=True,
        )

    job_id = state.get("job_id") or ""
    company_id = ctx.company_id or ""
    approved_ids = [c["id"] for c in candidates if c.get("decision") == "approved"]
    approved_count = len(approved_ids)

    # STEP 2 — adicionar aprovados à vaga (deduped, sem busca, <1 s)
    _add_error = False
    if approved_ids and job_id:
        from app.core.database import AsyncSessionLocal as _FBSL
        from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool as _rcitp
        from app.api.v1.candidate_search.calibration import (
            _add_candidates_to_vacancy_internal as _add_internal,
        )

        _cids = list(approved_ids)
        _jid = job_id
        _coid = company_id

        async def _add_approved() -> None:
            async with _FBSL() as _add_db:
                await _add_internal(
                    db=_add_db,
                    job_id=_jid,
                    company_id=_coid,
                    candidate_ids=_cids,
                    source="calibration_wizard",
                    with_rubric=False,
                )
                await _add_db.commit()

        try:
            _rcitp(lambda: _add_approved(), timeout=5.0)
            logger.info(
                "[advance_calibration] %d aprovado(s) adicionado(s) à vaga %s",
                approved_count, job_id,
            )
        except Exception as _add_err:
            _add_error = True
            logger.error(
                "[advance_calibration] add_approved FALHOU: job=%s err=%s",
                job_id, _add_err, exc_info=True,
            )

    # STEP 3 — sinalizar handoff
    n = approved_count
    msg = (
        f"Calibração concluída! "
        + (f"{n} candidato(s) aprovado(s) adicionado(s) à vaga. " if n else "")
        + "Abrindo a vaga..."
    )
    state_updates: dict = {
        "calibration_complete": True,
        "_navigate_to_search": True,
    }
    if _add_error:
        state_updates["calibration_add_error"] = True

    return ToolResult(llm_message=msg, state_updates=state_updates)


def _handle_set_stakeholders(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Define os stakeholders/envolvidos adicionais da vaga.

    Aceita lista de {name, email, role?}. Valida emails e roles.
    Multi-tenancy: company_id proibido no input (sempre do ctx).
    """
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)

    raw_stakeholders = tool_input.get("stakeholders")
    if not raw_stakeholders or not isinstance(raw_stakeholders, list):
        return ToolResult(
            llm_message="stakeholders deve ser uma lista com ao menos 1 envolvido.",
            error=True,
        )

    if len(raw_stakeholders) > 20:
        return ToolResult(
            llm_message="Maximo de 20 stakeholders por vaga.",
            error=True,
        )

    validated = []
    errors = []
    for i, item in enumerate(raw_stakeholders):
        if not isinstance(item, dict):
            errors.append(f"stakeholders[{i}] deve ser um objeto")
            continue
        name = (item.get("name") or "").strip()
        email = (item.get("email") or "").strip().lower()
        role = (item.get("role") or "other").strip().lower()

        if not name or len(name) < 2:
            errors.append(f"stakeholders[{i}].name obrigatorio (min 2 chars)")
            continue
        if not email or not _EMAIL_PATTERN.match(email):
            errors.append(f"stakeholders[{i}].email invalido: {email!r}")
            continue
        if role not in _VALID_STAKEHOLDER_ROLES:
            errors.append(
                f"stakeholders[{i}].role invalido: {role!r}. "
                f"Aceitos: {sorted(_VALID_STAKEHOLDER_ROLES)}"
            )
            continue
        validated.append({"name": name, "email": email, "role": role})

    if errors:
        return ToolResult(llm_message="; ".join(errors), error=True)

    if not validated:
        return ToolResult(
            llm_message="Nenhum stakeholder valido fornecido.",
            error=True,
        )

    # Build confirmation message
    role_labels = {
        "ta_lead": "Lider de Recrutamento",
        "area_manager": "Gestor da Area",
        "area_director": "Diretor da Area",
        "technical_interviewer": "Entrevistador Tecnico",
        "hr_bp": "HRBP",
        "dept_head": "Lider de Area",
        "committee_member": "Comite",
        "interviewer": "Entrevistador",
        "other": "Outro",
    }
    parts = []
    for s in validated:
        label = role_labels.get(s["role"], s["role"])
        parts.append(f"- {s['name']} ({s['email']}) — {label}")
    listing = "\n".join(parts)

    return ToolResult(
        llm_message=(
            f"Stakeholders registrados ({len(validated)}):\n{listing}\n\n"
            "Esses envolvidos receberao notificacoes sobre a vaga."
        ),
        state_updates={"parsed_stakeholders": validated},
    )


SET_STAKEHOLDERS = WizardTool(
    name="set_stakeholders",
    description=(
        "Define os stakeholders/envolvidos adicionais da vaga (alem do gestor e "
        "recrutador). Exemplos: HRBP, lider de area, membro de comite de "
        "contratacao, entrevistador. Use quando o recrutador mencionar outras "
        "pessoas envolvidas no processo seletivo."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "stakeholders": {
                "type": "array",
                "description": "Lista de envolvidos adicionais",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nome completo"},
                        "email": {"type": "string", "description": "Email profissional"},
                        "role": {
                            "type": "string",
                            "enum": ["ta_lead", "area_manager", "area_director", "technical_interviewer", "hr_bp", "dept_head", "committee_member", "interviewer", "other"],
                            "description": "Papel: ta_lead (Lider de Recrutamento), area_manager (Gestor da Area), area_director (Diretor da Area), technical_interviewer (Entrevistador Tecnico), hr_bp (HRBP), committee_member (Comite), other (Outro)",
                        },
                    },
                    "required": ["name", "email"],
                },
            },
        },
        "required": ["stakeholders"],
        "additionalProperties": False,
    },
    handler=_handle_set_stakeholders,
)

CALIBRATION_ACTION = WizardTool(
    name="calibration_action",
    description=(
        "Registra a decisão do recrutador sobre um candidato na etapa de calibração. "
        "Use quando receber a mensagem estruturada "
        "[calibration_action candidate_id=ID signal=SIGNAL]. "
        "signal: like=aprovar, dislike=rejeitar, skip=pular (skip não conta para o threshold). "
        "Após chamar, relate o progresso (sinais: N/threshold)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "candidate_id": {
                "type": "string",
                "description": "ID do candidato (extrair EXATAMENTE do marcador)",
            },
            "signal": {
                "type": "string",
                "enum": ["like", "dislike", "skip"],
                "description": "like=aprovar, dislike=rejeitar, skip=pular",
            },
            "reason": {
                "type": "string",
                "description": "Motivo (opcional)",
            },
        },
        "required": ["candidate_id", "signal"],
        "additionalProperties": False,
    },
    handler=_handle_calibration_action,
)

ADVANCE_CALIBRATION = WizardTool(
    name="advance_calibration",
    description=(
        "Confirma conclusão da etapa de calibração e avança para handoff. "
        "Chamar quando receber a mensagem [calibration_complete]. "
        "NÃO chamar sem que o recrutador tenha clicado em Avançar."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    handler=_handle_advance_calibration,
)


SERVICE_TOOLS: tuple[WizardTool, ...] = (
    SUGGEST_COMPETENCIES,
    CONFIRM_COMPETENCIES,
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
    CONFIRM_SKIP_ELIGIBILITY,
    SUGGEST_MANAGERS,
    SEND_MANAGER_BRIEFING,
    SUGGEST_BENEFITS,
    SUGGEST_VARIABLE_COMPENSATION,
    SET_OPERATIONAL_FIELDS,
    ADD_BANK_QUESTION,
    SET_AFFIRMATIVE_FIELDS,
    INFER_DEPARTMENT,
    SET_STAKEHOLDERS,
    CALIBRATION_ACTION,
    ADVANCE_CALIBRATION,
    CLOSE_PANEL,
)
