"""Candidate search route: POST /candidates"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._shared import (
    CVParserService,
    CandidateProfile,
    CandidateSearchResultDTO,
    CreditEstimateDTO,
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
):
    """
    Busca candidatos usando busca híbrida (banco local + Pearch AI).
    
    Fluxo:
    1. Primeiro busca no banco local (gratuito)
    2. Se habilitado, complementa com Pearch AI (usa créditos)
    3. Retorna resultados combinados
    4. Se job_id fornecido, avalia candidatos com rubricas
    """
    try:
        # Prepara request híbrido com SearchSpec para filtros avançados
        hybrid_request = HybridSearchRequest(
            query=request.query,
            thread_id=request.thread_id,
            search_spec=request.search_spec,
            search_local_first=request.search_local,
            include_pearch=request.search_pearch,
            pearch_type=SearchType.FAST,
            local_limit=request.local_limit,
            pearch_limit=request.pearch_limit,
            show_emails=request.show_emails,
            show_phone_numbers=request.show_phone_numbers,
            job_vacancy_id=request.job_vacancy_id,
            exclude_candidate_ids=request.exclude_candidate_ids,
            include_discovered=request.include_discovered
        )
        
        # Log se SearchSpec foi recebido
        if request.search_spec:
            logger.info(f"SearchSpec received: {request.search_spec}")
        
        # Executa busca híbrida
        result = await pearch_svc.hybrid_search(db, hybrid_request)
        
        # Converte candidatos para DTO
        candidates = []
        
        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))
        
        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))
        
        candidates = await enrich_and_filter_candidates(db, candidates)
        
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

        return SearchResponseDTO(
            query=result.query,
            thread_id=result.thread_id,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=result.pearch_count,
            total_count=result.total_count,
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=(result.local_search_time or 0) + (result.pearch_search_time or 0),
            warning_message=_credit_warning or result.warning_message,
            can_load_more=result.pearch_count >= request.pearch_limit,
            should_expand_to_global=should_expand,
            expansion_message=expansion_message,
            high_adherence_count=high_adherence_count
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


