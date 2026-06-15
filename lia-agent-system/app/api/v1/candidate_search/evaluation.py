"""Evaluate candidates for job route: POST /evaluate-for-job"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

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
    _get_job_requirements,
    _get_match_label,
    _normalize_name,
    _normalize_priority,
    assert_resource_ownership,
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

@router.post("/evaluate-for-job", response_model=EvaluateForJobResponse)
async def evaluate_candidates_for_job(
    request: EvaluateForJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    rubric_svc: RubricEvaluationService = Depends(get_rubric_evaluation_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Avalia candidatos em batch contra os requisitos de uma vaga usando rubricas.
    
    Útil para:
    - Avaliar candidatos já descobertos/importados
    - Re-avaliar candidatos após atualização de requisitos da vaga
    - Calcular score de match para candidatos de diferentes fontes
    
    Retorna rubric_score (0-100), rubric_match_label (Exceeds/Meets/Partial/Missing) 
    e rubric_evaluated para cada candidato.
    """
    from sqlalchemy import select

    from app.models.candidate import Candidate, ExternalCandidateProfile

    results = []
    evaluated_count = 0
    failed_count = 0
    
    try:
        # Get job requirements
        requirements = await _get_job_requirements(db, request.job_id)
        if not requirements:
            return EvaluateForJobResponse(
                job_id=request.job_id,
                total_candidates=len(request.candidate_ids),
                evaluated_count=0,
                failed_count=len(request.candidate_ids),
                results=[
                    EvaluateForJobResult(
                        candidate_id=cid,
                        rubric_evaluated=False,
                        error="Nenhum requisito cadastrado para esta vaga"
                    )
                    for cid in request.candidate_ids
                ]
            )
        
        logger.info(f"Evaluating {len(request.candidate_ids)} candidates for job_id={request.job_id}")
        
        for candidate_id in request.candidate_ids:
            try:
                # Try to find candidate in main table
                result = await db.execute(
                    select(Candidate).where(Candidate.id == UUID(candidate_id), Candidate.company_id == company_id)
                )
                candidate = result.scalar_one_or_none()
                
                candidate_data = None
                
                if candidate:
                    # Build candidate data from main Candidate model
                    candidate_data = {
                        "id": str(candidate.id),
                        "name": candidate.name,
                        "current_title": candidate.current_title,
                        "current_company": candidate.current_company,
                        "years_of_experience": candidate.years_of_experience,
                        "seniority_level": candidate.seniority_level,
                        "technical_skills": candidate.technical_skills or [],
                        "skills": candidate.technical_skills or [],
                        "soft_skills": candidate.soft_skills or [],
                        "certifications": candidate.certifications or [],
                        "languages": candidate.languages or {},
                        "work_history": candidate.work_history or [],
                        "education": candidate.education or [],
                        "resume_text": candidate.resume_text,
                        "self_introduction": candidate.self_introduction,
                        "expertise": candidate.expertise or [],
                    }
                else:
                    # Try to find in staging table (discovered candidates)
                    staging_result = await db.execute(
                        select(ExternalCandidateProfile).where(
                            ExternalCandidateProfile.id == UUID(candidate_id),
                            ExternalCandidateProfile.company_id == company_id,
                        )
                    )
                    staging_candidate = staging_result.scalar_one_or_none()
                    
                    if staging_candidate:
                        candidate_data = {
                            "id": str(staging_candidate.id),
                            "name": staging_candidate.name,
                            "current_title": staging_candidate.current_title,
                            "current_company": staging_candidate.current_company,
                            "years_of_experience": staging_candidate.years_of_experience,
                            "seniority_level": staging_candidate.seniority_level,
                            "skills": staging_candidate.skills or [],
                            "technical_skills": staging_candidate.skills or [],
                            "expertise": staging_candidate.expertise or [],
                            "work_history": staging_candidate.experiences_snapshot or [],
                            "education": staging_candidate.education_snapshot or [],
                            "self_introduction": staging_candidate.summary,
                        }
                
                if not candidate_data:
                    results.append(EvaluateForJobResult(
                        candidate_id=candidate_id,
                        rubric_evaluated=False,
                        error="Candidato não encontrado"
                    ))
                    failed_count += 1
                    continue
                
                # Evaluate with rubrics
                eval_result = await rubric_svc.evaluate_candidate(
                    candidate_data=candidate_data,
                    requirements=requirements,
                )
                
                results.append(EvaluateForJobResult(
                    candidate_id=candidate_id,
                    rubric_score=eval_result.score,
                    rubric_match_label=_get_match_label(eval_result.score),
                    rubric_evaluated=True,
                ))
                evaluated_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to evaluate candidate {candidate_id}: {e}")
                results.append(EvaluateForJobResult(
                    candidate_id=candidate_id,
                    rubric_evaluated=False,
                    error=str(e)
                ))
                failed_count += 1
        
        return EvaluateForJobResponse(
            job_id=request.job_id,
            total_candidates=len(request.candidate_ids),
            evaluated_count=evaluated_count,
            failed_count=failed_count,
            results=results
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _normalize_name(name: str) -> str:
    """Normaliza nome para comparação e deduplicação."""
    import re
    import unicodedata
    normalized = unicodedata.normalize('NFKD', name.lower())
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    normalized = re.sub(r'[^a-z\s]', '', normalized)
    normalized = ' '.join(normalized.split())
    return normalized


def _generate_fingerprint(name: str, linkedin_url: str | None = None, email: str | None = None) -> str:
    """Gera hash de fingerprint para deduplicação."""
    import hashlib
    parts = [_normalize_name(name)]
    if linkedin_url:
        linkedin_id = linkedin_url.rstrip('/').split('/')[-1].lower()
        parts.append(f"li:{linkedin_id}")
    if email:
        parts.append(f"email:{email.lower()}")
    fingerprint_str = "|".join(sorted(parts))
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]


from app.auth.dependencies import assert_resource_ownership, get_current_user_or_demo, get_user_company_id
from app.auth.models import User as ImportUser


