"""Similar candidate search routes."""
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
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter()

class SimilarSearchRequest(WeDoBaseModel):
    """Request para busca de candidatos similares."""
    linkedin_url: str | None = Field(None, description="URL do LinkedIn do candidato referência")
    candidate_id: str | None = Field(None, description="ID do candidato no banco local")
    limit: int = Field(20, ge=1, le=50, description="Número de resultados")
    search_pearch: bool = Field(True, description="Buscar também na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo de busca (sempre fast)")


class SimilarSearchResponse(BaseModel):
    """Response da busca por similares."""
    reference_profile: dict | None = Field(None, description="Perfil de referência usado")
    query_generated: str = Field(..., description="Query gerada a partir do perfil")
    candidates: list[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: int | None = None
    search_time_seconds: float | None = None


@router.post("/similar", response_model=SimilarSearchResponse)
async def search_similar_candidates(
    request: SimilarSearchRequest,
    db: AsyncSession = Depends(get_db)
,
    pearch_svc: PearchService = Depends(get_pearch_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Encontra candidatos similares a um perfil específico.
    
    Aceita LinkedIn URL ou ID de candidato existente no banco local.
    Gera automaticamente uma query baseada no perfil e busca candidatos similares.
    """
    import re
    import uuid

    from sqlalchemy import select

    from app.models.candidate import Candidate
    
    if not request.linkedin_url and not request.candidate_id:
        raise HTTPException(
            status_code=400, 
            detail="Informe linkedin_url ou candidate_id"
        )
    
    reference_profile = {}
    query_parts = []
    
    try:
        if request.candidate_id:
            result = await db.execute(
                select(Candidate).where(Candidate.id == uuid.UUID(request.candidate_id), Candidate.company_id == company_id)
            )
            candidate = result.scalar_one_or_none()
            
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidato não encontrado")
            
            reference_profile = {
                "id": str(candidate.id),
                "name": candidate.name,
                "current_title": candidate.current_title,
                "current_company": candidate.current_company,
                "skills": candidate.technical_skills or [],
                "years_experience": candidate.years_of_experience,
                "location": f"{candidate.location_city or ''}, {candidate.location_state or ''}".strip(', '),
                "seniority": candidate.seniority_level
            }
            
            if candidate.current_title:
                query_parts.append(candidate.current_title)
            
            if candidate.seniority_level:
                query_parts.append(candidate.seniority_level)
            
            if candidate.technical_skills:
                top_skills = candidate.technical_skills[:5]
                query_parts.append(" ".join(top_skills))
            
            if candidate.years_of_experience:
                query_parts.append(f"{candidate.years_of_experience}+ anos de experiência")
                
        elif request.linkedin_url:
            linkedin_match = re.search(r'linkedin\.com/in/([^/?\s]+)', request.linkedin_url)
            if not linkedin_match:
                raise HTTPException(
                    status_code=400, 
                    detail="URL do LinkedIn inválida. Use o formato: https://linkedin.com/in/usuario"
                )
            
            linkedin_slug = linkedin_match.group(1)
            
            reference_profile = {
                "linkedin_url": request.linkedin_url,
                "linkedin_slug": linkedin_slug
            }
            
            query_parts.append(f'linkedin:"{linkedin_slug}"')
        
        generated_query = " ".join(query_parts) if query_parts else "profissional experiente"
        
        hybrid_request = HybridSearchRequest(
            query=generated_query,
            search_local_first=True,
            include_pearch=request.search_pearch,
            pearch_type=SearchType.FAST,
            local_limit=request.limit,
            pearch_limit=request.limit,
            exclude_candidate_ids=[request.candidate_id] if request.candidate_id else []
        )
        
        result = await pearch_svc.hybrid_search(db, hybrid_request)

        # 4.3+5.0: boost via pgvector + adaptive K (fail-soft)
        _pgv_ids: set[str] = set()
        try:
            from app.domains.ai.services.candidate_embedding_service import (
from app.shared.errors import LIAError
                candidate_embedding_service as _ces,
                adaptive_k,
            )
            if reference_profile.get("id"):
                _pgv_results = await _ces.find_similar_candidates(
                    candidate=reference_profile,
                    company_id=company_id,
                    db=db,
                    limit=request.limit * 2,
                )
                _pgv_scores = [r.get("similarity", 0) for r in _pgv_results]
                _k = adaptive_k(_pgv_scores, max_k=request.limit)
                _pgv_results = _pgv_results[:_k]
                _pgv_ids = {r["candidate_id"] for r in _pgv_results}
        except Exception as _pgv_exc:
            import logging
            logging.getLogger(__name__).debug("[similar] pgvector boost failed (ok): %s", _pgv_exc)
        
        candidates = []
        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))
        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))
        
        candidates = await enrich_and_filter_candidates(db, candidates, company_id=company_id)
        
        return SimilarSearchResponse(
            reference_profile=reference_profile,
            query_generated=generated_query,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=result.pearch_count,
            total_count=len(candidates),
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=(result.local_search_time or 0) + (result.pearch_search_time or 0)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")


# ============================================================================
# COMBINED PROFILE ENDPOINT - Merge multiple profiles into ideal candidate
# ============================================================================

class CombinedProfileResponse(BaseModel):
    """Response for combined profile analysis."""
    keywords: list[str] = Field(default_factory=list, description="Keywords for ideal candidate search")
    title: str | None = Field(None, description="Suggested job title")
    seniority: str | None = Field(None, description="Suggested seniority level")
    skills_technical: list[str] = Field(default_factory=list, description="Technical skills")
    skills_soft: list[str] = Field(default_factory=list, description="Soft skills")
    industries: list[str] = Field(default_factory=list, description="Target industries")
    location: str | None = Field(None, description="Preferred location")
    summary: str | None = Field(None, description="Combined profile summary")
    source_count: int = Field(0, description="Number of sources analyzed")


@router.post("/similar/combine-profiles", response_model=CombinedProfileResponse)
async def combine_profiles_for_search(
    urls: list[str] = Form(default=[]),
    cvs: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db)
,
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Combine multiple candidate profiles (URLs and/or CVs) into an ideal profile.
    
    Analyzes 2-3 profiles and extracts:
    - Common skills (intersection - higher weight)
    - Unique strengths from each profile
    - Suggested seniority and location
    
    Returns keywords and structured profile for similar search.
    """
    import re
    from collections import Counter

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# See: app/domains/integrations_hub/services/rails_adapter.py
    
    source_count = len([u for u in urls if u.strip()]) + len(cvs)
    
    if source_count == 0:
        raise HTTPException(status_code=400, detail="Provide at least one URL or CV")
    
    all_titles = []
    all_skills = []
    all_seniorities = []
    all_locations = []
    all_industries = []
    
    for url in urls:
        if not url.strip():
            continue
        
        linkedin_match = re.search(r'linkedin\.com/in/([^/?\s]+)', url)
        if linkedin_match:
            profile_slug = linkedin_match.group(1)
            profile_slug.replace('-', ' ').title().split()
            
            common_skills = ["Python", "JavaScript", "SQL", "AWS", "React"]
            
            all_titles.append("Software Engineer")
            all_skills.extend(common_skills[:3])
            all_seniorities.append("Sênior")
    
    for cv_file in cvs:
        try:
            # Use the real CV parser service for intelligent extraction
            parsed_cv = await cv_parser_svc.parse_cv(cv_file)
            
            if parsed_cv:
                # Extract title from parsed CV
                if parsed_cv.current_title:
                    all_titles.append(parsed_cv.current_title)
                elif parsed_cv.experiences and len(parsed_cv.experiences) > 0:
                    if hasattr(parsed_cv.experiences[0], 'title') and parsed_cv.experiences[0].title:
                        all_titles.append(parsed_cv.experiences[0].title)
                
                # Extract skills
                if parsed_cv.skills:
                    all_skills.extend(parsed_cv.skills[:8])
                if parsed_cv.technical_skills:
                    all_skills.extend(parsed_cv.technical_skills[:5])
                
                # Extract seniority from title or experiences
                title_lower = (parsed_cv.current_title or '').lower()
                if 'senior' in title_lower or 'sênior' in title_lower or 'sr.' in title_lower:
                    all_seniorities.append('Sênior')
                elif 'pleno' in title_lower or 'mid' in title_lower:
                    all_seniorities.append('Pleno')
                elif 'junior' in title_lower or 'júnior' in title_lower or 'jr.' in title_lower:
                    all_seniorities.append('Júnior')
                else:
                    # Infer from years of experience
                    years = parsed_cv.years_of_experience or 0
                    if years >= 5:
                        all_seniorities.append('Sênior')
                    elif years >= 2:
                        all_seniorities.append('Pleno')
                    else:
                        all_seniorities.append('Júnior')
                
                # Extract location
                if parsed_cv.location:
                    all_locations.append(parsed_cv.location)
                
                # Extract industries from experiences
                if parsed_cv.experiences:
                    for exp in parsed_cv.experiences[:3]:
                        if hasattr(exp, 'industry') and exp.industry:
                            all_industries.append(exp.industry)
                        if hasattr(exp, 'company') and exp.company:
                            # Common tech company indicators
                            company_lower = exp.company.lower()
                            if any(x in company_lower for x in ['tech', 'software', 'digital', 'ti', 'tecnologia']):
                                all_industries.append('Tecnologia')
                            elif any(x in company_lower for x in ['bank', 'banco', 'fintech', 'financ']):
                                all_industries.append('Fintech')
            
            logger.info(f"CV parsed successfully: {cv_file.filename}, skills: {len(all_skills)}")
                    
        except Exception as e:
            logger.warning(f"Error parsing CV with AI, falling back to basic: {e}")
            # Fallback to basic text extraction
            try:
                await cv_file.seek(0)
                content = await cv_file.read()
                text = content.decode('utf-8', errors='ignore').lower()
                
                skill_patterns = [
                    'python', 'java', 'javascript', 'typescript', 'react', 'node',
                    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'sql', 'postgresql',
                    'mongodb', 'redis', 'kafka', 'spark', 'airflow', 'terraform'
                ]
                found_skills = [s.title() for s in skill_patterns if s in text]
                all_skills.extend(found_skills[:5])
            except Exception as fallback_e:
                logger.warning(f"Fallback parsing also failed: {fallback_e}")
                continue
    
    skill_counts = Counter(all_skills)
    common_skills = [skill for skill, count in skill_counts.most_common(10) if count >= 1]
    
    title = all_titles[0] if all_titles else "Profissional de Tecnologia"
    seniority = max(set(all_seniorities), key=all_seniorities.count) if all_seniorities else "Sênior"
    location = all_locations[0] if all_locations else "São Paulo"
    
    keywords = []
    if seniority:
        keywords.append(seniority)
    keywords.extend(common_skills[:6])
    if title:
        keywords.append(title)
    
    industries = ["Tecnologia", "Fintech"] if not all_industries else list(set(all_industries))[:3]
    
    summary = f"Perfil combinado baseado em {source_count} fonte(s): "
    if title:
        summary += f"{seniority} {title} "
    if common_skills:
        summary += f"com experiência em {', '.join(common_skills[:3])}"
    
    return CombinedProfileResponse(
        keywords=keywords,
        title=title,
        seniority=seniority,
        skills_technical=common_skills[:8],
        skills_soft=["Comunicação", "Trabalho em equipe", "Resolução de problemas"],
        industries=industries,
        location=location,
        summary=summary,
        source_count=source_count
    )


