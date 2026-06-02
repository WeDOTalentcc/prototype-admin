"""Candidate search route: POST /candidates"""
import asyncio
import time as _time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._shared import (
    CVParserService,
    CandidateProfile,
    CandidateSearchResultDTO,
    EducationDTO,
    EvaluateForJobRequest,
    EvaluateForJobResponse,
    EvaluateForJobResult,
    ExperienceDTO,
    HybridSearchRequest,
    IdMapping,
    ImportCandidateDTO,
    ImportCandidateExperienceDTO,
    ImportCandidatesRequest,
    ImportCandidatesResponse,
    ImportUser,
    JobRequirement,
    JobRequirementCreate,
    LanguageDTO,
    PearchService,
    PearchSearchRequest,
    RubricEvaluationService,
    SearchRequestDTO,
    SearchResponseDTO,
    SearchType,
    User,
    _build_candidate_data_from_dto,
    _evaluate_candidates_with_rubrics,
    _generate_fingerprint,
    _generate_search_fingerprint,
    _get_job_requirements,
    _get_match_label,
    _normalize_name,
    _normalize_priority,
    assert_resource_ownership,
    enrich_and_filter_candidates,
    get_current_user_or_demo,
    get_cv_parser_service,
    get_db,
    get_pearch_service,
    get_rubric_evaluation_service,
    get_user_company_id,
    logger,
    rubric_evaluation_service,
)
from app.domains.credits.services.credit_service import CreditService, get_credit_service
from app.domains.sourcing.services.apify_search_service import (
    APIFY_SEARCH_FALLBACK_ENABLED,
    apify_search_service,
)
from app.shared.resilience.circuit_breaker import (
    APIFY_SEARCH_CIRCUIT,
    CircuitBreakerError,
    CircuitState,
    PEARCH_CIRCUIT,
    get_degraded_response,
)
from app.shared.security.require_company_id import require_company_id
from ._persist import (
    _persist_pearch_profiles_best_effort,
    get_suppression_docids,
)

router = APIRouter()

async def _evaluate_candidates_with_rubrics(
    candidates: list["CandidateSearchResultDTO"],
    requirements: list[JobRequirementCreate],
    rubric_svc=None,
) -> list["CandidateSearchResultDTO"]:
    """
    Evaluate candidates using rubric evaluation service.
    Updates candidates in-place with rubric_score, rubric_match_label, and rubric_evaluated.
    """
    for candidate in candidates:
        try:
            candidate_data = _build_candidate_data_from_dto(candidate)
            _svc = rubric_svc if rubric_svc is not None else rubric_evaluation_service
            result = await _svc.evaluate_candidate(
                candidate_data=candidate_data,
                requirements=requirements,
            )
            candidate.rubric_score = result.score
            candidate.rubric_match_label = _get_match_label(result.score)
            candidate.rubric_evaluated = True
        except Exception as e:
            logger.warning(f"Failed to evaluate candidate {candidate.id} with rubrics: {e}")
            candidate.rubric_evaluated = False
    
    return candidates




@router.post("/candidates", response_model=SearchResponseDTO)
async def search_candidates(
    request: SearchRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    pearch_svc: PearchService = Depends(get_pearch_service),
    rubric_svc: RubricEvaluationService = Depends(get_rubric_evaluation_service),
    _cs: CreditService = Depends(get_credit_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Busca candidatos usando busca híbrida (banco local + Pearch AI).
    
    Fluxo:
    1. Primeiro busca no banco local (gratuito)
    2. Se habilitado, complementa com Pearch AI (usa créditos)
    3. Retorna resultados combinados
    4. Se job_id fornecido, avalia candidatos com rubricas
    """
    try:
        # Fase 2: fingerprint dos criterios (ancora feedback/aprendizado a esta busca)
        _search_fp = _generate_search_fingerprint(request.query, request.search_spec)
        # Fase 4: supressao de credito -- docids ja conhecidos -> docid_blacklist
        _suppression_docids: list[str] = []
        if request.search_pearch:
            _suppression_docids = await get_suppression_docids(db, company_id)
        hybrid_request = HybridSearchRequest(
            query=request.query,
            thread_id=request.thread_id,
            search_spec=request.search_spec,
            search_local_first=request.search_local,
            include_pearch=request.search_pearch,
            pearch_type=SearchType.FAST,
            local_limit=request.local_limit,
            pearch_limit=request.pearch_limit,
            require_emails=request.require_emails,
            require_phone_numbers=request.require_phone_numbers,
            show_emails=request.show_emails,
            show_phone_numbers=request.show_phone_numbers,
            job_vacancy_id=request.job_vacancy_id,
            exclude_candidate_ids=list(request.exclude_candidate_ids or []) + _suppression_docids,
            include_discovered=request.include_discovered
        )
        
        if request.search_spec:
            logger.info(f"SearchSpec received: {request.search_spec}")
        
        _apify_fallback_warning = None
        _fb_pearch_count = 0
        _fb_search_time = 0.0
        _fb_can_load_more = False

        _pearch_is_open = PEARCH_CIRCUIT.state == CircuitState.OPEN
        _apify_search_is_open = APIFY_SEARCH_CIRCUIT.state == CircuitState.OPEN

        if _pearch_is_open and request.search_pearch and APIFY_SEARCH_FALLBACK_ENABLED and _apify_search_is_open:
            raise HTTPException(
                status_code=503,
                detail="Serviço de busca temporariamente indisponível. Pearch e Apify fallback estão fora do ar. Tente novamente em alguns minutos.",
            )

        _skip_pearch = _pearch_is_open and request.search_pearch and APIFY_SEARCH_FALLBACK_ENABLED and not _apify_search_is_open

        if _skip_pearch:
            hybrid_request.include_pearch = False

        # Task #961 — deadline canônico (config-driven) da rota. Cobre busca
        # local + chamada Pearch. A chamada Pearch já tem sua própria política
        # de timeouts httpx + asyncio.wait_for interno; este wait_for é o
        # cinto-de-segurança que garante que a rota nunca exceda o deadline
        # antes do proxy do Next.js (90s) ou do browser desistirem.
        from lia_config.config import settings as _settings
        _route_deadline = _settings.SEARCH_CANDIDATES_DEADLINE_SECONDS
        try:
            result = await asyncio.wait_for(
                pearch_svc.hybrid_search(db, hybrid_request),
                timeout=_route_deadline,
            )
        except asyncio.TimeoutError:
            logger.error(
                "[search_candidates] hybrid_search exceeded %.1fs deadline; "
                "returning degraded response (query=%s)",
                _route_deadline, request.query,
            )
            # Contabiliza o cancelamento no circuit breaker do Pearch SOMENTE
            # quando Pearch foi efetivamente acionado nesta busca. Se o
            # circuito já estava aberto e caímos no fallback Apify
            # (`_skip_pearch=True`), Pearch não foi tocado — penalizá-lo
            # geraria falso positivo (false-open) no breaker.
            # Efeitos colaterais (circuit breaker + audit) em BACKGROUND: NAO podem
            # atrasar a resposta degradada. Quando o Pearch estoura o deadline, o DB/audit
            # pode estar lento tambem; await aqui empurrava a resposta alem dos 30s do
            # proxy -> 504 + retries que re-cobram Pearch. Fire-and-forget devolve a
            # resposta degradada na hora (Task #961 + fix 504).
            _pearch_was_attempted = request.search_pearch and not _skip_pearch
            _company_id_audit = (
                getattr(current_user, "company_id", None)
                or getattr(getattr(current_user, "state", None), "company_id", None)
            )

            async def _emit_timeout_side_effects():
                if _pearch_was_attempted:
                    try:
                        await PEARCH_CIRCUIT.record_failure()
                    except Exception as _cb_err:
                        logger.debug("[search_candidates] PEARCH_CIRCUIT.record_failure failed: %s", _cb_err)
                try:
                    import uuid as _uuid
                    from app.shared.compliance.audit_service import AuditService
                    await AuditService().log_action(
                        trace_id=str(_uuid.uuid4()),
                        company_id=str(_company_id_audit) if _company_id_audit else "unattributed",
                        action_type="pearch.search.timeout",
                        actor="api:search_candidates",
                        target_type="external_api",
                        target_id="pearch",
                        metadata={
                            "source": "route_deadline",
                            "deadline_seconds": _route_deadline,
                            "query": request.query,
                        },
                    )
                except Exception as _audit_err:
                    logger.debug("[search_candidates] timeout audit emit failed: %s", _audit_err)

            try:
                asyncio.create_task(_emit_timeout_side_effects())
            except Exception:
                pass
            return SearchResponseDTO(
                query=request.query,
                thread_id=request.thread_id or "",
                search_fingerprint=_search_fp,
                candidates=[],
                local_count=0,
                pearch_count=0,
                total_count=0,
                credits_remaining=None,
                search_time_seconds=_route_deadline,
                warning_message=(
                    "Busca demorou mais que o esperado e foi interrompida. "
                    "Tente novamente em alguns segundos."
                ),
                can_load_more=False,
                should_expand_to_global=False,
                expansion_message=None,
                high_adherence_count=0,
            )

        candidates = []

        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))

        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))

        # Fase 4: persist-on-search (fire-and-forget, nao bloqueia resposta)
        # LGPD Art. 7 IX: interesse legitimo recrutamento. company_id do JWT.
        if result.pearch_candidates:
            asyncio.create_task(
                _persist_pearch_profiles_best_effort(
                    result.pearch_candidates,
                    company_id,
                    _search_fp,
                    request.query,
                )
            )

        if _skip_pearch:
            logger.info("[SearchFallback] Pearch circuit open, using Apify search fallback")
            _company_id = getattr(current_user, "company_id", None) or getattr(getattr(current_user, "state", None), "company_id", None)
            _user_id = getattr(current_user, "id", None) or getattr(current_user, "user_id", None)
            _location = (request.search_spec or {}).get("location")
            try:
                _fb_start = _time.time()
                _fb_result = await APIFY_SEARCH_CIRCUIT.call(
                    apify_search_service.search_candidates,
                    query=request.query,
                    location=_location,
                    limit=request.pearch_limit,
                    company_id=str(_company_id) if _company_id else None,
                    user_id=str(_user_id) if _user_id else None,
                )
                _fb_elapsed_ms = int((_time.time() - _fb_start) * 1000)

                for _profile in _fb_result.candidates:
                    _dto_data = apify_search_service.map_to_search_dto(_profile)
                    if _dto_data is None:
                        continue
                    candidates.append(CandidateSearchResultDTO(**_dto_data))

                _fb_pearch_count = len(_fb_result.candidates)
                _fb_search_time = _fb_result.search_time_seconds
                _fb_can_load_more = _fb_pearch_count >= request.pearch_limit

                _apify_fallback_warning = (
                    f"Busca Pearch indisponível — usando fallback Apify "
                    f"({_fb_result.profiles_scraped} perfis, {_fb_result.emails_found} emails, "
                    f"${_fb_result.total_cost_usd:.2f})"
                )

                if _company_id:
                    try:
                        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService
                        for _sr in _fb_result.stage_records:
                            await ConsumptionTrackingService.record_apify_search_call(
                                db=db,
                                company_id=str(_company_id),
                                user_id=str(_user_id) if _user_id else None,
                                operation=_sr.operation,
                                cost_usd=_sr.cost_usd,
                                success=_sr.success,
                                pipeline_id=_fb_result.pipeline_id,
                                response_time_ms=_sr.response_time_ms,
                                error_message=_sr.error_message,
                            )
                        await db.commit()
                    except Exception as _track_err:
                        logger.warning("[SearchFallback] Consumption tracking error: %s", _track_err)

                logger.info(
                    "[SearchFallback] Apify fallback complete: %d candidates, $%.4f, %dms",
                    len(_fb_result.candidates), _fb_result.total_cost_usd, _fb_elapsed_ms,
                )
            except CircuitBreakerError:
                _apify_fallback_warning = get_degraded_response("apify_search")
                logger.warning("[SearchFallback] Apify search circuit opened during call")
            except Exception as _fb_err:
                _apify_fallback_warning = "Busca fallback via Apify falhou. Tente novamente em instantes."
                logger.error("[SearchFallback] Apify fallback error: %s", _fb_err)
                if _company_id:
                    try:
                        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService
                        await ConsumptionTrackingService.record_apify_search_call(
                            db=db,
                            company_id=str(_company_id),
                            user_id=str(_user_id) if _user_id else None,
                            operation="apify_search",
                            cost_usd=0.0,
                            success=False,
                            error_message=str(_fb_err)[:500],
                        )
                        await db.commit()
                    except Exception:
                        pass
        elif _pearch_is_open and request.search_pearch and not APIFY_SEARCH_FALLBACK_ENABLED:
            _apify_fallback_warning = get_degraded_response("pearch")
        
        candidates = await enrich_and_filter_candidates(db, candidates, company_id=company_id)

        # Task #1219 — garantia final "só candidatos com email" no modo
        # "Híbrida com email". Rede de segurança que cobre TODOS os caminhos
        # (incl. fallback Apify), não só o pool local/Pearch já filtrado em
        # hybrid_search. Os descartados aqui somam ao diagnóstico honesto.
        _extra_no_contact = 0
        if request.require_emails:
            _before_email_filter = len(candidates)
            candidates = [
                c for c in candidates
                if getattr(c, "has_email", False) or getattr(c, "email", None)
            ]
            _extra_no_contact = _before_email_filter - len(candidates)

        # Rubric evaluation if job_id is provided
        if request.job_id and candidates:
            try:
                requirements = await _get_job_requirements(db, request.job_id)
                if requirements:
                    logger.info(f"Evaluating {len(candidates)} candidates with rubrics for job_id={request.job_id}")
                    candidates = await _evaluate_candidates_with_rubrics(
                candidates,
                requirements,
                rubric_svc=rubric_svc,
            )
                else:
                    logger.info(f"No requirements found for job_id={request.job_id}, skipping rubric evaluation")
            except Exception as e:
                logger.warning(f"Rubric evaluation failed for job_id={request.job_id}: {e}")
        
        high_adherence_count = sum(
            1 for c in candidates 
            if c.source == "local" and c.score is not None and c.score >= 60.0
        )
        
        local_only_count = sum(1 for c in candidates if c.source == "local")
        should_expand = (
            local_only_count < 25 and 
            high_adherence_count < int(local_only_count * 0.6) and
            not request.search_pearch
        )
        
        expansion_message = None
        if should_expand:
            if local_only_count == 0:
                expansion_message = "Nenhum candidato encontrado no banco local. Recomendamos expandir para busca global (Pearch)."
            elif high_adherence_count < 10:
                expansion_message = f"Encontrados apenas {high_adherence_count} candidatos com aderência >= 60%. Considere expandir para busca global."
            else:
                expansion_message = f"Pool local limitado ({local_only_count} candidatos). Busca global pode encontrar mais perfis adequados."
        
        _credit_warning = None
        try:
            _company_id = getattr(current_user, "company_id", None) or getattr(getattr(current_user, "state", None), "company_id", None)
            if _company_id:
                _action = "bulk_search" if request.search_pearch else "search"
                _success, _remaining = await _cs.consume_action(db, _company_id, _action, reference_type="search", reference_id=result.thread_id)
                if not _success:
                    _credit_warning = f"Créditos insuficientes (saldo: {_remaining}). Resultados foram retornados, mas a ação não foi debitada."
                    logger.warning("[Credits] Insufficient credits for %s action=%s balance=%d", _company_id, _action, _remaining)
                else:
                    _balance_data = await _cs.get_balance(db, _company_id)
                    if _balance_data.get("low_balance_warning"):
                        _credit_warning = f"Atenção: saldo de créditos baixo ({_remaining} restantes). Considere adquirir mais créditos."
                await db.commit()
        except Exception as _credit_err:
            logger.warning("[Credits] Credit deduction error (non-fatal): %s", _credit_err)

        _effective_pearch_count = result.pearch_count + _fb_pearch_count
        _effective_search_time = (result.local_search_time or 0) + (result.pearch_search_time or 0) + _fb_search_time
        _effective_can_load_more = (result.pearch_count >= request.pearch_limit) or _fb_can_load_more
        # Task #1219 — diagnósticos honestos do modo "Híbrida com email".
        _filtered_no_contact = (getattr(result, "filtered_no_contact", 0) or 0) + _extra_no_contact
        _sources_exhausted = getattr(result, "sources_exhausted", False) or False
        # Em modo require_emails, se as fontes esgotaram não há mais o que
        # carregar — evita "Carregar mais" que retornaria vazio.
        if request.require_emails and _sources_exhausted:
            _effective_can_load_more = False

        return SearchResponseDTO(
            query=result.query,
            thread_id=result.thread_id,
            search_fingerprint=_search_fp,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=_effective_pearch_count,
            total_count=len(candidates),
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=_effective_search_time,
            warning_message=_apify_fallback_warning or _credit_warning or result.warning_message,
            can_load_more=_effective_can_load_more,
            should_expand_to_global=should_expand,
            expansion_message=expansion_message,
            high_adherence_count=high_adherence_count,
            filtered_no_contact=_filtered_no_contact,
            sources_exhausted=_sources_exhausted,
            enrichment_attempted=getattr(result, "enrichment_attempted", 0) or 0,
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")




@router.get("/candidates/search/snapshot", response_model=SearchResponseDTO)
async def get_search_snapshot(
    fingerprint: str,
    db: "AsyncSession" = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Fase 4: resgate congelado — retorna perfis Pearch já persistidos pelo fingerprint.

    Carrega de external_candidate_profiles SEM chamar Pearch (zero crédito).
    Idêntico em estrutura ao POST /candidates, mas congelado no momento da busca original.
    """
    import sqlalchemy as sa
    from lia_models.candidate import ExternalCandidateProfile

    try:
        result = await db.execute(
            sa.select(ExternalCandidateProfile)
            .where(
                sa.and_(
                    ExternalCandidateProfile.search_fingerprint == fingerprint,
                    ExternalCandidateProfile.company_id == company_id,
                    ExternalCandidateProfile.source == "pearch",
                )
            )
            .order_by(ExternalCandidateProfile.created_at.desc())
            .limit(100)
        )
        rows = result.scalars().all()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Snapshot retrieval failed: {exc}")

    candidates = []
    for row in rows:
        loc_parts = [p for p in [row.location_city, row.location_state, row.location_country] if p]
        location = ", ".join(loc_parts) if loc_parts else row.location_raw

        candidates.append(
            CandidateSearchResultDTO(
                id=str(row.source_profile_id),
                name=row.name or "",
                first_name=row.first_name,
                last_name=row.last_name,
                headline=row.headline,
                current_title=row.current_title,
                current_company=row.current_company,
                location=location,
                skills=list(row.skills or []),
                linkedin_url=row.linkedin_url,
                has_email=bool(row.has_email),
                has_phone=bool(row.has_phone),
                email=row.email,
                phone=row.phone,
                picture_url=row.avatar_url,
                is_discovered=True,
                is_open_to_work=row.is_open_to_work,
                total_experience_years=float(row.years_of_experience) if row.years_of_experience else None,
                source="pearch",
                summary=row.summary,
            )
        )

    return SearchResponseDTO(
        query=rows[0].search_query or "" if rows else "",
        search_fingerprint=fingerprint,
        candidates=candidates,
        pearch_count=len(candidates),
        total_count=len(candidates),
        credits_used=0,  # resgate congelado: zero crédito
    )
