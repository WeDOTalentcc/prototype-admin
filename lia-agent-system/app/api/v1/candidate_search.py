"""
Candidate Search API - Endpoints for hybrid candidate search (local + Pearch).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.domains.cv_screening.services.cv_parser import cv_parser_service
from app.domains.analytics.services.search_analytics_service import search_analytics_service
from app.services.archetype_builder_service import extract_tags_from_search_spec, build_archetype_from_search
from app.schemas.archetype import ArchetypeFromSearchCreate, ArchetypeFromSearchResponse, ArchetypeResponse
from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service, get_recommendation
from app.models.rubric import JobRequirement
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
from uuid import UUID
from enum import Enum as PyEnum

logger = logging.getLogger(__name__)


def _normalize_priority(priority_value) -> RequirementPriorityEnum:
    """Normalize priority value to RequirementPriorityEnum, handling ORM enums and strings."""
    if priority_value is None:
        return RequirementPriorityEnum.IMPORTANT
    if isinstance(priority_value, RequirementPriorityEnum):
        return priority_value
    if isinstance(priority_value, PyEnum):
        priority_value = priority_value.value
    if isinstance(priority_value, str):
        try:
            return RequirementPriorityEnum(priority_value.lower())
        except ValueError:
            return RequirementPriorityEnum.IMPORTANT
    return RequirementPriorityEnum.IMPORTANT
from app.domains.sourcing.services.pearch_service import pearch_service
from app.models.pearch import (
    HybridSearchRequest,
    HybridSearchResponse,
    PearchSearchRequest,
    PearchSearchResponse,
    SearchType,
    CreditEstimate,
    SearchConfirmation,
    CandidateProfile
)

router = APIRouter(prefix="/search", tags=["candidate-search"])


class SearchRequestDTO(BaseModel):
    """Request para busca de candidatos via API."""
    query: str = Field(..., description="Query em linguagem natural")
    thread_id: Optional[str] = Field(None, description="Thread ID para refinamento")
    
    # SearchSpec - metadados estruturados extraídos pelo LLM do frontend
    search_spec: Optional[Dict[str, Any]] = Field(None, description="Metadados estruturados (location, skills, seniority, etc)")
    
    # Configuração de busca
    search_local: bool = Field(True, description="Buscar no banco local")
    search_pearch: bool = Field(True, description="Buscar na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo: 'fast' ou 'pro'", pattern="^(fast|pro)$")
    
    # Limites
    local_limit: int = Field(20, ge=1, le=100)
    pearch_limit: int = Field(15, ge=1, le=50)
    
    # Opções de contato
    show_emails: bool = Field(False)
    show_phone_numbers: bool = Field(False)
    high_freshness: bool = Field(False, description="Dados em tempo real (+2 créditos)")
    require_emails: bool = Field(False, description="Apenas perfis com email")
    require_phone_numbers: bool = Field(False, description="Apenas perfis com telefone")
    
    # Contexto
    job_vacancy_id: Optional[int] = Field(None)
    exclude_candidate_ids: List[str] = Field(default_factory=list)
    
    # Include discovered candidates from staging table
    include_discovered: bool = Field(True, description="Include discovered candidates from staging table")
    
    # Rubric evaluation - optional job_id to evaluate candidates against job requirements
    job_id: Optional[str] = Field(None, description="Job UUID for rubric evaluation. If provided, candidates will be scored against job requirements.")


class ExperienceDTO(BaseModel):
    """Experiência profissional para o frontend."""
    title: Optional[str] = None
    company: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_years: Optional[float] = None
    description: Optional[str] = None
    current: bool = False
    industries: List[str] = Field(default_factory=list)
    company_size: Optional[str] = None
    company_size_range: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    is_startup: Optional[bool] = None
    company_linkedin_url: Optional[str] = None
    company_domain: Optional[str] = None


class ImportCandidateExperienceDTO(BaseModel):
    """Experiência para importação com dados ricos de empresa."""
    company_name: str
    company_linkedin_url: Optional[str] = None
    company_domain: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_years: Optional[float] = None
    is_current: bool = False
    description: Optional[str] = None
    location: Optional[str] = None
    industries: List[str] = Field(default_factory=list)
    company_size: Optional[str] = None
    company_size_range: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    is_startup: Optional[bool] = None
    company_founded_year: Optional[int] = None
    company_annual_revenue: Optional[float] = None
    # Campos de company_info da Pearch
    company_followers_count: Optional[int] = None
    company_keywords: List[str] = Field(default_factory=list)
    company_is_hiring: Optional[bool] = None


class ImportCandidateDTO(BaseModel):
    """Candidato Pearch para importação na base local."""
    pearch_id: str
    name: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    years_of_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    languages: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    experiences: List[ImportCandidateExperienceDTO] = Field(default_factory=list)
    is_open_to_work: Optional[bool] = None
    is_decision_maker: Optional[bool] = None
    is_top_universities: Optional[bool] = None
    is_hiring: Optional[bool] = None
    expertise: List[str] = Field(default_factory=list)
    # Campos de contato Pearch
    best_personal_email: Optional[str] = None
    best_business_email: Optional[str] = None
    personal_emails: List[str] = Field(default_factory=list)
    business_emails: List[str] = Field(default_factory=list)
    phone_types: Optional[Dict[str, Any]] = None
    # Campos de perfil Pearch
    estimated_age: Optional[int] = None
    linkedin_followers_count: Optional[int] = None
    linkedin_connections_count: Optional[int] = None
    # Insights e mensagem
    insights: Optional[Dict[str, Any]] = None
    outreach_message: Optional[str] = None
    match_reasoning: Optional[str] = None


class ImportCandidatesRequest(BaseModel):
    """Request para importar candidatos Pearch para base local."""
    candidates: List[ImportCandidateDTO]
    source_search_query: Optional[str] = None
    add_to_vacancy_id: Optional[str] = None


class IdMapping(BaseModel):
    """Mapeamento de pearch_id para local_id."""
    pearch_id: str
    local_id: str


class ImportCandidatesResponse(BaseModel):
    """Response da importação de candidatos."""
    imported_count: int
    skipped_count: int
    updated_count: int = 0
    imported_ids: List[str]
    skipped_ids: List[str]
    mapping: List[IdMapping]
    message: str


class EducationDTO(BaseModel):
    """Formação educacional para o frontend."""
    school: Optional[str] = None
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class LanguageDTO(BaseModel):
    """Idioma para o frontend."""
    language: Optional[str] = None
    name: Optional[str] = None
    proficiency: Optional[str] = None
    level: Optional[str] = None


class CandidateSearchResultDTO(BaseModel):
    """Resultado individual para o frontend."""
    id: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture_url: Optional[str] = None
    
    headline: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    
    total_experience_years: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    
    score: Optional[float] = None  # 0-100
    match_summary: Optional[str] = None
    
    linkedin_url: Optional[str] = None
    has_email: bool = False
    has_phone: bool = False
    email: Optional[str] = None
    phone: Optional[str] = None
    
    source: str = "local"  # "local" or "pearch"
    is_open_to_work: Optional[bool] = None
    is_discovered: bool = False  # True if candidate is from staging table (not saved to local base yet)
    
    # Campos expandidos para dados completos do perfil (Pearch)
    summary: Optional[str] = None
    experiences: List[ExperienceDTO] = Field(default_factory=list)
    work_history: List[ExperienceDTO] = Field(default_factory=list)
    education: List[EducationDTO] = Field(default_factory=list)
    languages: List[LanguageDTO] = Field(default_factory=list)
    expertise: List[str] = Field(default_factory=list)
    
    # Flattened company info from most recent experience (for table columns)
    company_industries: List[str] = Field(default_factory=list, description="Industries from most recent experience")
    company_size: Optional[str] = Field(None, description="Company size from most recent experience")
    
    # Rubric evaluation fields (populated when job_id is provided in search)
    rubric_score: Optional[float] = Field(None, description="Rubric evaluation score 0-100")
    rubric_match_label: Optional[str] = Field(None, description="Match label: Exceeds/Meets/Partial/Missing")
    rubric_evaluated: bool = Field(False, description="Whether rubric evaluation was performed")
    
    @classmethod
    def from_profile(cls, profile: CandidateProfile, source: str = "local") -> "CandidateSearchResultDTO":
        """Converte CandidateProfile para DTO do frontend."""
        # Mapear experiências com dados ricos de empresa
        experiences_dto = []
        for exp in (profile.experiences or []):
            # Extrair dados de empresa se disponíveis
            company_info = exp.company_info
            industries = company_info.industries if company_info else []
            technologies = company_info.technologies if company_info else []
            company_size = str(company_info.num_employees) if company_info and company_info.num_employees else None
            company_size_range = company_info.num_employees_range if company_info else None
            is_startup = company_info.is_startup if company_info else None
            company_linkedin_url = company_info.linkedin_url if company_info else None
            company_domain = company_info.domain if company_info else None
            
            # Verificar se tem company_roles (estrutura nova do Pearch)
            if exp.company_roles:
                for role in exp.company_roles:
                    experiences_dto.append(ExperienceDTO(
                        title=role.title,
                        company=role.company or (exp.company_info.name if exp.company_info else None),
                        company_name=role.company or (exp.company_info.name if exp.company_info else None),
                        location=role.location or (exp.company_info.short_address if exp.company_info else None),
                        start_date=role.start_date,
                        end_date=role.end_date,
                        duration_years=role.duration_years,
                        description=role.description,
                        current=role.end_date is None or role.end_date == "",
                        industries=industries,
                        company_size=company_size,
                        company_size_range=company_size_range,
                        technologies=technologies,
                        is_startup=is_startup,
                        company_linkedin_url=company_linkedin_url,
                        company_domain=company_domain
                    ))
            else:
                # Estrutura legada
                experiences_dto.append(ExperienceDTO(
                    title=exp.title,
                    company=exp.company,
                    company_name=exp.company,
                    location=exp.location,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    duration_years=exp.duration_years,
                    description=exp.description,
                    current=exp.end_date is None or exp.end_date == "",
                    industries=industries,
                    company_size=company_size,
                    company_size_range=company_size_range,
                    technologies=technologies,
                    is_startup=is_startup,
                    company_linkedin_url=company_linkedin_url,
                    company_domain=company_domain
                ))
        
        # Mapear educação
        education_dto = []
        for edu in (profile.education or []):
            education_dto.append(EducationDTO(
                school=edu.school,
                institution=edu.school,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                start_date=edu.start_date,
                end_date=edu.end_date
            ))
        
        # Mapear idiomas
        languages_dto = []
        all_languages = (profile.languages or []) + (profile.inferred_languages or [])
        seen_languages = set()
        for lang in all_languages:
            lang_name = lang.language
            if lang_name and lang_name not in seen_languages:
                seen_languages.add(lang_name)
                languages_dto.append(LanguageDTO(
                    language=lang_name,
                    name=lang_name,
                    proficiency=lang.proficiency,
                    level=lang.proficiency
                ))
        
        # Extract flattened company info from most recent experience
        top_level_company_industries: List[str] = []
        top_level_company_size: Optional[str] = None
        if profile.experiences and len(profile.experiences) > 0:
            first_exp = profile.experiences[0]
            if first_exp.company_info:
                top_level_company_industries = first_exp.company_info.industries or []
                top_level_company_size = first_exp.company_info.num_employees_range
            elif first_exp.industries:
                top_level_company_industries = first_exp.industries
                top_level_company_size = first_exp.company_size
        
        return cls(
            id=profile.docid or "",
            name=profile.get_full_name(),
            first_name=profile.first_name,
            last_name=profile.last_name,
            picture_url=profile.picture_url,
            headline=profile.headline,
            current_title=profile.current_title,
            current_company=profile.current_company,
            location=profile.location,
            total_experience_years=profile.total_experience_years,
            skills=profile.skills[:15] if profile.skills else [],
            score=profile.get_score_percentage(),
            match_summary=profile.insights.overall_summary if profile.insights else profile.match_reasoning,
            linkedin_url=profile.get_linkedin_url(),
            has_email=profile.has_emails or False,
            has_phone=profile.has_phone_numbers or False,
            email=profile.best_personal_email or (profile.emails[0] if profile.emails else None),
            phone=profile.phone_numbers[0] if profile.phone_numbers else None,
            source=source,
            is_open_to_work=profile.is_opentowork,
            is_discovered=profile.is_discovered,
            # Novos campos expandidos
            summary=profile.summary,
            experiences=experiences_dto,
            work_history=experiences_dto,
            education=education_dto,
            languages=languages_dto,
            expertise=profile.expertise[:10] if profile.expertise else [],
            # Flattened company info from most recent experience
            company_industries=top_level_company_industries,
            company_size=top_level_company_size
        )


class SearchResponseDTO(BaseModel):
    """Response da busca para o frontend."""
    query: str
    thread_id: Optional[str] = None
    
    candidates: List[CandidateSearchResultDTO] = Field(default_factory=list)
    
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    
    credits_used: Optional[int] = None
    credits_remaining: Optional[int] = None
    
    search_time_seconds: Optional[float] = None
    warning_message: Optional[str] = None
    
    can_load_more: bool = False
    
    should_expand_to_global: bool = Field(
        default=False,
        description="Indica se a busca deve ser expandida para busca global (Pearch)"
    )
    expansion_message: Optional[str] = Field(
        default=None,
        description="Mensagem de recomendação para expansão da busca"
    )
    high_adherence_count: int = Field(
        default=0,
        description="Número de candidatos com aderência >= 60%"
    )


class CreditEstimateDTO(BaseModel):
    """Estimativa de créditos para confirmação."""
    query: str
    pearch_type: str
    limit: int
    
    cost_per_candidate: int
    total_estimated: int
    
    breakdown: dict = Field(default_factory=dict)
    confirmation_message: str


class EvaluateForJobRequest(BaseModel):
    """Request para avaliar candidatos em batch por job_id."""
    job_id: str = Field(..., description="UUID da vaga para avaliação")
    candidate_ids: List[str] = Field(..., description="Lista de UUIDs dos candidatos a avaliar", min_length=1, max_length=100)


class EvaluateForJobResult(BaseModel):
    """Resultado da avaliação de um candidato."""
    candidate_id: str
    rubric_score: Optional[float] = None
    rubric_match_label: Optional[str] = None
    rubric_evaluated: bool = False
    error: Optional[str] = None


class EvaluateForJobResponse(BaseModel):
    """Response da avaliação em batch."""
    job_id: str
    total_candidates: int
    evaluated_count: int
    failed_count: int
    results: List[EvaluateForJobResult]


def _get_match_label(score: float) -> str:
    """Get match label based on rubric score."""
    if score >= 85:
        return "Exceeds"
    elif score >= 70:
        return "Meets"
    elif score >= 40:
        return "Partial"
    else:
        return "Missing"


async def _get_job_requirements(
    db: AsyncSession, 
    job_id: str
) -> Optional[List[JobRequirementCreate]]:
    """Fetch job requirements for a given job_id."""
    try:
        from sqlalchemy import select
        result = await db.execute(
            select(JobRequirement).where(
                JobRequirement.job_vacancy_id == UUID(job_id)
            )
        )
        db_requirements = result.scalars().all()
        
        if not db_requirements:
            return None
        
        return [
            JobRequirementCreate(
                requirement=req.requirement,
                description=req.description,
                priority=_normalize_priority(req.priority),
                category=req.category,
            )
            for req in db_requirements
        ]
    except Exception as e:
        logger.warning(f"Failed to fetch job requirements for job_id={job_id}: {e}")
        return None


def _build_candidate_data_from_dto(candidate_dto: "CandidateSearchResultDTO") -> Dict[str, Any]:
    """Build candidate data dict for rubric evaluation from CandidateSearchResultDTO."""
    work_history = []
    for exp in (candidate_dto.experiences or candidate_dto.work_history or []):
        work_history.append({
            "title": exp.title,
            "company_name": exp.company or exp.company_name,
            "start_date": exp.start_date,
            "end_date": exp.end_date,
            "description": exp.description,
            "technologies": exp.technologies or [],
        })
    
    education = []
    for edu in (candidate_dto.education or []):
        education.append({
            "degree": edu.degree,
            "institution": edu.school or edu.institution,
            "field_of_study": edu.field_of_study,
        })
    
    return {
        "id": candidate_dto.id,
        "name": candidate_dto.name,
        "current_title": candidate_dto.current_title,
        "current_company": candidate_dto.current_company,
        "years_of_experience": candidate_dto.total_experience_years,
        "skills": candidate_dto.skills or [],
        "technical_skills": candidate_dto.skills or [],
        "expertise": candidate_dto.expertise or [],
        "work_history": work_history,
        "education": education,
        "self_introduction": candidate_dto.summary,
    }


async def _evaluate_candidates_with_rubrics(
    candidates: List["CandidateSearchResultDTO"],
    requirements: List[JobRequirementCreate],
) -> List["CandidateSearchResultDTO"]:
    """
    Evaluate candidates using rubric evaluation service.
    Updates candidates in-place with rubric_score, rubric_match_label, and rubric_evaluated.
    """
    for candidate in candidates:
        try:
            candidate_data = _build_candidate_data_from_dto(candidate)
            result = await rubric_evaluation_service.evaluate_candidate(
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
    current_user: User = Depends(get_current_user_or_demo)
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
            pearch_type=SearchType(request.pearch_type) if request.pearch_type in ["fast", "pro"] else SearchType.FAST,
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
        result = await pearch_service.hybrid_search(db, hybrid_request)
        
        # Converte candidatos para DTO
        candidates = []
        
        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))
        
        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))
        
        # Rubric evaluation if job_id is provided
        if request.job_id and candidates:
            try:
                requirements = await _get_job_requirements(db, request.job_id)
                if requirements:
                    logger.info(f"Evaluating {len(candidates)} candidates with rubrics for job_id={request.job_id}")
                    candidates = await _evaluate_candidates_with_rubrics(candidates, requirements)
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
        
        return SearchResponseDTO(
            query=result.query,
            thread_id=result.thread_id,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=result.pearch_count,
            total_count=result.total_count,
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=(result.local_search_time or 0) + (result.pearch_search_time or 0),
            warning_message=result.warning_message,
            can_load_more=result.pearch_count >= request.pearch_limit,
            should_expand_to_global=should_expand,
            expansion_message=expansion_message,
            high_adherence_count=high_adherence_count
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/evaluate-for-job", response_model=EvaluateForJobResponse)
async def evaluate_candidates_for_job(
    request: EvaluateForJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Avalia candidatos em batch contra os requisitos de uma vaga usando rubricas.
    
    Útil para:
    - Avaliar candidatos já descobertos/importados
    - Re-avaliar candidatos após atualização de requisitos da vaga
    - Calcular score de match para candidatos de diferentes fontes
    
    Retorna rubric_score (0-100), rubric_match_label (Exceeds/Meets/Partial/Missing) 
    e rubric_evaluated para cada candidato.
    """
    from app.models.candidate import Candidate, ExternalCandidateProfile
    from sqlalchemy import select, or_
    
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
                    select(Candidate).where(Candidate.id == UUID(candidate_id))
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
                            ExternalCandidateProfile.id == UUID(candidate_id)
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
                eval_result = await rubric_evaluation_service.evaluate_candidate(
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
    
    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")


def _normalize_name(name: str) -> str:
    """Normaliza nome para comparação e deduplicação."""
    import unicodedata
    import re
    normalized = unicodedata.normalize('NFKD', name.lower())
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    normalized = re.sub(r'[^a-z\s]', '', normalized)
    normalized = ' '.join(normalized.split())
    return normalized


def _generate_fingerprint(name: str, linkedin_url: Optional[str] = None, email: Optional[str] = None) -> str:
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


from app.auth.dependencies import get_current_user_or_demo, get_user_company_id, assert_resource_ownership
from app.auth.models import User as ImportUser


@router.post("/candidates/import", response_model=ImportCandidatesResponse)
async def import_pearch_candidates(
    request: ImportCandidatesRequest,
    current_user: ImportUser = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Importa candidatos da busca Pearch para a TABELA DE STAGING (external_candidate_profiles).
    
    ARQUITETURA DE STAGING:
    - Candidatos descobertos NÃO vão para a base principal (candidates)
    - Ficam em staging até serem explicitamente "promovidos" pelo recrutador
    - Evita poluição da base com candidatos sem contato revelado
    
    SEGURANÇA:
    - company_id derivado do usuário autenticado via get_current_user_or_demo
    - Multi-tenant isolation garantido via company_id do usuário
    
    Use POST /candidates/promote/{profile_id} para promover um candidato para a base principal.
    """
    from app.models.candidate import ExternalCandidateProfile, Candidate, CandidateSource
    from sqlalchemy import select, or_
    import uuid as uuid_lib
    
    imported_ids = []
    skipped_ids = []
    updated_ids = []
    id_mappings = []
    company_id = get_user_company_id(current_user)
    
    try:
        for candidate_dto in request.candidates:
            fingerprint = _generate_fingerprint(
                candidate_dto.name,
                candidate_dto.linkedin_url,
                candidate_dto.email
            )
            
            existing_in_main = await db.execute(
                select(Candidate).where(
                    or_(
                        Candidate.pearch_profile_id == candidate_dto.pearch_id,
                        Candidate.linkedin_url == candidate_dto.linkedin_url
                    )
                ).limit(1)
            )
            existing_candidate = existing_in_main.scalars().first()
            if existing_candidate:
                skipped_ids.append(candidate_dto.pearch_id)
                id_mappings.append(IdMapping(
                    pearch_id=candidate_dto.pearch_id,
                    local_id=str(existing_candidate.id)
                ))
                continue
            
            staging_filters = [ExternalCandidateProfile.source_profile_id == candidate_dto.pearch_id]
            if candidate_dto.linkedin_url:
                staging_filters.append(ExternalCandidateProfile.linkedin_url == candidate_dto.linkedin_url)
            staging_filters.append(ExternalCandidateProfile.fingerprint_hash == fingerprint)
            
            existing_in_staging = await db.execute(
                select(ExternalCandidateProfile).where(
                    ExternalCandidateProfile.company_id == company_id,
                    or_(*staging_filters)
                ).limit(1)
            )
            existing_profile = existing_in_staging.scalars().first()
            
            if existing_profile:
                updated = False
                if candidate_dto.email and not existing_profile.email:
                    existing_profile.email = candidate_dto.email
                    existing_profile.has_email = True
                    existing_profile.contact_revealed = True
                    updated = True
                if candidate_dto.phone and not existing_profile.phone:
                    existing_profile.phone = candidate_dto.phone
                    existing_profile.has_phone = True
                    existing_profile.contact_revealed = True
                    updated = True
                if updated:
                    updated_ids.append(candidate_dto.pearch_id)
                else:
                    skipped_ids.append(candidate_dto.pearch_id)
                id_mappings.append(IdMapping(
                    pearch_id=candidate_dto.pearch_id,
                    local_id=str(existing_profile.id)
                ))
                continue
            
            location_city, location_state, location_country = None, None, None
            if candidate_dto.location:
                parts = [p.strip() for p in candidate_dto.location.split(",")]
                if len(parts) >= 1:
                    location_city = parts[0]
                if len(parts) >= 2:
                    location_state = parts[1]
                if len(parts) >= 3:
                    location_country = parts[2]
            
            name_parts = candidate_dto.name.split(' ', 1)
            first_name = candidate_dto.first_name or (name_parts[0] if len(name_parts) > 0 else None)
            last_name = candidate_dto.last_name or (name_parts[1] if len(name_parts) > 1 else None)
            
            experiences_snapshot = []
            for exp in candidate_dto.experiences:
                experiences_snapshot.append({
                    "company_name": exp.company_name,
                    "company_linkedin_url": exp.company_linkedin_url,
                    "company_domain": exp.company_domain,
                    "title": exp.title,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "duration_years": exp.duration_years,
                    "is_current": exp.is_current,
                    "description": exp.description,
                    "location": exp.location,
                    "industries": exp.industries or [],
                    "company_size": exp.company_size,
                    "company_size_range": exp.company_size_range,
                    "technologies": exp.technologies or [],
                    "is_startup": exp.is_startup,
                    "company_founded_year": exp.company_founded_year,
                    "company_annual_revenue": exp.company_annual_revenue,
                    # Campos Pearch company_info
                    "company_followers_count": exp.company_followers_count,
                    "company_keywords": exp.company_keywords or []
                })
            
            new_id = uuid_lib.uuid4()
            profile = ExternalCandidateProfile(
                id=new_id,
                company_id=company_id,
                source="pearch",
                source_profile_id=candidate_dto.pearch_id,
                linkedin_url=candidate_dto.linkedin_url,
                raw_payload={
                    "original_dto": candidate_dto.model_dump(),
                    "source_search_query": request.source_search_query
                },
                name=candidate_dto.name,
                normalized_name=_normalize_name(candidate_dto.name),
                first_name=first_name,
                last_name=last_name,
                email=candidate_dto.email,
                phone=candidate_dto.phone,
                avatar_url=candidate_dto.avatar_url,
                headline=candidate_dto.headline,
                summary=candidate_dto.summary,
                current_title=candidate_dto.current_title,
                current_company=candidate_dto.current_company,
                location_city=location_city,
                location_state=location_state,
                location_country=location_country,
                location_raw=candidate_dto.location,
                years_of_experience=int(candidate_dto.years_of_experience) if candidate_dto.years_of_experience else None,
                skills=candidate_dto.skills[:50] if candidate_dto.skills else [],
                expertise=candidate_dto.expertise[:20] if candidate_dto.expertise else [],
                languages={"items": candidate_dto.languages} if candidate_dto.languages else {},
                experiences_snapshot=experiences_snapshot,
                education_snapshot=candidate_dto.education,
                is_open_to_work=candidate_dto.is_open_to_work,
                is_decision_maker=candidate_dto.is_decision_maker,
                is_top_universities=candidate_dto.is_top_universities,
                has_email=bool(candidate_dto.email),
                has_phone=bool(candidate_dto.phone),
                contact_revealed=bool(candidate_dto.email or candidate_dto.phone),
                fingerprint_hash=fingerprint,
                status="discovered",
                search_query=request.source_search_query
            )
            db.add(profile)
            
            imported_ids.append(str(new_id))
            id_mappings.append(IdMapping(
                pearch_id=candidate_dto.pearch_id,
                local_id=str(new_id)
            ))
        
        await db.commit()
        
        return ImportCandidatesResponse(
            imported_count=len(imported_ids),
            skipped_count=len(skipped_ids),
            updated_count=len(updated_ids),
            imported_ids=imported_ids,
            skipped_ids=skipped_ids,
            mapping=id_mappings,
            message=f"Salvos {len(imported_ids)} candidatos descobertos em staging. {len(updated_ids)} atualizados. {len(skipped_ids)} já existiam."
        )
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Error importing candidates to staging: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


class PromoteCandidateResponse(BaseModel):
    """Response da promoção de candidato para a base principal."""
    success: bool
    message: str
    candidate_id: str
    profile_id: str
    was_merged: bool = False
    merged_with_id: Optional[str] = None


@router.post("/candidates/promote/{profile_id}", response_model=PromoteCandidateResponse)
async def promote_candidate_to_main_base(
    profile_id: str,
    current_user: ImportUser = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Promove um candidato descoberto (staging) para a base principal.
    
    FLUXO DE PROMOÇÃO:
    1. Busca o perfil em external_candidate_profiles
    2. Valida ownership (company_id derivado do usuário autenticado) e status (não promovido)
    3. Verifica se já existe candidato similar na base principal (por linkedin_url ou fingerprint)
    4. Se existe: faz merge dos dados (APENAS adiciona dados faltantes, não sobrescreve)
    5. Se não existe: cria novo candidato + CandidateSource + experiências + educação
    6. Atualiza o perfil de staging com promoted_to_candidate_id
    
    SEGURANÇA:
    - company_id derivado do usuário autenticado via get_current_user_or_demo
    - assert_resource_ownership valida isolamento multi-tenant
    - Bloqueia se já foi promovido
    - Merge preserva dados canônicos (não sobrescreve dados existentes)
    - Operação atômica com rollback em caso de erro
    
    Returns:
        PromoteCandidateResponse com o ID do candidato na base principal
    """
    from app.models.candidate import ExternalCandidateProfile, Candidate, CandidateSource, CandidateExperience, CandidateEducation
    from sqlalchemy import select, or_
    from datetime import datetime
    import uuid as uuid_lib
    
    user_company_id = get_user_company_id(current_user)
    
    try:
        profile_result = await db.execute(
            select(ExternalCandidateProfile).where(ExternalCandidateProfile.id == profile_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil não encontrado na staging")
        
        assert_resource_ownership(profile, current_user, "external_profile")
        
        if profile.promoted_to_candidate_id:
            return PromoteCandidateResponse(
                success=True,
                message="Candidato já foi promovido anteriormente",
                candidate_id=str(profile.promoted_to_candidate_id),
                profile_id=profile_id,
                was_merged=False
            )
        
        existing_candidate = None
        if profile.linkedin_url:
            existing_result = await db.execute(
                select(Candidate).where(Candidate.linkedin_url == profile.linkedin_url)
            )
            existing_candidate = existing_result.scalar_one_or_none()
        
        if not existing_candidate and profile.source_profile_id:
            existing_result = await db.execute(
                select(Candidate).where(Candidate.pearch_profile_id == profile.source_profile_id)
            )
            existing_candidate = existing_result.scalar_one_or_none()
        
        if existing_candidate:
            updated_fields = []
            if profile.email and not existing_candidate.email:
                existing_candidate.email = profile.email
                updated_fields.append("email")
            if profile.phone and not existing_candidate.phone:
                existing_candidate.phone = profile.phone
                updated_fields.append("phone")
            if profile.avatar_url and not existing_candidate.avatar_url:
                existing_candidate.avatar_url = profile.avatar_url
                updated_fields.append("avatar_url")
            if profile.summary and not existing_candidate.self_introduction:
                existing_candidate.self_introduction = profile.summary
                updated_fields.append("self_introduction")
            if profile.skills and not existing_candidate.technical_skills:
                existing_candidate.technical_skills = profile.skills
                updated_fields.append("technical_skills")
            
            # Campos exclusivos da busca global Pearch - SEMPRE sobrescrever com dados frescos
            # Usar raw_payload como fonte da verdade para determinar se campo foi retornado
            # O raw_payload pode ter estrutura { original_dto: {...} } ou os campos diretamente
            raw_payload_raw = profile.raw_payload or {}
            raw_payload = raw_payload_raw.get("original_dto", raw_payload_raw)
            
            # Campos booleanos - usar raw_payload como fonte da verdade
            # Quando Pearch retorna o campo, sobrescrever (inclusive com None para limpar dados antigos)
            # IMPORTANTE: Usar atribuição direta sem `or` para preservar valores False legítimos
            if "is_open_to_work" in raw_payload:
                existing_candidate.is_open_to_work = raw_payload["is_open_to_work"]
                updated_fields.append("is_open_to_work")
            elif "is_opentowork" in raw_payload:
                existing_candidate.is_open_to_work = raw_payload["is_opentowork"]
                updated_fields.append("is_open_to_work")
            if "is_decision_maker" in raw_payload:
                existing_candidate.is_decision_maker = raw_payload["is_decision_maker"]
                updated_fields.append("is_decision_maker")
            if "is_top_universities" in raw_payload:
                existing_candidate.is_top_universities = raw_payload["is_top_universities"]
                updated_fields.append("is_top_universities")
            if "is_hiring" in raw_payload:
                existing_candidate.is_hiring = raw_payload["is_hiring"]
                updated_fields.append("is_hiring")
            
            # Campos de texto - verificar raw_payload primeiro, depois fallback para profile
            # Quando Pearch omite um campo, NÃO sobrescrever (manter dados existentes)
            if "headline" in raw_payload:
                existing_candidate.headline = raw_payload.get("headline")
                updated_fields.append("headline")
            elif profile.headline is not None:
                existing_candidate.headline = profile.headline
                updated_fields.append("headline")
            
            if "expertise" in raw_payload:
                existing_candidate.expertise = raw_payload.get("expertise")
                updated_fields.append("expertise")
            elif profile.expertise is not None:
                existing_candidate.expertise = profile.expertise
                updated_fields.append("expertise")
            
            if "seniority_level" in raw_payload:
                existing_candidate.seniority_level = raw_payload.get("seniority_level")
                updated_fields.append("seniority_level")
            elif profile.seniority_level is not None:
                existing_candidate.seniority_level = profile.seniority_level
                updated_fields.append("seniority_level")
            
            if "best_personal_email" in raw_payload:
                existing_candidate.best_personal_email = raw_payload.get("best_personal_email")
                updated_fields.append("best_personal_email")
            elif profile.best_personal_email is not None:
                existing_candidate.best_personal_email = profile.best_personal_email
                updated_fields.append("best_personal_email")
            
            if "estimated_age" in raw_payload:
                existing_candidate.estimated_age = raw_payload.get("estimated_age")
                updated_fields.append("estimated_age")
            elif profile.estimated_age is not None:
                existing_candidate.estimated_age = profile.estimated_age
                updated_fields.append("estimated_age")
            
            # Campos JSON/dict - verificar raw_payload primeiro
            if "phone_types" in raw_payload:
                existing_candidate.phone_types = raw_payload.get("phone_types")
                updated_fields.append("phone_types")
            elif profile.phone_types is not None:
                existing_candidate.phone_types = profile.phone_types
                updated_fields.append("phone_types")
            
            # Construir pearch_insights a partir do raw_payload (insights + query_insights)
            if "insights" in raw_payload or profile.pearch_insights is not None:
                pearch_insights_data = {}
                raw_insights = raw_payload.get("insights", {})
                if raw_insights:
                    pearch_insights_data = {
                        "overall_summary": raw_insights.get("overall_summary"),
                        "query_insights": raw_insights.get("query_insights", []),
                        "match_reasoning": raw_payload.get("match_reasoning")
                    }
                elif profile.pearch_insights is not None:
                    pearch_insights_data = profile.pearch_insights
                existing_candidate.pearch_insights = pearch_insights_data
                updated_fields.append("pearch_insights")
            
            # Campos numéricos - verificar raw_payload primeiro (0 é válido)
            if "followers_count" in raw_payload or "linkedin_followers_count" in raw_payload:
                existing_candidate.linkedin_followers_count = raw_payload.get("followers_count") or raw_payload.get("linkedin_followers_count")
                updated_fields.append("linkedin_followers_count")
            elif profile.linkedin_followers_count is not None:
                existing_candidate.linkedin_followers_count = profile.linkedin_followers_count
                updated_fields.append("linkedin_followers_count")
            
            if "connections_count" in raw_payload or "linkedin_connections_count" in raw_payload:
                existing_candidate.linkedin_connections_count = raw_payload.get("connections_count") or raw_payload.get("linkedin_connections_count")
                updated_fields.append("linkedin_connections_count")
            elif profile.linkedin_connections_count is not None:
                existing_candidate.linkedin_connections_count = profile.linkedin_connections_count
                updated_fields.append("linkedin_connections_count")
            
            # Campo outreach_message - verificar raw_payload primeiro
            if "outreach_message" in raw_payload:
                existing_candidate.outreach_message = raw_payload.get("outreach_message")
                updated_fields.append("outreach_message")
            elif profile.outreach_message is not None:
                existing_candidate.outreach_message = profile.outreach_message
                updated_fields.append("outreach_message")
            
            # Novos campos Pearch - middle_name, emails de negócio/pessoais
            if "middle_name" in raw_payload:
                existing_candidate.middle_name = raw_payload.get("middle_name")
                updated_fields.append("middle_name")
            
            if "best_business_email" in raw_payload:
                existing_candidate.best_business_email = raw_payload.get("best_business_email")
                updated_fields.append("best_business_email")
            
            if "personal_emails" in raw_payload:
                existing_candidate.personal_emails = raw_payload.get("personal_emails", [])
                updated_fields.append("personal_emails")
            
            if "business_emails" in raw_payload:
                existing_candidate.business_emails = raw_payload.get("business_emails", [])
                updated_fields.append("business_emails")
            
            # Campos de company_info da primeira experiência
            # Suporta formato API Pearch (company_info aninhado) e DTO (campos diretos)
            experiences_data = raw_payload.get("experiences", [])
            if experiences_data and len(experiences_data) > 0:
                first_exp = experiences_data[0] if isinstance(experiences_data[0], dict) else {}
                # Primeiro tenta o formato API Pearch (company_info aninhado)
                company_info = first_exp.get("company_info", {})
                if company_info:
                    if "followers_count" in company_info:
                        existing_candidate.company_followers_count = company_info.get("followers_count")
                        updated_fields.append("company_followers_count")
                    if "keywords" in company_info:
                        existing_candidate.company_keywords = company_info.get("keywords", [])
                        updated_fields.append("company_keywords")
                # Se não tiver company_info, usa campos diretos do DTO
                if "company_followers_count" not in updated_fields and "company_followers_count" in first_exp:
                    existing_candidate.company_followers_count = first_exp.get("company_followers_count")
                    updated_fields.append("company_followers_count")
                if "company_keywords" not in updated_fields and "company_keywords" in first_exp:
                    existing_candidate.company_keywords = first_exp.get("company_keywords", [])
                    updated_fields.append("company_keywords")
            
            existing_source = await db.execute(
                select(CandidateSource).where(
                    CandidateSource.candidate_id == existing_candidate.id,
                    CandidateSource.source == profile.source
                )
            )
            if not existing_source.scalar_one_or_none():
                source = CandidateSource(
                    candidate_id=existing_candidate.id,
                    source=profile.source,
                    source_profile_id=profile.source_profile_id,
                    linkedin_url=profile.linkedin_url,
                    fingerprint_hash=profile.fingerprint_hash,
                    is_primary=False,
                    external_profile_id=profile.id
                )
                db.add(source)
            
            profile.promoted_to_candidate_id = existing_candidate.id
            profile.promoted_at = datetime.utcnow()
            profile.status = "promoted_merged"
            
            await db.commit()
            
            return PromoteCandidateResponse(
                success=True,
                message=f"Candidato mesclado com existente. Campos atualizados: {', '.join(updated_fields) if updated_fields else 'nenhum (dados já completos)'}",
                candidate_id=str(existing_candidate.id),
                profile_id=profile_id,
                was_merged=True,
                merged_with_id=str(existing_candidate.id)
            )
        
        new_candidate_id = uuid_lib.uuid4()
        
        # Extrair insights da Pearch do raw_payload se disponível
        # O raw_payload pode ter estrutura { original_dto: {...} } ou os campos diretamente
        raw_payload_raw = profile.raw_payload or {}
        raw_payload = raw_payload_raw.get("original_dto", raw_payload_raw)
        pearch_insights_data = {}
        if raw_payload.get("insights"):
            pearch_insights_data = {
                "overall_summary": raw_payload.get("insights", {}).get("overall_summary"),
                "query_insights": raw_payload.get("insights", {}).get("query_insights", []),
                "match_reasoning": raw_payload.get("match_reasoning")
            }
        
        # Extrair company_info da primeira experiência (se disponível)
        # Suporta formato API Pearch (company_info aninhado) e DTO (campos diretos)
        company_followers_count = None
        company_keywords = None
        experiences_data = raw_payload.get("experiences", [])
        if experiences_data and len(experiences_data) > 0:
            first_exp = experiences_data[0] if isinstance(experiences_data[0], dict) else {}
            # Primeiro tenta o formato API Pearch (company_info aninhado)
            company_info = first_exp.get("company_info", {})
            if company_info:
                company_followers_count = company_info.get("followers_count")
                company_keywords = company_info.get("keywords", [])
            # Se não tiver company_info, usa campos diretos do DTO
            if company_followers_count is None:
                company_followers_count = first_exp.get("company_followers_count")
            if not company_keywords:
                company_keywords = first_exp.get("company_keywords", [])
        
        candidate = Candidate(
            id=new_candidate_id,
            name=profile.name,
            email=profile.email,
            phone=profile.phone,
            linkedin_url=profile.linkedin_url,
            avatar_url=profile.avatar_url,
            current_title=profile.current_title,
            current_company=profile.current_company,
            seniority_level=profile.seniority_level,
            self_introduction=profile.summary,
            headline=profile.headline,
            location_city=profile.location_city,
            location_state=profile.location_state,
            location_country=profile.location_country,
            years_of_experience=profile.years_of_experience,
            technical_skills=profile.skills or [],
            expertise=profile.expertise or [],
            languages=profile.languages or {},
            source="pearch",
            pearch_profile_id=profile.source_profile_id,
            # Campos exclusivos da busca global Pearch
            is_open_to_work=profile.is_open_to_work,
            is_decision_maker=profile.is_decision_maker,
            is_top_universities=profile.is_top_universities,
            is_hiring=raw_payload.get("is_hiring"),
            linkedin_followers_count=raw_payload.get("followers_count"),
            linkedin_connections_count=raw_payload.get("connections_count"),
            pearch_insights=pearch_insights_data,
            outreach_message=raw_payload.get("outreach_message") or getattr(profile, 'outreach_message', None),
            best_personal_email=getattr(profile, 'best_personal_email', None) or raw_payload.get("best_personal_email"),
            phone_types=getattr(profile, 'phone_types', None) or raw_payload.get("phone_types", {}),
            estimated_age=getattr(profile, 'estimated_age', None) or raw_payload.get("estimated_age"),
            # Novos campos Pearch
            middle_name=raw_payload.get("middle_name"),
            best_business_email=raw_payload.get("best_business_email"),
            personal_emails=raw_payload.get("personal_emails", []),
            business_emails=raw_payload.get("business_emails", []),
            company_followers_count=company_followers_count,
            company_keywords=company_keywords,
            status="new",
            is_active=True,
            additional_data={
                "promoted_from_staging": True,
                "original_profile_id": str(profile.id)
            }
        )
        db.add(candidate)
        
        source = CandidateSource(
            candidate_id=new_candidate_id,
            source=profile.source,
            source_profile_id=profile.source_profile_id,
            linkedin_url=profile.linkedin_url,
            fingerprint_hash=profile.fingerprint_hash,
            is_primary=True,
            external_profile_id=profile.id
        )
        db.add(source)
        
        for idx, exp_data in enumerate(profile.experiences_snapshot or []):
            experience = CandidateExperience(
                candidate_id=new_candidate_id,
                company_name=exp_data.get("company_name", "Unknown"),
                company_linkedin_url=exp_data.get("company_linkedin_url"),
                company_domain=exp_data.get("company_domain"),
                title=exp_data.get("title"),
                start_date=exp_data.get("start_date"),
                end_date=exp_data.get("end_date"),
                duration_years=exp_data.get("duration_years"),
                is_current=exp_data.get("is_current", False),
                description=exp_data.get("description"),
                location=exp_data.get("location"),
                industries=exp_data.get("industries", []),
                company_size=exp_data.get("company_size"),
                company_size_range=exp_data.get("company_size_range"),
                technologies=exp_data.get("technologies", []),
                is_startup=exp_data.get("is_startup"),
                company_founded_year=exp_data.get("company_founded_year"),
                company_annual_revenue=exp_data.get("company_annual_revenue"),
                sequence_order=idx
            )
            db.add(experience)
        
        for idx, edu_data in enumerate(profile.education_snapshot or []):
            education = CandidateEducation(
                candidate_id=new_candidate_id,
                institution=edu_data.get("school") or edu_data.get("institution"),
                degree=edu_data.get("degree"),
                field_of_study=edu_data.get("field_of_study") or edu_data.get("field"),
                start_date=edu_data.get("start_date"),
                end_date=edu_data.get("end_date"),
                is_completed=True if edu_data.get("end_date") else False,
                sequence_order=idx
            )
            db.add(education)
        
        profile.promoted_to_candidate_id = new_candidate_id
        profile.promoted_at = datetime.utcnow()
        profile.status = "promoted"
        
        await db.commit()
        
        return PromoteCandidateResponse(
            success=True,
            message="Candidato promovido para a base principal com sucesso",
            candidate_id=str(new_candidate_id),
            profile_id=profile_id,
            was_merged=False
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error promoting candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Promotion failed: {str(e)}")


class RevealedContactDTO(BaseModel):
    """Dados de contato revelado para persistência."""
    pearch_id: str = Field(..., description="ID do candidato na Pearch")
    candidate_name: str = Field(..., description="Nome do candidato")
    email: Optional[str] = Field(None, description="Email revelado")
    phone: Optional[str] = Field(None, description="Telefone revelado")
    linkedin_url: Optional[str] = Field(None, description="URL do LinkedIn")
    current_title: Optional[str] = Field(None, description="Cargo atual")
    current_company: Optional[str] = Field(None, description="Empresa atual")
    avatar_url: Optional[str] = Field(None, description="URL do avatar")


class RevealedContactResponse(BaseModel):
    """Response da persistência de contato revelado."""
    success: bool
    message: str
    candidate_id: Optional[str] = None
    is_new: bool = False


@router.post("/candidates/persist-revealed", response_model=RevealedContactResponse)
async def persist_revealed_contact(
    request: RevealedContactDTO,
    db: AsyncSession = Depends(get_db)
):
    """
    Persiste dados de contato revelados de candidatos Pearch.
    
    Quando o recrutador paga créditos para revelar email ou telefone,
    este endpoint salva automaticamente os dados no banco local.
    
    - Se o candidato já existe (por pearch_id): atualiza os dados de contato
    - Se não existe: cria um novo registro com os dados revelados
    """
    from app.models.candidate import Candidate
    from sqlalchemy import select
    import uuid as uuid_lib
    
    try:
        # Check if candidate already exists by pearch_id
        existing = await db.execute(
            select(Candidate).where(Candidate.pearch_profile_id == request.pearch_id)
        )
        candidate = existing.scalar_one_or_none()
        
        if candidate:
            # Update existing candidate with revealed contact
            updated = False
            if request.email and not candidate.email:
                candidate.email = request.email
                updated = True
            if request.phone and not candidate.phone:
                candidate.phone = request.phone
                updated = True
            
            if updated:
                await db.commit()
                return RevealedContactResponse(
                    success=True,
                    message="Dados de contato atualizados no cadastro existente",
                    candidate_id=str(candidate.id),
                    is_new=False
                )
            else:
                return RevealedContactResponse(
                    success=True,
                    message="Candidato já possui os dados de contato",
                    candidate_id=str(candidate.id),
                    is_new=False
                )
        else:
            # Create new candidate with basic info + revealed contact
            name_parts = request.candidate_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
            
            new_id = uuid_lib.uuid4()
            candidate = Candidate(
                id=new_id,
                name=request.candidate_name,
                first_name=first_name,
                last_name=last_name,
                email=request.email,
                phone=request.phone,
                linkedin_url=request.linkedin_url,
                avatar_url=request.avatar_url,
                current_title=request.current_title,
                current_company=request.current_company,
                source="pearch",
                pearch_profile_id=request.pearch_id,
                status="new",
                is_active=True,
                additional_data={
                    "imported_via": "reveal_contact",
                    "has_revealed_email": request.email is not None,
                    "has_revealed_phone": request.phone is not None
                }
            )
            db.add(candidate)
            await db.commit()
            
            return RevealedContactResponse(
                success=True,
                message="Candidato salvo na base local com dados de contato",
                candidate_id=str(new_id),
                is_new=True
            )
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Error persisting revealed contact: {e}")
        raise HTTPException(status_code=500, detail=f"Persist failed: {str(e)}")


class CreditEstimateRequest(BaseModel):
    """Request completo para estimativa de créditos."""
    query: str = Field(..., description="Query de busca")
    pearch_type: str = Field("fast", description="Tipo: fast ou pro")
    limit: int = Field(15, ge=1, le=50)
    
    # Opções de qualidade
    insights: bool = Field(True, description="Incluir insights (+1 crédito)")
    high_freshness: bool = Field(False, description="Dados em tempo real (+2 créditos)")
    profile_scoring: bool = Field(True, description="Scoring (+1 crédito)")
    strict_filters: bool = Field(False, description="Filtros rigorosos")
    
    # Opções de contato
    require_emails: bool = Field(False, description="Apenas com email (+1 crédito)")
    show_emails: bool = Field(False, description="Mostrar emails (+2 créditos)")
    require_phone_numbers: bool = Field(False, description="Apenas com telefone (+1 crédito)")
    show_phone_numbers: bool = Field(False, description="Mostrar telefones (+14 créditos)")
    require_phones_or_emails: bool = Field(False, description="Email OU telefone (+1 crédito)")


class DetailedCreditEstimateDTO(BaseModel):
    """Estimativa detalhada de créditos."""
    query: str
    pearch_type: str
    limit: int
    
    # Custos individuais
    base_cost: int
    insights_cost: int
    freshness_cost: int
    email_cost: int
    phone_cost: int
    
    # Totais
    cost_per_candidate: int
    total_estimated: int
    
    # Breakdown para UI
    breakdown: dict = Field(default_factory=dict)
    
    # Mensagem formatada
    confirmation_message: str
    
    # Alertas de custo
    warnings: List[str] = Field(default_factory=list)


@router.post("/candidates/estimate", response_model=DetailedCreditEstimateDTO)
async def estimate_search_credits(request: CreditEstimateRequest):
    """
    Estima o custo em créditos ANTES de executar a busca.
    
    Use este endpoint para mostrar ao usuário quanto a busca irá custar.
    Aceita todos os parâmetros Pearch para cálculo preciso.
    """
    if request.pearch_type not in ["fast", "pro"]:
        raise HTTPException(status_code=400, detail="pearch_type must be 'fast' or 'pro'")
    
    pearch_request = PearchSearchRequest(
        query=request.query,
        type=SearchType(request.pearch_type),
        insights=request.insights,
        high_freshness=request.high_freshness,
        profile_scoring=request.profile_scoring,
        custom_filters=None,
        strict_filters=request.strict_filters,
        require_emails=request.require_emails,
        show_emails=request.show_emails,
        require_phone_numbers=request.require_phone_numbers,
        require_phones_or_emails=request.require_phones_or_emails,
        show_phone_numbers=request.show_phone_numbers,
        limit=request.limit
    )
    
    estimate = pearch_service.estimate_credits(pearch_request)
    confirmation = pearch_service.create_confirmation_message(pearch_request)
    
    # Gerar alertas de custo
    warnings = []
    if request.show_phone_numbers:
        warnings.append("Exibir telefones adiciona +14 créditos por candidato - custo significativo!")
    if estimate.total_estimated > 100:
        warnings.append(f"Custo total estimado alto: {estimate.total_estimated} créditos")
    if request.pearch_type == "pro" and request.limit > 30:
        warnings.append("Busca profissional com muitos resultados pode consumir créditos rapidamente")
    
    return DetailedCreditEstimateDTO(
        query=request.query,
        pearch_type=request.pearch_type,
        limit=request.limit,
        base_cost=estimate.base_cost,
        insights_cost=estimate.insights_cost,
        freshness_cost=estimate.freshness_cost,
        email_cost=estimate.email_cost,
        phone_cost=estimate.phone_cost,
        cost_per_candidate=estimate.total_per_candidate,
        total_estimated=estimate.total_estimated,
        breakdown={
            "base": estimate.base_cost,
            "insights": estimate.insights_cost,
            "emails": estimate.email_cost,
            "phones": estimate.phone_cost,
            "freshness": estimate.freshness_cost
        },
        confirmation_message=confirmation.confirmation_message,
        warnings=warnings
    )


class SimilarSearchRequest(BaseModel):
    """Request para busca de candidatos similares."""
    linkedin_url: Optional[str] = Field(None, description="URL do LinkedIn do candidato referência")
    candidate_id: Optional[str] = Field(None, description="ID do candidato no banco local")
    limit: int = Field(20, ge=1, le=50, description="Número de resultados")
    search_pearch: bool = Field(True, description="Buscar também na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo: 'fast' ou 'pro'")


class SimilarSearchResponse(BaseModel):
    """Response da busca por similares."""
    reference_profile: Optional[dict] = Field(None, description="Perfil de referência usado")
    query_generated: str = Field(..., description="Query gerada a partir do perfil")
    candidates: List[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: Optional[int] = None
    search_time_seconds: Optional[float] = None


@router.post("/similar", response_model=SimilarSearchResponse)
async def search_similar_candidates(
    request: SimilarSearchRequest,
    db: AsyncSession = Depends(get_db)
):
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
                select(Candidate).where(Candidate.id == uuid.UUID(request.candidate_id))
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
            pearch_type=SearchType(request.pearch_type) if request.pearch_type in ["fast", "pro"] else SearchType.FAST,
            local_limit=request.limit,
            pearch_limit=request.limit,
            exclude_candidate_ids=[request.candidate_id] if request.candidate_id else []
        )
        
        result = await pearch_service.hybrid_search(db, hybrid_request)
        
        candidates = []
        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))
        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))
        
        return SimilarSearchResponse(
            reference_profile=reference_profile,
            query_generated=generated_query,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=result.pearch_count,
            total_count=result.total_count,
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=(result.local_search_time or 0) + (result.pearch_search_time or 0)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar search failed: {str(e)}")


# ============================================================================
# COMBINED PROFILE ENDPOINT - Merge multiple profiles into ideal candidate
# ============================================================================

class CombinedProfileResponse(BaseModel):
    """Response for combined profile analysis."""
    keywords: List[str] = Field(default_factory=list, description="Keywords for ideal candidate search")
    title: Optional[str] = Field(None, description="Suggested job title")
    seniority: Optional[str] = Field(None, description="Suggested seniority level")
    skills_technical: List[str] = Field(default_factory=list, description="Technical skills")
    skills_soft: List[str] = Field(default_factory=list, description="Soft skills")
    industries: List[str] = Field(default_factory=list, description="Target industries")
    location: Optional[str] = Field(None, description="Preferred location")
    summary: Optional[str] = Field(None, description="Combined profile summary")
    source_count: int = Field(0, description="Number of sources analyzed")


@router.post("/similar/combine-profiles", response_model=CombinedProfileResponse)
async def combine_profiles_for_search(
    urls: List[str] = Form(default=[]),
    cvs: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db)
):
    """
    Combine multiple candidate profiles (URLs and/or CVs) into an ideal profile.
    
    Analyzes 2-3 profiles and extracts:
    - Common skills (intersection - higher weight)
    - Unique strengths from each profile
    - Suggested seniority and location
    
    Returns keywords and structured profile for similar search.
    """
    from collections import Counter
    import re
    
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
            name_parts = profile_slug.replace('-', ' ').title().split()
            
            common_titles = ["Developer", "Engineer", "Analyst", "Manager", "Designer"]
            common_skills = ["Python", "JavaScript", "SQL", "AWS", "React"]
            
            all_titles.append("Software Engineer")
            all_skills.extend(common_skills[:3])
            all_seniorities.append("Sênior")
    
    for cv_file in cvs:
        try:
            # Use the real CV parser service for intelligent extraction
            parsed_cv = await cv_parser_service.parse_cv(cv_file)
            
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


class JobDescriptionSearchRequest(BaseModel):
    """Request para busca por job description."""
    job_description: str = Field(..., min_length=50, description="Descrição completa da vaga")
    location: Optional[str] = Field(None, description="Localização preferida")
    limit: int = Field(20, ge=1, le=50)
    search_pearch: bool = Field(True, description="Buscar também na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo: 'fast' ou 'pro'")


class ExtractedCriteria(BaseModel):
    """Critérios extraídos da job description."""
    job_title: Optional[str] = None
    seniority: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = None
    location: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)


class JobDescriptionSearchResponse(BaseModel):
    """Response da busca por job description."""
    extracted_criteria: ExtractedCriteria
    query_generated: str
    candidates: List[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: Optional[int] = None
    search_time_seconds: Optional[float] = None


@router.post("/by-job-description", response_model=JobDescriptionSearchResponse)
async def search_by_job_description(
    request: JobDescriptionSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca candidatos a partir de uma descrição de vaga completa.
    
    Extrai automaticamente critérios (skills, experiência, localização) 
    e gera uma query otimizada para encontrar candidatos compatíveis.
    """
    import re
    
    jd_lower = request.job_description.lower()
    extracted = ExtractedCriteria()
    
    job_titles = [
        'desenvolvedor', 'developer', 'engenheiro', 'engineer', 'analista', 'analyst',
        'gerente', 'manager', 'coordenador', 'coordinator', 'designer', 'architect',
        'data scientist', 'cientista de dados', 'devops', 'sre', 'qa', 'tester',
        'product manager', 'scrum master', 'tech lead', 'líder técnico'
    ]
    for title in job_titles:
        if title in jd_lower:
            extracted.job_title = title.title()
            break
    
    seniority_patterns = {
        r'\b(júnior|junior|jr)\b': 'Junior',
        r'\b(pleno|mid|mid-level)\b': 'Pleno',
        r'\b(sênior|senior|sr)\b': 'Senior',
        r'\b(staff|principal)\b': 'Staff',
        r'\b(lead|líder)\b': 'Lead'
    }
    for pattern, level in seniority_patterns.items():
        if re.search(pattern, jd_lower):
            extracted.seniority = level
            break
    
    skills_list = [
        'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
        'node', 'nodejs', 'django', 'flask', 'fastapi', 'spring', 'aws', 'gcp',
        'azure', 'docker', 'kubernetes', 'terraform', 'sql', 'postgresql', 'mongodb',
        'redis', 'kafka', 'rabbitmq', 'graphql', 'rest', 'api', 'git', 'ci/cd',
        'machine learning', 'ml', 'deep learning', 'tensorflow', 'pytorch',
        'pandas', 'numpy', 'spark', 'hadoop', 'airflow', 'dbt', 'tableau', 'power bi',
        'figma', 'sketch', 'adobe xd', 'jira', 'confluence', 'scrum', 'agile'
    ]
    found_skills = [s for s in skills_list if s in jd_lower]
    extracted.skills = list(set(found_skills))[:10]
    
    exp_match = re.search(r'(\d+)\s*(?:\+)?\s*(?:anos?|years?)', jd_lower)
    if exp_match:
        extracted.experience_years = int(exp_match.group(1))
    
    languages = ['inglês', 'english', 'espanhol', 'spanish', 'português', 'french', 'francês']
    found_languages = [l for l in languages if l in jd_lower]
    extracted.languages = list(set(found_languages))
    
    if request.location:
        extracted.location = request.location
    else:
        locations = ['são paulo', 'sp', 'rio de janeiro', 'rj', 'belo horizonte', 'curitiba', 
                    'porto alegre', 'brasília', 'remoto', 'remote', 'híbrido', 'hybrid']
        for loc in locations:
            if loc in jd_lower:
                extracted.location = loc.title()
                break
    
    query_parts = []
    if extracted.job_title:
        query_parts.append(extracted.job_title)
    if extracted.seniority:
        query_parts.append(extracted.seniority)
    if extracted.skills:
        query_parts.append(" ".join(extracted.skills[:5]))
    if extracted.experience_years:
        query_parts.append(f"{extracted.experience_years}+ anos")
    if extracted.location:
        query_parts.append(f"em {extracted.location}")
    
    generated_query = " ".join(query_parts) if query_parts else "profissional"
    
    try:
        hybrid_request = HybridSearchRequest(
            query=generated_query,
            search_local_first=True,
            include_pearch=request.search_pearch,
            pearch_type=SearchType(request.pearch_type) if request.pearch_type in ["fast", "pro"] else SearchType.FAST,
            local_limit=request.limit,
            pearch_limit=request.limit
        )
        
        result = await pearch_service.hybrid_search(db, hybrid_request)
        
        candidates = []
        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))
        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))
        
        return JobDescriptionSearchResponse(
            extracted_criteria=extracted,
            query_generated=generated_query,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=result.pearch_count,
            total_count=result.total_count,
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=(result.local_search_time or 0) + (result.pearch_search_time or 0)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job description search failed: {str(e)}")


@router.post("/candidates/refine", response_model=SearchResponseDTO)
async def refine_search(
    thread_id: str = Query(..., description="Thread ID da busca anterior"),
    additional_query: str = Query(..., description="Critérios adicionais"),
    limit: Optional[int] = Query(None, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Refina uma busca existente usando o thread_id.
    
    Use para adicionar critérios ou pedir mais resultados sem custo completo.
    """
    try:
        result = await pearch_service.refine_search(
            thread_id=thread_id,
            additional_query=additional_query,
            limit=limit
        )
        
        candidates = [
            CandidateSearchResultDTO.from_profile(profile, "pearch")
            for profile in result.get_candidates()
        ]
        
        return SearchResponseDTO(
            query=additional_query,
            thread_id=result.thread_id,
            candidates=candidates,
            pearch_count=len(candidates),
            total_count=len(candidates),
            credits_remaining=result.credits_remaining,
            search_time_seconds=result.search_time_seconds
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refine failed: {str(e)}")


@router.get("/candidates/local", response_model=SearchResponseDTO)
async def search_local_only(
    query: str = Query(..., description="Query de busca"),
    limit: int = Query(20, ge=1, le=100),
    industries: Optional[str] = Query(None, description="Setores separados por vírgula (ex: Tecnologia,Fintech)"),
    require_email: bool = Query(False, description="Apenas candidatos com email"),
    require_phone: bool = Query(False, description="Apenas candidatos com telefone"),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca APENAS no banco de dados local (sem custo de créditos).
    
    Útil para verificar se já temos candidatos antes de usar Pearch.
    Suporta filtros por setores/indústrias e disponibilidade de contato.
    """
    try:
        # Parse industries string para lista
        industries_list = None
        if industries:
            industries_list = [ind.strip() for ind in industries.split(',') if ind.strip()]
        
        profiles, count = await pearch_service.search_local_candidates(
            db=db,
            query=query,
            limit=limit,
            industries=industries_list,
            require_email=require_email,
            require_phone=require_phone
        )
        
        candidates = [
            CandidateSearchResultDTO.from_profile(profile, "local")
            for profile in profiles
        ]
        
        return SearchResponseDTO(
            query=query,
            candidates=candidates,
            local_count=count,
            total_count=count
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local search failed: {str(e)}")


class ParseQueryRequest(BaseModel):
    """Request para parsing de query em linguagem natural."""
    query: str = Field(..., min_length=1, max_length=500)


class ParsedEntities(BaseModel):
    """Entidades extraídas da query."""
    location: Optional[str] = None
    job_title: Optional[str] = None
    years_experience: Optional[str] = None
    industry: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None
    company: Optional[str] = None


class ParseQueryResponse(BaseModel):
    """Response do parsing de query."""
    query: str
    entities: ParsedEntities
    confidence: float = 0.0
    suggestions: List[str] = Field(default_factory=list)


@router.post("/parse-query", response_model=ParseQueryResponse)
async def parse_search_query(request: ParseQueryRequest):
    """
    Extrai entidades de uma query de busca em linguagem natural.
    
    Usado para preencher tags dinâmicas no SmartSearchInput.
    Análise rápida sem custo de créditos.
    """
    import re
    
    query = request.query.lower().strip()
    entities = ParsedEntities()
    confidence = 0.0
    suggestions = []
    
    # ============================================
    # 1. LOCATION - Cidades, Estados, Países, Modelo de Trabalho
    # ============================================
    brazilian_cities = [
        'são paulo', 'sp', 'rio de janeiro', 'rj', 'belo horizonte', 'bh', 
        'brasília', 'df', 'curitiba', 'porto alegre', 'poa', 'salvador', 
        'fortaleza', 'recife', 'manaus', 'belém', 'goiânia', 'guarulhos',
        'campinas', 'são bernardo', 'santo andré', 'osasco', 'sorocaba',
        'ribeirão preto', 'uberlândia', 'contagem', 'niterói', 'florianópolis',
        'joinville', 'londrina', 'juiz de fora', 'santos', 'são josé dos campos',
        'natal', 'joão pessoa', 'maceió', 'teresina', 'campo grande', 'cuiabá',
        'aracaju', 'vitória', 'são luís', 'vila velha', 'feira de santana'
    ]
    
    brazilian_states = [
        'minas gerais', 'mg', 'rio grande do sul', 'rs', 'paraná', 'pr',
        'santa catarina', 'sc', 'bahia', 'ba', 'pernambuco', 'pe', 'ceará', 'ce',
        'goiás', 'go', 'espírito santo', 'es', 'pará', 'pa', 'amazonas', 'am',
        'maranhão', 'ma', 'mato grosso', 'mt', 'mato grosso do sul', 'ms',
        'rio grande do norte', 'rn', 'paraíba', 'pb', 'alagoas', 'al',
        'piauí', 'pi', 'sergipe', 'se', 'tocantins', 'to', 'acre', 'ac',
        'amapá', 'ap', 'rondônia', 'ro', 'roraima', 'rr'
    ]
    
    work_models = ['remote', 'remoto', 'híbrido', 'hibrido', 'presencial', 'home office', 'anywhere', 'global']
    countries_regions = ['brasil', 'brazil', 'usa', 'eua', 'estados unidos', 'europa', 'latam', 'américa latina', 'portugal', 'argentina', 'chile', 'méxico', 'canada', 'uk', 'reino unido', 'alemanha', 'espanha']
    
    all_locations = brazilian_cities + brazilian_states + work_models + countries_regions
    location_pattern = r'\b(' + '|'.join(re.escape(loc) for loc in all_locations) + r')\b'
    
    match = re.search(location_pattern, query, re.IGNORECASE)
    if match:
        entities.location = match.group(0).strip().title()
        confidence += 0.2
    else:
        em_pattern = r'\bem\s+([a-záàâãéèêíïóôõöúçñ\s]{3,25})(?:\s+com|\s+que|\s+de|\s+e\s|,|$)'
        match = re.search(em_pattern, query, re.IGNORECASE)
        if match:
            potential_loc = match.group(1).strip()
            if len(potential_loc) >= 3 and potential_loc not in ['experiência', 'experiencia', 'empresa', 'startup']:
                entities.location = potential_loc.title()
                confidence += 0.15
    
    # ============================================
    # 2. JOB TITLE - Cargos e Funções
    # ============================================
    job_titles = [
        # Product & Management
        'product manager', 'product managers', 'gerente de produto', 'pm', 'product owner', 'po',
        'project manager', 'gerente de projeto', 'program manager', 'scrum master', 'agile coach',
        'tech lead', 'technical lead', 'líder técnico', 'engineering manager', 'gerente de engenharia',
        'cto', 'cio', 'vp engineering', 'head of engineering', 'diretor de tecnologia',
        
        # Development
        'desenvolvedor', 'desenvolvedora', 'developer', 'programador', 'programadora',
        'engenheiro de software', 'engenheira de software', 'software engineer',
        'fullstack', 'full-stack', 'full stack', 'frontend', 'front-end', 'front end',
        'backend', 'back-end', 'back end', 'mobile developer', 'desenvolvedor mobile',
        'ios developer', 'android developer', 'react developer', 'java developer',
        'python developer', 'node developer', 'golang developer', '.net developer',
        
        # Data & AI
        'data scientist', 'cientista de dados', 'data engineer', 'engenheiro de dados',
        'data analyst', 'analista de dados', 'ml engineer', 'machine learning engineer',
        'ai engineer', 'engenheiro de ia', 'bi analyst', 'analista de bi',
        'data architect', 'arquiteto de dados',
        
        # DevOps & Infrastructure
        'devops', 'devops engineer', 'sre', 'site reliability engineer',
        'cloud engineer', 'engenheiro de cloud', 'platform engineer',
        'infrastructure engineer', 'network engineer', 'security engineer',
        'devsecops', 'cloud architect', 'arquiteto de soluções', 'solutions architect',
        
        # QA & Testing
        'qa', 'qa engineer', 'quality assurance', 'tester', 'test engineer',
        'automation engineer', 'sdet', 'qa analyst', 'analista de qualidade',
        
        # Design
        'designer', 'ux designer', 'ui designer', 'ux/ui', 'product designer',
        'visual designer', 'graphic designer', 'motion designer', 'ux researcher',
        
        # Other Tech
        'arquiteto', 'arquiteta', 'architect', 'analista', 'analyst', 'consultor', 'consultant',
        'especialista', 'specialist', 'coordenador', 'coordenadora', 'supervisor', 'supervisora',
        'gerente', 'manager', 'diretor', 'diretora', 'director', 'head', 'chief',
        
        # Support & Operations
        'support engineer', 'suporte técnico', 'help desk', 'dba', 'database administrator',
        'system administrator', 'sysadmin', 'administrador de sistemas'
    ]
    
    job_pattern = r'\b(' + '|'.join(re.escape(title) for title in job_titles) + r')\b'
    match = re.search(job_pattern, query, re.IGNORECASE)
    if match:
        entities.job_title = match.group(0).strip().title()
        confidence += 0.2
    
    # ============================================
    # 3. EXPERIENCE - Anos de experiência e senioridade
    # ============================================
    exp_patterns = [
        (r'(\d+)\s*\+?\s*(?:anos?|years?|yrs?)\s*(?:de\s+)?(?:experiência|experience|exp)?', 'years'),
        (r'(?:experiência|experience|exp)\s*(?:de\s+)?(\d+)\s*\+?\s*(?:anos?|years?)?', 'years'),
        (r'(?:mínimo|minimo|pelo menos|no mínimo|at least)\s*(\d+)\s*(?:anos?|years?)', 'years'),
        (r'(\d+)\s*(?:a|to|-)\s*(\d+)\s*(?:anos?|years?)', 'range'),
        (r'mais de\s*(\d+)\s*(?:anos?|years?)', 'years'),
    ]
    
    for pattern, ptype in exp_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            if ptype == 'range':
                entities.years_experience = f"{match.group(1)}-{match.group(2)} anos"
            else:
                entities.years_experience = f"{match.group(1)}+ anos"
            confidence += 0.2
            break
    
    seniority_patterns = {
        r'\b(júnior|junior|jr|trainee|estagiário|estagiaria|intern)\b': 'Junior',
        r'\b(pleno|mid|mid-level|middle|intermediário|intermediario)\b': 'Pleno',
        r'\b(sênior|senior|sr|experiente|experienced)\b': 'Senior',
        r'\b(staff|principal|distinguished)\b': 'Staff',
        r'\b(lead|líder|lider|head)\b': 'Lead',
        r'\b(specialist|especialista|expert)\b': 'Especialista',
    }
    
    for pattern, level in seniority_patterns.items():
        if re.search(pattern, query, re.IGNORECASE):
            entities.seniority = level
            if not entities.years_experience:
                entities.years_experience = level
            confidence += 0.1
            break
    
    # ============================================
    # 4. SKILLS - Tecnologias, Linguagens, Ferramentas
    # ============================================
    skills_list = [
        # Programming Languages
        'python', 'java', 'javascript', 'js', 'typescript', 'ts', 'golang', 'go',
        'rust', 'ruby', 'php', 'c\\+\\+', 'cpp', 'c#', 'csharp', '\\.net', 'dotnet',
        'kotlin', 'swift', 'scala', 'perl', 'r', 'matlab', 'julia', 'elixir',
        'clojure', 'haskell', 'lua', 'dart', 'objective-c', 'cobol', 'fortran',
        
        # Frontend
        'react', 'reactjs', 'react\\.js', 'angular', 'vue', 'vuejs', 'vue\\.js',
        'svelte', 'next\\.?js', 'nextjs', 'nuxt', 'gatsby', 'remix',
        'html', 'css', 'sass', 'scss', 'less', 'tailwind', 'bootstrap', 'material-ui',
        'styled-components', 'webpack', 'vite', 'babel', 'redux', 'mobx', 'zustand',
        
        # Backend
        'node\\.?js', 'nodejs', 'express', 'fastapi', 'django', 'flask', 'fastify',
        'spring', 'spring boot', 'springboot', 'rails', 'ruby on rails', 'laravel',
        'asp\\.net', 'gin', 'echo', 'fiber', 'nestjs', 'nest\\.js', 'graphql', 'rest',
        
        # Mobile
        'react native', 'flutter', 'ionic', 'xamarin', 'swiftui', 'jetpack compose',
        
        # Databases
        'sql', 'nosql', 'mongodb', 'mongo', 'postgresql', 'postgres', 'mysql',
        'mariadb', 'sqlite', 'oracle', 'sql server', 'dynamodb', 'cassandra',
        'redis', 'elasticsearch', 'elastic', 'neo4j', 'couchdb', 'firestore',
        
        # Cloud & DevOps
        'aws', 'amazon web services', 'azure', 'gcp', 'google cloud',
        'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'puppet', 'chef',
        'jenkins', 'github actions', 'gitlab ci', 'circleci', 'travis',
        'nginx', 'apache', 'linux', 'unix', 'bash', 'shell',
        
        # Data & AI
        'machine learning', 'ml', 'deep learning', 'ai', 'inteligência artificial',
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'pandas',
        'numpy', 'spark', 'pyspark', 'hadoop', 'airflow', 'kafka', 'rabbitmq',
        'tableau', 'power bi', 'looker', 'metabase', 'dbt', 'snowflake', 'databricks',
        'nlp', 'computer vision', 'llm', 'gpt', 'openai', 'langchain',
        
        # Tools & Practices
        'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'notion',
        'figma', 'sketch', 'adobe xd', 'invision', 'zeplin',
        'agile', 'scrum', 'kanban', 'lean', 'ci/cd', 'cicd', 'tdd', 'bdd',
        'microservices', 'microsserviços', 'api', 'rest api', 'websocket',
        'serverless', 'lambda', 'event-driven', 'ddd', 'clean architecture',
        
        # Security
        'security', 'segurança', 'owasp', 'penetration testing', 'pentest',
        'soc', 'siem', 'firewall', 'vpn', 'ssl', 'tls', 'oauth', 'jwt',
        
        # Languages (human)
        'inglês', 'ingles', 'english', 'espanhol', 'spanish', 'francês', 'french',
        'alemão', 'german', 'italiano', 'italian', 'mandarim', 'mandarin',
        'inglês fluente', 'inglês avançado', 'bilíngue', 'bilingue'
    ]
    
    skills_found = set()
    for skill in skills_list:
        pattern = r'\b' + skill + r'\b'
        if re.search(pattern, query, re.IGNORECASE):
            skill_clean = skill.replace('\\', '').replace('.?', '.').replace('\\+\\+', '++')
            if skill_clean.lower() in ['js', 'javascript']:
                skill_clean = 'JavaScript'
            elif skill_clean.lower() in ['ts', 'typescript']:
                skill_clean = 'TypeScript'
            elif skill_clean.lower() in ['node.js', 'nodejs']:
                skill_clean = 'Node.js'
            elif skill_clean.lower() in ['k8s', 'kubernetes']:
                skill_clean = 'Kubernetes'
            elif skill_clean.lower() in ['ml', 'machine learning']:
                skill_clean = 'Machine Learning'
            elif skill_clean.lower() in ['ai', 'inteligência artificial']:
                skill_clean = 'AI'
            elif skill_clean.lower() in ['inglês', 'ingles', 'english']:
                skill_clean = 'Inglês'
            elif skill_clean.lower() in ['inglês fluente', 'inglês avançado']:
                skill_clean = 'Inglês Avançado'
            elif len(skill_clean) <= 3:
                skill_clean = skill_clean.upper()
            else:
                skill_clean = skill_clean.title()
            skills_found.add(skill_clean)
    
    if skills_found:
        entities.skills = list(skills_found)[:8]
        confidence += 0.2
    
    # ============================================
    # 5. INDUSTRY - Setores e Indústrias
    # ============================================
    industries = {
        # Tech Verticals
        r'\b(fintech|fin-tech)\b': 'Fintech',
        r'\b(healthtech|health-tech|saúde digital)\b': 'Healthtech',
        r'\b(edtech|ed-tech|educação digital)\b': 'Edtech',
        r'\b(agritech|agri-tech|agrotech)\b': 'Agritech',
        r'\b(legaltech|legal-tech|lawtech)\b': 'Legaltech',
        r'\b(insurtech|insur-tech)\b': 'Insurtech',
        r'\b(proptech|prop-tech|real estate tech)\b': 'Proptech',
        r'\b(logtech|log-tech|logística tech)\b': 'Logtech',
        r'\b(retailtech|retail-tech)\b': 'Retailtech',
        r'\b(martech|mar-tech|marketing tech)\b': 'Martech',
        r'\b(hrtech|hr-tech|rh tech)\b': 'HRtech',
        r'\b(govtech|gov-tech)\b': 'Govtech',
        r'\b(foodtech|food-tech)\b': 'Foodtech',
        r'\b(cleantech|clean-tech|greentech)\b': 'Cleantech',
        
        # Traditional Industries  
        r'\b(?:mercado\s+)?financeiro\b': 'Mercado Financeiro',
        r'\b(finanças|finance|banking|banco|bancos)\b': 'Finanças',
        r'\b(investimento|investment|asset management)\b': 'Investimentos',
        r'\b(seguros?|insurance)\b': 'Seguros',
        r'\b(saúde|health|healthcare|hospitalar?)\b': 'Saúde',
        r'\b(educação|education|ensino)\b': 'Educação',
        r'\b(varejo|retail|e-commerce|ecommerce|comércio)\b': 'Varejo',
        r'\b(logística|logistics|supply chain|cadeia de suprimentos)\b': 'Logística',
        r'\b(telecomunicações?|telecom|telecommunications?)\b': 'Telecom',
        r'\b(energia|energy|utilities|utilities)\b': 'Energia',
        r'\b(automotivo|automotive|automobilístico)\b': 'Automotivo',
        r'\b(farmacêutico|pharma|pharmaceutical)\b': 'Farmacêutico',
        r'\b(imobiliário|real estate|construção|construction)\b': 'Imobiliário',
        r'\b(mídia|media|entretenimento|entertainment)\b': 'Mídia',
        r'\b(agricultura|agro|agronegócio|agribusiness)\b': 'Agronegócio',
        r'\b(manufatura|manufacturing|indústria|industrial)\b': 'Manufatura',
        r'\b(aviação|aviation|aéreo|aerospace)\b': 'Aviação',
        r'\b(jurídico|legal|advocacia|law)\b': 'Jurídico',
        r'\b(rh|recursos humanos|human resources|hr)\b': 'RH',
        
        # Company Types
        r'\b(startup|startups)\b': 'Startup',
        r'\b(scale-?up)\b': 'Scale-up',
        r'\b(consultoria|consulting|consultancy)\b': 'Consultoria',
        r'\b(agência|agency|agencias)\b': 'Agência',
        r'\b(software house|fábrica de software)\b': 'Software House',
        r'\b(big tech|faang|maang)\b': 'Big Tech',
        r'\b(multinacional|multinational|global company)\b': 'Multinacional',
        r'\b(b2b|business to business)\b': 'B2B',
        r'\b(b2c|business to consumer)\b': 'B2C',
        r'\b(saas|software as a service)\b': 'SaaS',
    }
    
    for pattern, industry in industries.items():
        if re.search(pattern, query, re.IGNORECASE):
            entities.industry = industry
            confidence += 0.15
            break
    
    confidence = min(confidence, 1.0)
    
    if not entities.job_title:
        suggestions.append("Especifique o cargo (ex: Product Manager, Desenvolvedor Python)")
    if not entities.location:
        suggestions.append("Adicione a localização (ex: São Paulo, Remoto)")
    if not entities.skills:
        suggestions.append("Liste as skills técnicas (ex: React, Python, AWS)")
    if not entities.years_experience and not entities.seniority:
        suggestions.append("Defina a senioridade (ex: Senior, 5+ anos)")
    if not entities.industry:
        suggestions.append("Mencione o setor (ex: Fintech, Mercado Financeiro)")
    
    return ParseQueryResponse(
        query=request.query,
        entities=entities,
        confidence=confidence,
        suggestions=suggestions
    )


# ========================
# REVEAL CONTACT ENDPOINTS
# ========================

class RevealType(str):
    EMAIL = "email"
    PHONE = "phone"


class RevealContactRequest(BaseModel):
    """Request para revelar email ou telefone de um candidato Pearch."""
    candidate_id: str = Field(..., description="ID do candidato (docid do Pearch)")
    candidate_name: str = Field(..., description="Nome do candidato para busca")
    reveal_type: str = Field(..., description="Tipo: 'email' ou 'phone'", pattern="^(email|phone)$")
    linkedin_slug: Optional[str] = Field(None, description="LinkedIn slug para busca mais precisa")


class RevealContactResponse(BaseModel):
    """Response com dados de contato revelados."""
    success: bool
    candidate_id: str
    reveal_type: str
    
    # Dados revelados
    email: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phone: Optional[str] = None
    phones: List[str] = Field(default_factory=list)
    
    # Custos
    credits_used: int = 0
    credits_remaining: Optional[int] = None
    
    # Mensagem
    message: str = ""


class RevealCostEstimate(BaseModel):
    """Estimativa de custo para reveal."""
    reveal_type: str
    credits_required: int
    description: str


@router.get("/reveal/cost")
async def get_reveal_cost(
    reveal_type: str = Query(..., description="Tipo: 'email' ou 'phone'")
) -> RevealCostEstimate:
    """
    Retorna o custo em créditos para revelar email ou telefone.
    
    Custos:
    - Email: 2 créditos
    - Telefone: 14 créditos
    """
    if reveal_type == "email":
        return RevealCostEstimate(
            reveal_type="email",
            credits_required=2,
            description="Revelar email do candidato"
        )
    elif reveal_type == "phone":
        return RevealCostEstimate(
            reveal_type="phone",
            credits_required=14,
            description="Revelar telefone do candidato"
        )
    else:
        raise HTTPException(status_code=400, detail="reveal_type deve ser 'email' ou 'phone'")


@router.post("/reveal", response_model=RevealContactResponse)
async def reveal_contact(
    request: RevealContactRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Revela email ou telefone de um candidato Pearch.
    
    Custos:
    - Email: 2 créditos por candidato (só cobra se tiver email)
    - Telefone: 14 créditos por candidato (só cobra se tiver telefone)
    
    Fluxo:
    1. Faz busca específica no Pearch com show_emails ou show_phone_numbers
    2. Retorna os dados de contato encontrados
    3. Opcionalmente atualiza o candidato no banco local
    """
    try:
        # Configura busca específica
        search_query = request.candidate_name
        if request.linkedin_slug:
            search_query = f"{request.candidate_name} linkedin:{request.linkedin_slug}"
        
        # Define flags baseado no tipo de reveal
        show_emails = request.reveal_type == "email"
        show_phone_numbers = request.reveal_type == "phone"
        
        # Cria request para Pearch
        pearch_request = PearchSearchRequest(
            query=search_query,
            type=SearchType.FAST,  # Usar fast para reveal individual
            limit=1,
            insights=False,
            profile_scoring=False,
            high_freshness=False,
            require_emails=show_emails,
            show_emails=show_emails,
            require_phone_numbers=show_phone_numbers,
            show_phone_numbers=show_phone_numbers
        )
        
        # Executa busca
        result = await pearch_service.search_candidates(pearch_request, timeout=30)
        
        if not result.search_results:
            return RevealContactResponse(
                success=False,
                candidate_id=request.candidate_id,
                reveal_type=request.reveal_type,
                message=f"Candidato não encontrado ou sem {request.reveal_type} disponível",
                credits_remaining=result.credits_remaining
            )
        
        # Pega primeiro resultado
        profile = result.search_results[0].profile
        
        if request.reveal_type == "email":
            emails = profile.emails or []
            primary_email = profile.best_personal_email or profile.best_business_email or (emails[0] if emails else None)
            
            if not emails and not primary_email:
                return RevealContactResponse(
                    success=False,
                    candidate_id=request.candidate_id,
                    reveal_type=request.reveal_type,
                    message="Este candidato não possui email disponível",
                    credits_used=0,
                    credits_remaining=result.credits_remaining
                )
            
            return RevealContactResponse(
                success=True,
                candidate_id=request.candidate_id,
                reveal_type=request.reveal_type,
                email=primary_email,
                emails=emails,
                credits_used=2,
                credits_remaining=result.credits_remaining,
                message="Email revelado com sucesso"
            )
        
        elif request.reveal_type == "phone":
            phones = profile.phone_numbers or []
            primary_phone = phones[0] if phones else None
            
            if not phones:
                return RevealContactResponse(
                    success=False,
                    candidate_id=request.candidate_id,
                    reveal_type=request.reveal_type,
                    message="Este candidato não possui telefone disponível",
                    credits_used=0,
                    credits_remaining=result.credits_remaining
                )
            
            return RevealContactResponse(
                success=True,
                candidate_id=request.candidate_id,
                reveal_type=request.reveal_type,
                phone=primary_phone,
                phones=phones,
                credits_used=14,
                credits_remaining=result.credits_remaining,
                message="Telefone revelado com sucesso"
            )
        
        return RevealContactResponse(
            success=False,
            candidate_id=request.candidate_id,
            reveal_type=request.reveal_type,
            message="Tipo de reveal inválido"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao revelar contato: {str(e)}")


# ============================================================================
# FILTER SUGGESTIONS ENDPOINT - Autocomplete com contagens
# ============================================================================

class SuggestionCategory(str):
    """Categorias disponíveis para sugestões."""
    TITLES = "titles"
    COMPANIES = "companies"
    SKILLS = "skills"
    UNIVERSITIES = "universities"
    FIELDS_OF_STUDY = "fields_of_study"
    LOCATIONS = "locations"
    COUNTRIES = "countries"
    INDUSTRIES = "industries"
    LANGUAGES = "languages"


class FilterSuggestion(BaseModel):
    """Uma sugestão de filtro com contagem de candidatos."""
    value: str = Field(..., description="Valor canônico para o filtro")
    label: str = Field(..., description="Label para exibição")
    local_count: int = Field(0, description="Contagem de candidatos na base local")
    global_count: Optional[int] = Field(None, description="Contagem estimada na busca global (se disponível)")
    aliases: List[str] = Field(default_factory=list, description="Variações do mesmo termo")
    source: str = Field("local", description="Fonte da sugestão: local ou global")


class FilterSuggestionsRequest(BaseModel):
    """Request para buscar sugestões de filtros."""
    category: str = Field(..., description="Categoria: titles, companies, skills, universities, fields_of_study, locations, countries, industries, languages")
    query: str = Field(..., description="Termo de busca parcial")
    limit: int = Field(10, ge=1, le=50, description="Número máximo de sugestões")
    include_global: bool = Field(False, description="Incluir estimativa global (assíncrono)")


class FilterSuggestionsResponse(BaseModel):
    """Response com sugestões de filtros."""
    category: str
    query: str
    suggestions: List[FilterSuggestion]
    has_more: bool = Field(False, description="Indica se há mais resultados")
    global_pending: bool = Field(False, description="Indica se contagem global está sendo processada")


@router.post("/suggestions", response_model=FilterSuggestionsResponse)
async def get_filter_suggestions(
    request: FilterSuggestionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna sugestões de filtros com contagem de candidatos.
    
    Suporta categorias:
    - titles: Cargos/títulos profissionais
    - companies: Empresas
    - skills: Habilidades técnicas
    - universities: Universidades
    - fields_of_study: Áreas de estudo
    - locations: Cidades/Estados
    - countries: Países
    - industries: Setores/Indústrias
    - languages: Idiomas
    
    Retorna contagem local imediata. Contagem global pode ser solicitada
    via include_global=true (processada de forma assíncrona).
    """
    from sqlalchemy import text, func
    from app.models.candidate import Candidate
    from sqlalchemy.future import select
    from collections import Counter
    
    query_lower = request.query.lower().strip()
    suggestions: List[FilterSuggestion] = []
    
    try:
        # Definir aliases comuns para termos de busca
        COMMON_ALIASES = {
            "titles": {
                "product manager": ["gerente de produto", "pm", "head de produto"],
                "gerente de produto": ["product manager", "pm"],
                "software engineer": ["engenheiro de software", "desenvolvedor", "developer"],
                "desenvolvedor": ["developer", "programador", "software engineer"],
                "tech lead": ["líder técnico", "technical lead"],
                "data scientist": ["cientista de dados"],
                "ux designer": ["designer ux", "product designer"],
                "devops": ["devops engineer", "sre", "site reliability engineer"],
                "backend": ["backend developer", "desenvolvedor backend"],
                "frontend": ["frontend developer", "desenvolvedor frontend"],
                "fullstack": ["full stack", "desenvolvedor fullstack"],
            },
            "skills": {
                "python": ["py"],
                "javascript": ["js", "ecmascript"],
                "typescript": ["ts"],
                "react": ["reactjs", "react.js"],
                "node": ["nodejs", "node.js"],
                "aws": ["amazon web services"],
                "gcp": ["google cloud", "google cloud platform"],
                "azure": ["microsoft azure"],
                "sql": ["mysql", "postgresql", "postgres"],
                "machine learning": ["ml", "aprendizado de máquina"],
            },
            "locations": {
                "sp": ["são paulo", "sao paulo"],
                "são paulo": ["sp", "sao paulo"],
                "rj": ["rio de janeiro"],
                "rio de janeiro": ["rj"],
                "bh": ["belo horizonte"],
                "belo horizonte": ["bh"],
                "poa": ["porto alegre"],
            },
            "languages": {
                "english": ["inglês", "ingles"],
                "inglês": ["english", "ingles"],
                "spanish": ["espanhol"],
                "espanhol": ["spanish"],
                "portuguese": ["português", "portugues"],
                "português": ["portuguese", "portugues"],
            }
        }
        
        # Buscar dados do banco baseado na categoria
        if request.category == "titles":
            # Buscar títulos únicos com contagem
            result = await db.execute(
                text("""
                    SELECT current_title, COUNT(*) as count
                    FROM candidates
                    WHERE current_title IS NOT NULL 
                    AND current_title != ''
                    AND is_active = true
                    AND LOWER(current_title) LIKE :query
                    GROUP BY current_title
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit * 2}
            )
            rows = result.fetchall()
            
            # Agrupar títulos similares
            title_counts = {}
            for row in rows:
                title = row[0]
                count = row[1]
                title_lower = title.lower()
                
                # Verificar se é alias de outro já encontrado
                found_canonical = None
                for canonical in title_counts:
                    if title_lower == canonical.lower():
                        found_canonical = canonical
                        break
                    aliases = COMMON_ALIASES.get("titles", {}).get(canonical.lower(), [])
                    if title_lower in [a.lower() for a in aliases]:
                        found_canonical = canonical
                        break
                
                if found_canonical:
                    title_counts[found_canonical]["count"] += count
                    if title not in title_counts[found_canonical]["aliases"]:
                        title_counts[found_canonical]["aliases"].append(title)
                else:
                    title_counts[title] = {
                        "count": count,
                        "aliases": COMMON_ALIASES.get("titles", {}).get(title_lower, [])
                    }
            
            # Criar sugestões
            for title, data in sorted(title_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:request.limit]:
                suggestions.append(FilterSuggestion(
                    value=title,
                    label=title,
                    local_count=data["count"],
                    aliases=data["aliases"][:3]
                ))
        
        elif request.category == "companies":
            result = await db.execute(
                text("""
                    SELECT current_company, COUNT(*) as count
                    FROM candidates
                    WHERE current_company IS NOT NULL 
                    AND current_company != ''
                    AND is_active = true
                    AND LOWER(current_company) LIKE :query
                    GROUP BY current_company
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                suggestions.append(FilterSuggestion(
                    value=row[0],
                    label=row[0],
                    local_count=row[1]
                ))
        
        elif request.category == "skills":
            # Buscar skills do array technical_skills
            result = await db.execute(
                text("""
                    SELECT skill, COUNT(*) as count
                    FROM (
                        SELECT UNNEST(technical_skills) as skill
                        FROM candidates
                        WHERE is_active = true
                        AND technical_skills IS NOT NULL
                    ) skills_expanded
                    WHERE LOWER(skill) LIKE :query
                    GROUP BY skill
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                skill = row[0]
                skill_lower = skill.lower()
                aliases = COMMON_ALIASES.get("skills", {}).get(skill_lower, [])
                suggestions.append(FilterSuggestion(
                    value=skill,
                    label=skill,
                    local_count=row[1],
                    aliases=aliases[:3]
                ))
        
        elif request.category == "locations":
            # Combinar cidade e estado
            result = await db.execute(
                text("""
                    SELECT 
                        CASE 
                            WHEN location_state IS NOT NULL AND location_state != ''
                            THEN CONCAT(location_city, ', ', location_state)
                            ELSE location_city
                        END as location,
                        COUNT(*) as count
                    FROM candidates
                    WHERE location_city IS NOT NULL 
                    AND location_city != ''
                    AND is_active = true
                    AND (
                        LOWER(location_city) LIKE :query
                        OR LOWER(location_state) LIKE :query
                    )
                    GROUP BY location_city, location_state
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                location = row[0]
                location_lower = (location or "").lower()
                aliases = []
                for key, vals in COMMON_ALIASES.get("locations", {}).items():
                    if key in location_lower or location_lower in key:
                        aliases.extend(vals)
                
                suggestions.append(FilterSuggestion(
                    value=location or "",
                    label=location or "",
                    local_count=row[1],
                    aliases=aliases[:3]
                ))
        
        elif request.category == "countries":
            result = await db.execute(
                text("""
                    SELECT location_country, COUNT(*) as count
                    FROM candidates
                    WHERE location_country IS NOT NULL 
                    AND location_country != ''
                    AND is_active = true
                    AND LOWER(location_country) LIKE :query
                    GROUP BY location_country
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                suggestions.append(FilterSuggestion(
                    value=row[0],
                    label=row[0],
                    local_count=row[1]
                ))
        
        elif request.category == "universities":
            # Universities would be in additional_data or a dedicated field
            # For now, search in resume_text with common university patterns
            result = await db.execute(
                text("""
                    SELECT 
                        COALESCE(additional_data->>'university', 'Não especificado') as university,
                        COUNT(*) as count
                    FROM candidates
                    WHERE is_active = true
                    AND additional_data->>'university' IS NOT NULL
                    AND LOWER(additional_data->>'university') LIKE :query
                    GROUP BY additional_data->>'university'
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                if row[0] and row[0] != 'Não especificado':
                    suggestions.append(FilterSuggestion(
                        value=row[0],
                        label=row[0],
                        local_count=row[1]
                    ))
            
            # Se não encontrou, retornar universidades comuns como sugestão
            if not suggestions and query_lower:
                common_universities = [
                    "USP - Universidade de São Paulo",
                    "UNICAMP - Universidade Estadual de Campinas",
                    "UFRJ - Universidade Federal do Rio de Janeiro",
                    "UFMG - Universidade Federal de Minas Gerais",
                    "PUC-SP",
                    "PUC-RJ",
                    "FGV - Fundação Getúlio Vargas",
                    "UNESP",
                    "UFSC - Universidade Federal de Santa Catarina",
                    "UFRGS - Universidade Federal do Rio Grande do Sul"
                ]
                for uni in common_universities:
                    if query_lower in uni.lower():
                        suggestions.append(FilterSuggestion(
                            value=uni,
                            label=uni,
                            local_count=0,
                            source="suggested"
                        ))
                        if len(suggestions) >= request.limit:
                            break
        
        elif request.category == "languages":
            # Languages is a JSON field
            result = await db.execute(
                text("""
                    SELECT key as language, COUNT(*) as count
                    FROM candidates, jsonb_object_keys(COALESCE(languages, '{}'::jsonb)) as key
                    WHERE is_active = true
                    AND LOWER(key) LIKE :query
                    GROUP BY key
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                lang = row[0]
                lang_lower = lang.lower()
                aliases = COMMON_ALIASES.get("languages", {}).get(lang_lower, [])
                suggestions.append(FilterSuggestion(
                    value=lang,
                    label=lang,
                    local_count=row[1],
                    aliases=aliases[:3]
                ))
            
            # Se não encontrou, retornar idiomas comuns
            if not suggestions and query_lower:
                common_languages = ["Português", "Inglês", "Espanhol", "Francês", "Alemão", "Italiano", "Mandarim"]
                for lang in common_languages:
                    if query_lower in lang.lower():
                        aliases = COMMON_ALIASES.get("languages", {}).get(lang.lower(), [])
                        suggestions.append(FilterSuggestion(
                            value=lang,
                            label=lang,
                            local_count=0,
                            aliases=aliases[:3],
                            source="suggested"
                        ))
                        if len(suggestions) >= request.limit:
                            break
        
        elif request.category == "industries":
            # Industries from additional_data or inferred from company
            common_industries = [
                "Tecnologia",
                "Fintech",
                "E-commerce",
                "Saúde",
                "Educação",
                "Consultoria",
                "Varejo",
                "Agronegócio",
                "Logística",
                "Telecom",
                "Energia",
                "Startups",
                "Banking",
                "Insurance"
            ]
            
            for industry in common_industries:
                if query_lower in industry.lower():
                    suggestions.append(FilterSuggestion(
                        value=industry,
                        label=industry,
                        local_count=0,  # Would need industry mapping
                        source="suggested"
                    ))
                    if len(suggestions) >= request.limit:
                        break
        
        elif request.category == "fields_of_study":
            common_fields = [
                "Ciência da Computação",
                "Engenharia de Software",
                "Sistemas de Informação",
                "Administração",
                "Economia",
                "Engenharia Elétrica",
                "Engenharia Mecânica",
                "Engenharia de Produção",
                "Design",
                "Marketing",
                "Psicologia",
                "Direito",
                "Matemática",
                "Estatística",
                "Física"
            ]
            
            for field in common_fields:
                if query_lower in field.lower():
                    suggestions.append(FilterSuggestion(
                        value=field,
                        label=field,
                        local_count=0,
                        source="suggested"
                    ))
                    if len(suggestions) >= request.limit:
                        break
        
        return FilterSuggestionsResponse(
            category=request.category,
            query=request.query,
            suggestions=suggestions[:request.limit],
            has_more=len(suggestions) > request.limit,
            global_pending=request.include_global
        )
    
    except Exception as e:
        import traceback
        print(f"Error in get_filter_suggestions: {str(e)}")
        print(traceback.format_exc())
        # Return empty suggestions on error
        return FilterSuggestionsResponse(
            category=request.category,
            query=request.query,
            suggestions=[],
            has_more=False,
            global_pending=False
        )


# ============================================================================
# ARCHETYPE ENDPOINTS - Pre-configured search profiles
# ============================================================================

class ArchetypeDTO(BaseModel):
    """DTO for archetype data in API responses."""
    id: str
    name: str
    description: Optional[str] = None
    emoji: str = "🎯"
    query: str
    filters: dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    seniority: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    created_at: Optional[str] = None


class ArchetypeListResponse(BaseModel):
    """Response for listing archetypes."""
    archetypes: List[ArchetypeDTO]
    total: int
    default_count: int


class ArchetypeCreateRequest(BaseModel):
    """Request to create a new archetype."""
    id: Optional[str] = Field(None, description="ID único, gerado automaticamente se não fornecido")
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    emoji: str = Field("🎯", max_length=10)
    query: str = Field(..., min_length=5)
    filters: dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    seniority: Optional[str] = None


class ArchetypeUpdateRequest(BaseModel):
    """Request to update an existing archetype."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    emoji: Optional[str] = Field(None, max_length=10)
    query: Optional[str] = Field(None, min_length=5)
    filters: Optional[dict] = None
    tags: Optional[List[str]] = None
    industry: Optional[str] = None
    seniority: Optional[str] = None
    is_active: Optional[bool] = None


class ArchetypeSearchRequest(BaseModel):
    """Request to search using an archetype."""
    search_local: bool = Field(True, description="Buscar no banco local")
    search_pearch: bool = Field(True, description="Buscar na Pearch AI")
    pearch_type: str = Field("fast", pattern="^(fast|pro)$")
    local_limit: int = Field(20, ge=1, le=100)
    pearch_limit: int = Field(15, ge=1, le=50)
    show_emails: bool = False
    show_phone_numbers: bool = False
    calculate_lia_score: bool = Field(True, description="Calcular score LIA para cada candidato")


class ArchetypeSearchResultDTO(CandidateSearchResultDTO):
    """Extended search result with LIA score."""
    lia_score: Optional[float] = None
    lia_reasoning: Optional[str] = None
    lia_breakdown: Optional[dict] = None
    lia_strengths: List[str] = Field(default_factory=list)
    lia_concerns: List[str] = Field(default_factory=list)


class ArchetypeSearchResponse(BaseModel):
    """Response for archetype-based search."""
    archetype: ArchetypeDTO
    query: str
    thread_id: Optional[str] = None
    candidates: List[ArchetypeSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: Optional[int] = None
    search_time_seconds: Optional[float] = None
    warning_message: Optional[str] = None


@router.get("/archetypes", response_model=ArchetypeListResponse)
async def list_archetypes(
    include_inactive: bool = Query(False, description="Incluir arquétipos inativos"),
    industry: Optional[str] = Query(None, description="Filtrar por indústria"),
    seniority: Optional[str] = Query(None, description="Filtrar por senioridade"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos os arquétipos disponíveis.
    
    Arquétipos são templates de busca pré-configurados que facilitam
    encontrar perfis específicos sem precisar construir queries complexas.
    """
    from sqlalchemy import select
    from app.models.archetype import SearchArchetype, seed_default_archetypes
    
    try:
        # Seed default archetypes if needed
        created = await seed_default_archetypes(db)
        if created > 0:
            logger.info(f"Seeded {created} default archetypes")
        
        # Build query
        query = select(SearchArchetype)
        
        if not include_inactive:
            query = query.where(SearchArchetype.is_active == True)
        
        if industry:
            query = query.where(SearchArchetype.industry == industry)
        
        if seniority:
            query = query.where(SearchArchetype.seniority == seniority)
        
        query = query.order_by(SearchArchetype.is_default.desc(), SearchArchetype.usage_count.desc())
        
        result = await db.execute(query)
        archetypes = result.scalars().all()
        
        archetype_dtos = []
        default_count = 0
        
        for arch in archetypes:
            if arch.is_default:
                default_count += 1
            
            archetype_dtos.append(ArchetypeDTO(
                id=arch.id,
                name=arch.name,
                description=arch.description,
                emoji=arch.emoji or "🎯",
                query=arch.query,
                filters=arch.filters or {},
                tags=arch.tags or [],
                industry=arch.industry,
                seniority=arch.seniority,
                is_default=arch.is_default,
                is_active=arch.is_active,
                usage_count=arch.usage_count or 0,
                created_at=arch.created_at.isoformat() if arch.created_at else None
            ))
        
        return ArchetypeListResponse(
            archetypes=archetype_dtos,
            total=len(archetype_dtos),
            default_count=default_count
        )
    
    except Exception as e:
        logger.error(f"Error listing archetypes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list archetypes: {str(e)}")


@router.post("/archetypes", response_model=ArchetypeDTO)
async def create_archetype(
    request: ArchetypeCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo arquétipo personalizado.
    
    Arquétipos criados pelo usuário não são marcados como 'default'
    e podem ser modificados ou excluídos posteriormente.
    """
    from sqlalchemy import select
    from app.models.archetype import SearchArchetype
    import uuid as uuid_lib
    
    try:
        # Generate ID if not provided
        archetype_id = request.id or f"custom-{uuid_lib.uuid4().hex[:8]}"
        
        # Check if ID already exists
        existing = await db.execute(
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Archetype with ID '{archetype_id}' already exists")
        
        # Create archetype
        archetype = SearchArchetype(
            id=archetype_id,
            name=request.name,
            description=request.description,
            emoji=request.emoji,
            query=request.query,
            filters=request.filters,
            tags=request.tags,
            industry=request.industry,
            seniority=request.seniority,
            is_default=False,
            is_active=True,
            usage_count=0
        )
        
        db.add(archetype)
        await db.commit()
        await db.refresh(archetype)
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating archetype: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create archetype: {str(e)}")


@router.post("/archetypes/from-search", response_model=ArchetypeFromSearchResponse)
async def create_archetype_from_search(
    data: ArchetypeFromSearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Cria um novo arquétipo a partir de um SearchSpec.
    
    Extrai automaticamente tags, filtros e query do search_spec fornecido,
    criando um template reutilizável de busca.
    
    Args:
        data: SearchSpec + nome + descrição + emoji opcional
        
    Returns:
        O arquétipo criado com as tags extraídas
    """
    from app.models.archetype import SearchArchetype
    
    try:
        company_id = current_user.company_id
        user_id = str(current_user.id) if current_user.id else None
        if not company_id:
            raise HTTPException(status_code=400, detail="company_id is required to create an archetype")
        
        extracted_tags = extract_tags_from_search_spec(data.search_spec)
        
        archetype = build_archetype_from_search(
            search_spec=data.search_spec,
            name=data.name,
            description=data.description,
            emoji=data.emoji,
            company_id=company_id,
            user_id=user_id
        )
        
        db.add(archetype)
        await db.commit()
        await db.refresh(archetype)
        
        logger.info(f"Created archetype '{archetype.name}' (id={archetype.id}) from search spec")
        
        return ArchetypeFromSearchResponse(
            archetype=ArchetypeResponse(
                id=archetype.id,
                name=archetype.name,
                description=archetype.description,
                emoji=archetype.emoji or "🎯",
                query=archetype.query,
                filters=archetype.filters or {},
                tags=archetype.tags or [],
                industry=archetype.industry,
                seniority=archetype.seniority,
                is_default=archetype.is_default,
                is_active=archetype.is_active,
                usage_count=archetype.usage_count or 0,
                company_id=archetype.company_id,
                created_by=archetype.created_by,
                created_at=archetype.created_at,
                updated_at=archetype.updated_at
            ),
            extracted_tags=extracted_tags,
            message=f"Arquétipo '{archetype.name}' criado com sucesso com {len(extracted_tags)} tags extraídas"
        )
        
    except Exception as e:
        logger.error(f"Error creating archetype from search: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create archetype from search: {str(e)}")


# ============================================================================
# ARCHETYPE AUTO-GENERATION ENDPOINTS
# ============================================================================

class ClosedJobSuggestion(BaseModel):
    """Sugestão de vaga fechada para criar arquétipo."""
    job_id: str
    title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    closed_at: Optional[str] = None
    hired_count: int = 0
    suggested_archetype_name: str
    suggested_emoji: str = "🎯"


class ClosedJobSuggestionsResponse(BaseModel):
    """Response com sugestões de vagas fechadas."""
    suggestions: List[ClosedJobSuggestion] = Field(default_factory=list)
    total: int = 0


class ArchetypeFromDescriptionRequest(BaseModel):
    """Request para criar arquétipo a partir de descrição."""
    description: str = Field(..., min_length=20, description="Descrição do perfil ideal")
    name: Optional[str] = Field(None, description="Nome do arquétipo (opcional, será gerado se não fornecido)")


@router.get("/archetypes/suggestions/closed-jobs", response_model=ClosedJobSuggestionsResponse)
async def get_closed_job_suggestions(
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista sugestões de vagas fechadas para criar arquétipos.
    
    Retorna as últimas vagas concluídas com contratação bem-sucedida,
    sugerindo nomes e emojis para os arquétipos.
    """
    from sqlalchemy import select, desc, or_
    from app.models.job_vacancy import JobVacancy
    
    try:
        result = await db.execute(
            select(JobVacancy)
            .where(
                or_(
                    JobVacancy.status == "Concluída",
                    JobVacancy.status == "Fechada",
                    JobVacancy.closed_at.isnot(None)
                )
            )
            .order_by(desc(JobVacancy.closed_at), desc(JobVacancy.updated_at))
            .limit(limit)
        )
        jobs = result.scalars().all()
        
        suggestions = []
        emoji_map = {
            "tecnologia": "💻", "ti": "💻", "tech": "💻", "desenvolvimento": "🚀",
            "financeiro": "💰", "finanças": "📊", "contabilidade": "📑",
            "rh": "👥", "recursos humanos": "🤝", "people": "👥",
            "comercial": "🎯", "vendas": "💼", "sales": "📈",
            "marketing": "📣", "comunicação": "📢",
            "operações": "⚙️", "logística": "🚚", "supply": "📦",
            "jurídico": "⚖️", "legal": "📜",
            "produto": "🎨", "design": "✨", "ux": "🎨"
        }
        
        for job in jobs:
            dept_lower = (job.department or "").lower()
            emoji = "🎯"
            for key, value in emoji_map.items():
                if key in dept_lower or key in (job.title or "").lower():
                    emoji = value
                    break
            
            seniority_prefix = ""
            if job.seniority_level:
                seniority_prefix = f"{job.seniority_level} "
            
            suggestions.append(ClosedJobSuggestion(
                job_id=str(job.id),
                title=job.title,
                department=job.department,
                seniority=job.seniority_level,
                closed_at=job.closed_at.isoformat() if job.closed_at else None,
                hired_count=1,
                suggested_archetype_name=f"{seniority_prefix}{job.title}",
                suggested_emoji=emoji
            ))
        
        return ClosedJobSuggestionsResponse(
            suggestions=suggestions,
            total=len(suggestions)
        )
    
    except Exception as e:
        logger.error(f"Error getting closed job suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archetypes/from-job/{job_id}", response_model=ArchetypeDTO)
async def create_archetype_from_job(
    job_id: str,
    custom_name: Optional[str] = Query(None, description="Nome customizado para o arquétipo"),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um arquétipo automaticamente a partir de uma vaga fechada.
    
    Extrai título, senioridade, requisitos técnicos, competências
    comportamentais e outras informações da vaga para criar um
    arquétipo reutilizável.
    """
    from sqlalchemy import select
    from app.models.job_vacancy import JobVacancy
    from app.models.archetype import SearchArchetype
    import uuid as uuid_lib
    
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job vacancy '{job_id}' not found")
        
        skills = []
        if job.technical_requirements:
            for req in job.technical_requirements:
                if isinstance(req, dict) and req.get("technology"):
                    skills.append(req["technology"])
        if job.requirements:
            skills.extend(job.requirements[:5])
        
        behavioral = []
        if job.behavioral_competencies:
            for comp in job.behavioral_competencies:
                if isinstance(comp, dict) and comp.get("competency"):
                    behavioral.append(comp["competency"])
        
        query_parts = []
        if job.seniority_level:
            query_parts.append(job.seniority_level)
        query_parts.append(job.title)
        if skills[:3]:
            query_parts.append(f"com experiência em {', '.join(skills[:3])}")
        if job.location:
            query_parts.append(f"em {job.location}")
        
        query = " ".join(query_parts)
        
        emoji_map = {
            "tecnologia": "💻", "ti": "💻", "tech": "💻", "dev": "🚀",
            "financeiro": "💰", "finanças": "📊", "fp&a": "📈",
            "rh": "👥", "recursos humanos": "🤝", "recruiter": "🎯",
            "comercial": "🎯", "vendas": "💼", "sales": "📈",
            "marketing": "📣", "produto": "🎨", "design": "✨",
            "operações": "⚙️", "logística": "🚚", "compras": "🛒"
        }
        
        emoji = "🎯"
        search_text = f"{job.department or ''} {job.title}".lower()
        for key, value in emoji_map.items():
            if key in search_text:
                emoji = value
                break
        
        seniority_map = {
            "júnior": "junior", "junior": "junior", "jr": "junior",
            "pleno": "pleno", "mid": "pleno",
            "sênior": "senior", "senior": "senior", "sr": "senior",
            "especialista": "senior", "lead": "senior", "líder": "senior"
        }
        seniority = None
        if job.seniority_level:
            seniority = seniority_map.get(job.seniority_level.lower(), "pleno")
        
        industry = None
        dept_lower = (job.department or "").lower()
        title_lower = (job.title or "").lower()
        if any(k in dept_lower or k in title_lower for k in ["tech", "ti", "dev", "software", "dados"]):
            industry = "tecnologia"
        elif any(k in dept_lower or k in title_lower for k in ["financ", "contab", "fiscal", "tribut"]):
            industry = "financas"
        elif any(k in dept_lower or k in title_lower for k in ["rh", "recursos", "people", "gente"]):
            industry = "rh"
        elif any(k in dept_lower or k in title_lower for k in ["compras", "supply", "logist", "procurement"]):
            industry = "compras"
        elif any(k in dept_lower or k in title_lower for k in ["comercial", "vendas", "sales"]):
            industry = "comercial"
        
        archetype_name = custom_name or f"{job.seniority_level or ''} {job.title}".strip()
        archetype_id = f"job-{uuid_lib.uuid4().hex[:8]}"
        
        archetype = SearchArchetype(
            id=archetype_id,
            name=archetype_name,
            description=f"Arquétipo baseado na vaga: {job.title}. {job.description[:200] if job.description else ''}",
            emoji=emoji,
            query=query,
            filters={
                "seniority": seniority,
                "skills": skills[:10],
                "behavioral_competencies": behavioral[:5],
                "location": job.location,
                "work_model": job.work_model
            },
            tags=skills[:5] + behavioral[:3],
            industry=industry,
            seniority=seniority,
            is_default=False,
            is_active=True,
            usage_count=0
        )
        
        db.add(archetype)
        await db.commit()
        await db.refresh(archetype)
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating archetype from job: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archetypes/from-description", response_model=ArchetypeDTO)
async def create_archetype_from_description(
    request: ArchetypeFromDescriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um arquétipo a partir de uma descrição textual.
    
    A LIA analisa a descrição e extrai automaticamente:
    - Título do cargo
    - Senioridade
    - Skills técnicas
    - Competências comportamentais
    - Indústria/área
    """
    from app.models.archetype import SearchArchetype
    import uuid as uuid_lib
    import re
    
    try:
        description = request.description.lower()
        
        title = "Profissional"
        title_patterns = [
            (r'\b(desenvolvedor|developer|dev)\b', "Desenvolvedor"),
            (r'\b(engenheiro|engineer)\b', "Engenheiro"),
            (r'\b(analista|analyst)\b', "Analista"),
            (r'\b(gerente|manager|gestor)\b', "Gerente"),
            (r'\b(coordenador|coordinator)\b', "Coordenador"),
            (r'\b(diretor|director)\b', "Diretor"),
            (r'\b(especialista|specialist)\b', "Especialista"),
            (r'\b(consultor|consultant)\b', "Consultor"),
            (r'\b(designer)\b', "Designer"),
            (r'\b(arquiteto|architect)\b', "Arquiteto"),
            (r'\b(cientista|scientist)\b', "Cientista"),
            (r'\b(recrutador|recruiter)\b', "Recrutador"),
            (r'\b(comprador|buyer)\b', "Comprador"),
            (r'\b(contador|accountant)\b', "Contador")
        ]
        for pattern, found_title in title_patterns:
            if re.search(pattern, description):
                title = found_title
                break
        
        seniority = "pleno"
        if re.search(r'\b(sênior|senior|sr|experiente|8\+|10\+)\b', description):
            seniority = "senior"
        elif re.search(r'\b(júnior|junior|jr|iniciante|1\s*ano)\b', description):
            seniority = "junior"
        elif re.search(r'\b(pleno|mid|intermediário|3\+|4\+|5\+)\b', description):
            seniority = "pleno"
        
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'node', 'angular', 'vue',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'sql', 'postgresql', 'mongodb',
            'excel', 'power bi', 'tableau', 'sap', 'oracle', 'salesforce',
            'scrum', 'agile', 'kanban', 'pmp', 'itil',
            'machine learning', 'data science', 'inteligência artificial', 'nlp',
            'liderança', 'gestão', 'negociação', 'comunicação', 'análise'
        ]
        skills = [s.title() for s in skill_keywords if s in description][:8]
        
        industry = None
        if any(k in description for k in ['tech', 'ti', 'software', 'dados', 'dev', 'código']):
            industry = "tecnologia"
        elif any(k in description for k in ['financ', 'contab', 'fiscal', 'tribut', 'fp&a']):
            industry = "financas"
        elif any(k in description for k in ['rh', 'recursos humanos', 'people', 'gente', 'recrutamento']):
            industry = "rh"
        elif any(k in description for k in ['compras', 'supply', 'logíst', 'procurement']):
            industry = "compras"
        
        emoji_map = {
            "tecnologia": "💻", "financas": "💰", "rh": "👥", "compras": "📦"
        }
        emoji = emoji_map.get(industry, "🎯")
        
        seniority_pt = {"junior": "Júnior", "pleno": "Pleno", "senior": "Sênior"}.get(seniority, "")
        archetype_name = request.name or f"{seniority_pt} {title}".strip()
        
        query = request.description[:200]
        if skills:
            query = f"{seniority_pt} {title} com experiência em {', '.join(skills[:3])}"
        
        archetype_id = f"desc-{uuid_lib.uuid4().hex[:8]}"
        
        archetype = SearchArchetype(
            id=archetype_id,
            name=archetype_name,
            description=request.description[:500],
            emoji=emoji,
            query=query,
            filters={
                "seniority": seniority,
                "skills": skills
            },
            tags=skills[:5],
            industry=industry,
            seniority=seniority,
            is_default=False,
            is_active=True,
            usage_count=0
        )
        
        db.add(archetype)
        await db.commit()
        await db.refresh(archetype)
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating archetype from description: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/archetypes/{archetype_id}", response_model=ArchetypeDTO)
async def get_archetype(
    archetype_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Obtém detalhes de um arquétipo específico."""
    from sqlalchemy import select
    from app.models.archetype import SearchArchetype
    
    try:
        result = await db.execute(
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            raise HTTPException(status_code=404, detail=f"Archetype '{archetype_id}' not found")
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting archetype: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get archetype: {str(e)}")


@router.delete("/archetypes/{archetype_id}")
async def delete_archetype(
    archetype_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta um arquétipo personalizado.
    
    Arquétipos padrão do sistema não podem ser deletados.
    """
    from sqlalchemy import select, delete
    from app.models.archetype import SearchArchetype
    
    try:
        result = await db.execute(
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            raise HTTPException(status_code=404, detail=f"Archetype '{archetype_id}' not found")
        
        if archetype.is_default:
            raise HTTPException(
                status_code=403, 
                detail="Cannot delete default system archetypes. You can deactivate them instead."
            )
        
        await db.execute(
            delete(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        await db.commit()
        
        return {"message": f"Archetype '{archetype_id}' deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting archetype: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete archetype: {str(e)}")


@router.put("/archetypes/{archetype_id}", response_model=ArchetypeDTO)
async def update_archetype(
    archetype_id: str,
    request: ArchetypeUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza um arquétipo existente.
    
    Arquétipos padrão do sistema podem ter apenas alguns campos atualizados.
    """
    from sqlalchemy import select
    from app.models.archetype import SearchArchetype
    
    try:
        result = await db.execute(
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            raise HTTPException(status_code=404, detail=f"Archetype '{archetype_id}' not found")
        
        # Default archetypes can now be fully edited by users
        
        if request.name is not None:
            archetype.name = request.name
        if request.description is not None:
            archetype.description = request.description
        if request.emoji is not None:
            archetype.emoji = request.emoji
        if request.query is not None:
            archetype.query = request.query
        if request.filters is not None:
            archetype.filters = request.filters
        if request.tags is not None:
            archetype.tags = request.tags
        if request.industry is not None:
            archetype.industry = request.industry
        if request.seniority is not None:
            archetype.seniority = request.seniority
        if request.is_active is not None:
            archetype.is_active = request.is_active
        
        await db.commit()
        await db.refresh(archetype)
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating archetype: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update archetype: {str(e)}")


@router.post("/archetypes/{archetype_id}/search", response_model=ArchetypeSearchResponse)
async def search_by_archetype(
    archetype_id: str,
    request: ArchetypeSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Executa busca de candidatos usando um arquétipo específico.
    
    O arquétipo define a query e filtros pré-configurados.
    Opcionalmente calcula o score LIA para cada candidato encontrado.
    """
    from sqlalchemy import select, update
    from app.models.archetype import SearchArchetype
    from app.services.lia_score_service import lia_score_service
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get archetype
        result = await db.execute(
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            raise HTTPException(status_code=404, detail=f"Archetype '{archetype_id}' not found")
        
        if not archetype.is_active:
            raise HTTPException(status_code=400, detail=f"Archetype '{archetype_id}' is inactive")
        
        # Increment usage count
        await db.execute(
            update(SearchArchetype)
            .where(SearchArchetype.id == archetype_id)
            .values(usage_count=(archetype.usage_count or 0) + 1)
        )
        await db.commit()
        
        # Build hybrid search request
        hybrid_request = HybridSearchRequest(
            query=archetype.query,
            search_local_first=request.search_local,
            include_pearch=request.search_pearch,
            pearch_type=SearchType(request.pearch_type) if request.pearch_type in ["fast", "pro"] else SearchType.FAST,
            local_limit=request.local_limit,
            pearch_limit=request.pearch_limit,
            show_emails=request.show_emails,
            show_phone_numbers=request.show_phone_numbers
        )
        
        # Execute search
        search_result = await pearch_service.hybrid_search(db, hybrid_request)
        
        # Prepare criteria for LIA score calculation
        criteria = {
            "query": archetype.query,
            "filters": archetype.filters or {}
        }
        
        # Convert results and calculate LIA scores
        candidates = []
        
        for profile in search_result.local_candidates:
            candidate_dto = ArchetypeSearchResultDTO(
                id=profile.docid or "",
                name=profile.get_full_name(),
                first_name=profile.first_name,
                last_name=profile.last_name,
                picture_url=profile.picture_url,
                headline=profile.headline,
                current_title=profile.current_title,
                current_company=profile.current_company,
                location=profile.location,
                total_experience_years=profile.total_experience_years,
                skills=profile.skills[:10] if profile.skills else [],
                score=profile.get_score_percentage(),
                match_summary=profile.insights.overall_summary if profile.insights else profile.match_reasoning,
                linkedin_url=profile.get_linkedin_url(),
                has_email=profile.has_emails or False,
                has_phone=profile.has_phone_numbers or False,
                source="local",
                is_open_to_work=profile.is_opentowork
            )
            
            # Calculate LIA score if requested
            if request.calculate_lia_score:
                try:
                    candidate_data = {
                        "skills": profile.skills,
                        "total_experience_years": profile.total_experience_years,
                        "seniority_level": getattr(profile, 'seniority', None),
                        "location": profile.location,
                        "current_title": profile.current_title,
                        "is_opentowork": profile.is_opentowork,
                    }
                    lia_result = lia_score_service.calculate_score(candidate_data, criteria)
                    candidate_dto.lia_score = lia_result.score
                    candidate_dto.lia_reasoning = lia_result.reasoning
                    candidate_dto.lia_breakdown = lia_result.breakdown.to_dict()
                    candidate_dto.lia_strengths = lia_result.strengths
                    candidate_dto.lia_concerns = lia_result.concerns
                except Exception as e:
                    logger.warning(f"Failed to calculate LIA score: {e}")
            
            candidates.append(candidate_dto)
        
        for profile in search_result.pearch_candidates:
            candidate_dto = ArchetypeSearchResultDTO(
                id=profile.docid or "",
                name=profile.get_full_name(),
                first_name=profile.first_name,
                last_name=profile.last_name,
                picture_url=profile.picture_url,
                headline=profile.headline,
                current_title=profile.current_title,
                current_company=profile.current_company,
                location=profile.location,
                total_experience_years=profile.total_experience_years,
                skills=profile.skills[:10] if profile.skills else [],
                score=profile.get_score_percentage(),
                match_summary=profile.insights.overall_summary if profile.insights else profile.match_reasoning,
                linkedin_url=profile.get_linkedin_url(),
                has_email=profile.has_emails or False,
                has_phone=profile.has_phone_numbers or False,
                source="pearch",
                is_open_to_work=profile.is_opentowork
            )
            
            # Calculate LIA score if requested
            if request.calculate_lia_score:
                try:
                    candidate_data = {
                        "skills": profile.skills,
                        "total_experience_years": profile.total_experience_years,
                        "seniority_level": getattr(profile, 'seniority', None),
                        "location": profile.location,
                        "current_title": profile.current_title,
                        "is_opentowork": profile.is_opentowork,
                    }
                    lia_result = lia_score_service.calculate_score(candidate_data, criteria)
                    candidate_dto.lia_score = lia_result.score
                    candidate_dto.lia_reasoning = lia_result.reasoning
                    candidate_dto.lia_breakdown = lia_result.breakdown.to_dict()
                    candidate_dto.lia_strengths = lia_result.strengths
                    candidate_dto.lia_concerns = lia_result.concerns
                except Exception as e:
                    logger.warning(f"Failed to calculate LIA score: {e}")
            
            candidates.append(candidate_dto)
        
        # Sort by LIA score if calculated
        if request.calculate_lia_score:
            candidates.sort(key=lambda x: x.lia_score or 0, reverse=True)
        
        archetype_dto = ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=(archetype.usage_count or 0) + 1,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
        
        return ArchetypeSearchResponse(
            archetype=archetype_dto,
            query=archetype.query,
            thread_id=search_result.thread_id,
            candidates=candidates,
            local_count=search_result.local_count,
            pearch_count=search_result.pearch_count,
            total_count=search_result.total_count,
            credits_remaining=search_result.pearch_credits_remaining,
            search_time_seconds=(search_result.local_search_time or 0) + (search_result.pearch_search_time or 0),
            warning_message=search_result.warning_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching by archetype: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Archetype search failed: {str(e)}")


# ============================================================================
# ARCHETYPE GENERATION FROM JOB VACANCY - Create archetype from closed job
# ============================================================================

class ArchetypeGenerationRequest(BaseModel):
    """Request to generate an archetype from a closed job vacancy."""
    job_id: int = Field(..., description="ID da vaga fechada")
    name: Optional[str] = Field(None, description="Nome personalizado para o arquétipo (opcional, será gerado se não fornecido)")
    emoji: str = Field("🎯", max_length=10, description="Emoji para o arquétipo")


class ArchetypeGenerationResponse(BaseModel):
    """Response with generated archetype."""
    success: bool
    archetype: Optional[ArchetypeDTO] = None
    job_title: str
    hired_candidate_name: Optional[str] = None
    message: str


@router.post("/archetypes/from-job", response_model=ArchetypeGenerationResponse)
async def generate_archetype_from_job(
    request: ArchetypeGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Gera um arquétipo de busca a partir de uma vaga fechada com candidato contratado.
    
    Usa IA (Claude) para analisar:
    - Descrição da vaga (JD)
    - Perfil do candidato contratado
    - Requisitos técnicos e comportamentais
    
    E gerar:
    - Query otimizada para buscar candidatos similares
    - Filtros pré-configurados
    - Tags relevantes
    """
    from sqlalchemy import select
    from app.models.job_vacancy import JobVacancy
    from app.models.archetype import SearchArchetype
    import uuid as uuid_lib
    import anthropic
    import json
    import os
    
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == request.job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {request.job_id}")
        
        if job.status not in ["Concluída", "Fechada", "Preenchida"]:
            raise HTTPException(
                status_code=400, 
                detail=f"A vaga deve estar concluída para gerar arquétipo. Status atual: {job.status}"
            )
        
        hired_data = job.additional_data.get("hired_candidate") if job.additional_data else None
        hired_name = hired_data.get("name") if hired_data else None
        
        jd_info = {
            "title": job.title,
            "department": job.department,
            "location": job.location,
            "work_model": job.work_model,
            "seniority_level": job.seniority_level,
            "description": job.description,
            "requirements": job.requirements or [],
            "technical_requirements": job.technical_requirements or [],
            "behavioral_competencies": job.behavioral_competencies or [],
            "languages": job.languages or [],
        }
        
        candidate_info = None
        if hired_data:
            candidate_info = {
                "name": hired_data.get("name"),
                "current_title": hired_data.get("current_title"),
                "years_experience": hired_data.get("years_experience"),
                "skills": hired_data.get("skills", []),
                "location": hired_data.get("location"),
                "seniority": hired_data.get("seniority"),
            }
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""Você é um especialista em recrutamento. Analise a vaga e o perfil do candidato contratado para criar um arquétipo de busca.

DADOS DA VAGA:
{json.dumps(jd_info, ensure_ascii=False, indent=2)}

{"PERFIL DO CANDIDATO CONTRATADO:" if candidate_info else ""}
{json.dumps(candidate_info, ensure_ascii=False, indent=2) if candidate_info else "Não disponível"}

Gere um arquétipo de busca no formato JSON com:
1. name: Nome curto e descritivo do arquétipo (ex: "Product Manager B2B SaaS")
2. description: Descrição de 1-2 linhas do perfil ideal
3. query: Query em linguagem natural para buscar candidatos similares (incluir cargo, experiência, skills principais)
4. filters: Objeto com filtros:
   - seniority: "junior" | "pleno" | "senior" | "lead"
   - experience_years_min: número
   - skills: array de skills principais (máximo 5)
5. tags: Array de tags relevantes (máximo 5)
6. industry: Indústria/setor (ex: "tecnologia", "financas", "rh", "compras")
7. seniority: Senioridade principal do perfil

Responda APENAS com o JSON, sem explicações adicionais."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        archetype_data = json.loads(response_text)
        
        archetype_id = f"custom-{uuid_lib.uuid4().hex[:8]}"
        name = request.name or archetype_data.get("name", f"Similar a {job.title}")
        
        new_archetype = SearchArchetype(
            id=archetype_id,
            name=name,
            description=archetype_data.get("description"),
            emoji=request.emoji,
            query=archetype_data.get("query", ""),
            filters=archetype_data.get("filters", {}),
            tags=archetype_data.get("tags", []),
            industry=archetype_data.get("industry"),
            seniority=archetype_data.get("seniority"),
            is_default=False,
            is_active=True,
            usage_count=0,
            company_id=job.company_id,
            created_by="lia-system"
        )
        
        db.add(new_archetype)
        await db.commit()
        await db.refresh(new_archetype)
        
        logger.info(f"✅ Created archetype '{name}' from job '{job.title}'")
        
        return ArchetypeGenerationResponse(
            success=True,
            archetype=ArchetypeDTO(
                id=new_archetype.id,
                name=new_archetype.name,
                description=new_archetype.description,
                emoji=new_archetype.emoji or "🎯",
                query=new_archetype.query,
                filters=new_archetype.filters or {},
                tags=new_archetype.tags or [],
                industry=new_archetype.industry,
                seniority=new_archetype.seniority,
                is_default=False,
                is_active=True,
                usage_count=0,
                created_at=new_archetype.created_at.isoformat() if new_archetype.created_at else None
            ),
            job_title=job.title,
            hired_candidate_name=hired_name,
            message=f"Arquétipo '{name}' criado com sucesso a partir da vaga '{job.title}'"
        )
    
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise HTTPException(status_code=500, detail="Falha ao processar resposta da IA")
    except Exception as e:
        logger.error(f"Error generating archetype from job: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Falha ao gerar arquétipo: {str(e)}")


class ArchetypeFromDescriptionRequest(BaseModel):
    """Request to generate an archetype from a text description."""
    description: str = Field(..., min_length=20, description="Descrição textual do perfil ideal")
    name: Optional[str] = Field(None, description="Nome personalizado para o arquétipo")
    emoji: str = Field("🎯", max_length=10)


@router.post("/archetypes/from-description", response_model=ArchetypeGenerationResponse)
async def generate_archetype_from_description(
    request: ArchetypeFromDescriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Gera um arquétipo de busca a partir de uma descrição textual livre.
    
    Útil quando o usuário descreve o perfil ideal em linguagem natural.
    """
    from sqlalchemy import select
    from app.models.archetype import SearchArchetype
    import uuid as uuid_lib
    import anthropic
    import json
    import os
    
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""Você é um especialista em recrutamento. Analise a descrição do perfil ideal e crie um arquétipo de busca.

DESCRIÇÃO DO PERFIL IDEAL:
{request.description}

Gere um arquétipo de busca no formato JSON com:
1. name: Nome curto e descritivo do arquétipo (ex: "Product Manager B2B SaaS")
2. description: Descrição de 1-2 linhas do perfil ideal
3. query: Query em linguagem natural para buscar candidatos similares (incluir cargo, experiência, skills principais)
4. filters: Objeto com filtros:
   - seniority: "junior" | "pleno" | "senior" | "lead"
   - experience_years_min: número
   - skills: array de skills principais (máximo 5)
5. tags: Array de tags relevantes (máximo 5)
6. industry: Indústria/setor (ex: "tecnologia", "financas", "rh", "compras")
7. seniority: Senioridade principal do perfil

Responda APENAS com o JSON, sem explicações adicionais."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        archetype_data = json.loads(response_text)
        
        archetype_id = f"custom-{uuid_lib.uuid4().hex[:8]}"
        name = request.name or archetype_data.get("name", "Perfil Personalizado")
        
        new_archetype = SearchArchetype(
            id=archetype_id,
            name=name,
            description=archetype_data.get("description"),
            emoji=request.emoji,
            query=archetype_data.get("query", ""),
            filters=archetype_data.get("filters", {}),
            tags=archetype_data.get("tags", []),
            industry=archetype_data.get("industry"),
            seniority=archetype_data.get("seniority"),
            is_default=False,
            is_active=True,
            usage_count=0,
            company_id=None,
            created_by="lia-system"
        )
        
        db.add(new_archetype)
        await db.commit()
        await db.refresh(new_archetype)
        
        logger.info(f"✅ Created archetype '{name}' from description")
        
        return ArchetypeGenerationResponse(
            success=True,
            archetype=ArchetypeDTO(
                id=new_archetype.id,
                name=new_archetype.name,
                description=new_archetype.description,
                emoji=new_archetype.emoji or "🎯",
                query=new_archetype.query,
                filters=new_archetype.filters or {},
                tags=new_archetype.tags or [],
                industry=new_archetype.industry,
                seniority=new_archetype.seniority,
                is_default=False,
                is_active=True,
                usage_count=0,
                created_at=new_archetype.created_at.isoformat() if new_archetype.created_at else None
            ),
            job_title="Descrição Personalizada",
            hired_candidate_name=None,
            message=f"Arquétipo '{name}' criado com sucesso"
        )
    
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise HTTPException(status_code=500, detail="Falha ao processar resposta da IA")
    except Exception as e:
        logger.error(f"Error generating archetype from description: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Falha ao gerar arquétipo: {str(e)}")


class ClosedJobSuggestionDTO(BaseModel):
    """Suggestion for creating archetype from closed job."""
    id: int
    title: str
    department: Optional[str] = None
    closed_at: Optional[str] = None
    hired_candidate_name: Optional[str] = None
    has_hired_data: bool = False


class ClosedJobSuggestionsResponse(BaseModel):
    """Response with list of closed jobs that can be used to create archetypes."""
    jobs: List[ClosedJobSuggestionDTO]
    total: int


@router.get("/archetypes/suggestions", response_model=ClosedJobSuggestionsResponse)
async def get_archetype_suggestions(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Lista vagas fechadas que podem ser usadas para criar arquétipos.
    Prioriza vagas com dados do candidato contratado.
    """
    from sqlalchemy import select
    from app.models.job_vacancy import JobVacancy
    
    try:
        result = await db.execute(
            select(JobVacancy)
            .where(JobVacancy.status.in_(["Concluída", "Fechada", "Preenchida"]))
            .order_by(JobVacancy.closed_at.desc().nulls_last())
            .limit(limit)
        )
        jobs = result.scalars().all()
        
        suggestions = []
        for job in jobs:
            hired_data = job.additional_data.get("hired_candidate") if job.additional_data else None
            suggestions.append(ClosedJobSuggestionDTO(
                id=job.id,
                title=job.title,
                department=job.department,
                closed_at=job.closed_at.isoformat() if job.closed_at else None,
                hired_candidate_name=hired_data.get("name") if hired_data else None,
                has_hired_data=bool(hired_data)
            ))
        
        suggestions.sort(key=lambda x: (not x.has_hired_data, x.closed_at or ""))
        
        return ClosedJobSuggestionsResponse(
            jobs=suggestions,
            total=len(suggestions)
        )
    
    except Exception as e:
        logger.error(f"Error fetching archetype suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CV-BASED SEARCH ENDPOINT - Search similar candidates from CV upload
# ============================================================================

class CVSearchResultDTO(BaseModel):
    """Result from CV-based search."""
    parsed_cv: dict
    query_generated: str
    candidates: List[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: Optional[int] = None
    search_time_seconds: Optional[float] = None
    extracted_skills: List[str] = Field(default_factory=list)
    extracted_title: Optional[str] = None


@router.post("/from-cv", response_model=CVSearchResultDTO)
async def search_from_cv(
    file: UploadFile = File(..., description="CV file (PDF, DOCX, DOC, or TXT)"),
    limit: int = Query(20, ge=1, le=50, description="Number of results"),
    search_pearch: bool = Query(True, description="Include Pearch AI search"),
    pearch_type: str = Query("fast", description="Pearch type: fast or pro"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a CV file and search for similar candidates.
    
    Flow:
    1. Parse CV using AI to extract structured data
    2. Build search query from extracted title, skills, and experience
    3. Search for similar candidates in local database and optionally Pearch AI
    4. Return parsed CV data along with matching candidates
    
    Supported formats: PDF, DOCX, DOC, TXT
    Maximum file size: 5MB
    """
    import time
    start_time = time.time()
    
    try:
        parsed_cv = await cv_parser_service.parse_cv(file)
        
        query_parts = []
        extracted_title = None
        extracted_skills = parsed_cv.skills[:10] if parsed_cv.skills else []
        
        if parsed_cv.experiences and len(parsed_cv.experiences) > 0:
            current_exp = parsed_cv.experiences[0]
            if current_exp.title:
                extracted_title = current_exp.title
                query_parts.append(current_exp.title)
        
        if parsed_cv.skills:
            top_skills = parsed_cv.skills[:5]
            query_parts.append(f"com experiência em {', '.join(top_skills)}")
        
        if parsed_cv.location:
            query_parts.append(f"em {parsed_cv.location}")
        
        generated_query = " ".join(query_parts) if query_parts else "profissional experiente"
        
        hybrid_request = HybridSearchRequest(
            query=generated_query,
            search_local_first=True,
            include_pearch=search_pearch,
            pearch_type=SearchType(pearch_type) if pearch_type in ["fast", "pro"] else SearchType.FAST,
            local_limit=limit,
            pearch_limit=limit
        )
        
        result = await pearch_service.hybrid_search(db, hybrid_request)
        
        candidates = []
        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))
        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))
        
        search_time = time.time() - start_time
        
        parsed_cv_dict = {
            "full_name": parsed_cv.full_name,
            "email": parsed_cv.email,
            "phone": parsed_cv.phone,
            "linkedin": parsed_cv.linkedin,
            "github": parsed_cv.github,
            "portfolio": parsed_cv.portfolio,
            "location": parsed_cv.location,
            "summary": parsed_cv.summary,
            "skills": parsed_cv.skills,
            "languages": parsed_cv.languages,
            "certifications": parsed_cv.certifications,
            "confidence_score": parsed_cv.confidence_score,
            "extraction_notes": parsed_cv.extraction_notes,
            "experiences_count": len(parsed_cv.experiences) if parsed_cv.experiences else 0,
            "education_count": len(parsed_cv.education) if parsed_cv.education else 0,
        }
        
        return CVSearchResultDTO(
            parsed_cv=parsed_cv_dict,
            query_generated=generated_query,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=result.pearch_count,
            total_count=result.total_count,
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=search_time,
            extracted_skills=extracted_skills,
            extracted_title=extracted_title
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CV search failed: {str(e)}")


# ============================================================================
# SEARCH ANALYTICS ENDPOINT - Proactive analysis of search results
# ============================================================================

class AnalyzeSearchRequest(BaseModel):
    """Request para análise de resultados de busca."""
    candidates: List[Dict[str, Any]] = Field(..., description="Lista de candidatos para analisar")
    search_criteria: Optional[Dict[str, Any]] = Field(None, description="Critérios de busca opcionais")
    generate_narrative: bool = Field(True, description="Gerar narrativa textual")


class SearchAnalyticsSummary(BaseModel):
    """Summary metrics."""
    total_candidates: int
    local_count: int
    global_count: int
    average_lia_score: float


class ContactQuality(BaseModel):
    """Contact quality metrics."""
    with_valid_phone: int
    with_valid_email: int
    with_linkedin: int
    phone_percentage: float
    email_percentage: float


class SkillMetric(BaseModel):
    """Skill distribution metric."""
    skill: str
    count: int
    percentage: float


class CompanyMetric(BaseModel):
    """Company distribution metric."""
    company: str
    count: int


class ExperienceRange(BaseModel):
    """Experience years range."""
    min: int
    max: int
    average: float
    median: float


class Alert(BaseModel):
    """Alert message."""
    type: str
    message: str


class SuggestedAction(BaseModel):
    """Suggested action."""
    id: str
    label: str
    icon: str
    description: str
    action_type: str


class AnalyzeSearchResponse(BaseModel):
    """Response da análise de busca."""
    summary: SearchAnalyticsSummary
    contact_quality: ContactQuality
    distributions: Dict[str, Dict[str, int]]
    top_skills: List[SkillMetric]
    top_companies: List[CompanyMetric]
    experience_range: ExperienceRange
    alerts: List[Alert]
    suggested_actions: List[SuggestedAction]
    narrative: Optional[str] = None


@router.post("/analyze", response_model=AnalyzeSearchResponse)
async def analyze_search_results(request: AnalyzeSearchRequest):
    """
    Analisa resultados de busca e retorna métricas proativas.
    
    Este endpoint fornece:
    - Summary: Total de candidatos, divisão local/global, score médio
    - Contact Quality: Percentual com telefone, email, LinkedIn
    - Distributions: Senioridade, localização, modelo de trabalho
    - Top Skills: Skills mais comuns nos candidatos
    - Top Companies: Empresas mais comuns
    - Experience Range: Estatísticas de experiência
    - Alerts: Alertas contextuais (ex: concentração em empresas concorrentes)
    - Suggested Actions: Ações sugeridas para o pool de candidatos
    - Narrative: Descrição textual proativa (se generate_narrative=True)
    """
    try:
        analytics = search_analytics_service.analyze_search_results(
            candidates=request.candidates,
            search_criteria=request.search_criteria
        )
        
        if request.generate_narrative:
            narrative = search_analytics_service.generate_proactive_narrative(analytics)
            analytics["narrative"] = narrative
        
        summary = SearchAnalyticsSummary(**analytics["summary"])
        contact_quality = ContactQuality(**analytics["contact_quality"])
        experience_range = ExperienceRange(**analytics["experience_range"])
        
        top_skills = [SkillMetric(**s) for s in analytics["top_skills"]]
        top_companies = [CompanyMetric(**c) for c in analytics["top_companies"]]
        alerts = [Alert(**a) for a in analytics["alerts"]]
        suggested_actions = [SuggestedAction(**a) for a in analytics["suggested_actions"]]
        
        return AnalyzeSearchResponse(
            summary=summary,
            contact_quality=contact_quality,
            distributions=analytics["distributions"],
            top_skills=top_skills,
            top_companies=top_companies,
            experience_range=experience_range,
            alerts=alerts,
            suggested_actions=suggested_actions,
            narrative=analytics.get("narrative")
        )
    
    except Exception as e:
        logger.error(f"Search analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


class EnhancePromptRequest(BaseModel):
    """Request para aprimorar prompt de busca."""
    query: str = Field(..., description="Query original do usuário")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional (vaga, filtros, etc)")


class EnhancePromptSuggestion(BaseModel):
    """Sugestão de melhoria para o prompt."""
    label: str = Field(..., description="Label curto da sugestão")
    value: str = Field(..., description="Valor a adicionar ao prompt")
    category: str = Field(..., description="Categoria: location, experience, skills, industry, salary")


class EnhancePromptResponse(BaseModel):
    """Response com prompt aprimorado."""
    original_query: str
    enhanced_query: str
    explanation: str
    suggestions: List[EnhancePromptSuggestion]
    confidence: float = Field(ge=0, le=1, description="Confiança da sugestão (0-1)")


@router.post("/enhance-prompt", response_model=EnhancePromptResponse)
async def enhance_search_prompt(request: EnhancePromptRequest):
    """
    Analisa e aprimora um prompt de busca de candidatos.
    
    A LIA analisa o prompt original e sugere melhorias baseadas em:
    - Critérios faltantes (localização, experiência, skills, etc)
    - Melhores práticas de busca booleana
    - Contexto da vaga (se fornecido)
    
    Retorna:
    - enhanced_query: Versão otimizada do prompt
    - explanation: Explicação das melhorias
    - suggestions: Sugestões adicionais que o usuário pode aplicar
    """
    from app.services.llm import llm_service
    
    try:
        prompt = f"""Você é LIA, assistente especializada em otimizar buscas de candidatos para recrutamento.

PROMPT ORIGINAL DO RECRUTADOR:
"{request.query}"

{f'CONTEXTO ADICIONAL: {request.context}' if request.context else ''}

CRITÉRIOS ESSENCIAIS PARA UMA BUSCA COMPLETA:
1. CARGO: Título da posição (ex: Desenvolvedor Backend, Product Manager)
2. SENIORIDADE: Nível de experiência (ex: Júnior, Pleno, Sênior, Tech Lead)
3. LOCALIZAÇÃO: Cidade/Estado específico ou modelo de trabalho (ex: São Paulo Capital, Remoto Brasil)
4. HABILIDADES: Skills técnicas específicas (ex: Python, React, AWS)
5. SETOR/INDÚSTRIA: Área de atuação preferida (ex: Fintech, E-commerce, Saúde)
6. EXPERIÊNCIA: Tempo mínimo em anos (ex: 5+ anos de experiência)

REGRAS DE OTIMIZAÇÃO:
1. Mantenha a intenção original mas COMPLETE os critérios faltantes de forma inteligente
2. DESAMBIGUE localizações vagas (ex: "São Paulo" → "São Paulo Capital, SP")
3. Se mencionar tecnologias, sugira nível de proficiência
4. Adicione senioridade se não especificada baseado no contexto
5. O enhanced_query deve ser uma versão MELHOR e MAIS COMPLETA do original
6. Máximo de 200 caracteres para o prompt otimizado
7. Use linguagem natural em português brasileiro

IMPORTANTE: Analise o que FALTA no prompt e sugira completar. Cada sugestão deve indicar um critério específico que melhoraria a busca.

FORMATO DE RESPOSTA (JSON):
{{
  "enhanced_query": "prompt otimizado e mais completo aqui",
  "explanation": "O que foi adicionado: senioridade, localização precisa, etc",
  "suggestions": [
    {{"label": "Nível de experiência", "value": "Sênior 5+ anos", "category": "experience"}},
    {{"label": "Setor preferido", "value": "Fintech ou Startup", "category": "industry"}},
    {{"label": "Modelo de trabalho", "value": "Remoto ou Híbrido SP", "category": "work_model"}}
  ],
  "confidence": 0.85
}}

CATEGORIAS VÁLIDAS: experience, industry, work_model, location, seniority, skills, salary, education, languages

Responda APENAS com o JSON, sem texto adicional."""

        response = await llm_service.generate(prompt, provider="gemini")
        
        import json
        try:
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            result = json.loads(clean_response.strip())
        except json.JSONDecodeError:
            result = {
                "enhanced_query": request.query,
                "explanation": "Prompt mantido como original",
                "suggestions": [],
                "confidence": 0.5
            }
        
        suggestions = []
        for s in result.get("suggestions", []):
            if isinstance(s, dict) and all(k in s for k in ["label", "value", "category"]):
                suggestions.append(EnhancePromptSuggestion(**s))
        
        return EnhancePromptResponse(
            original_query=request.query,
            enhanced_query=result.get("enhanced_query", request.query),
            explanation=result.get("explanation", ""),
            suggestions=suggestions,
            confidence=min(1.0, max(0.0, float(result.get("confidence", 0.7))))
        )
    
    except Exception as e:
        logger.error(f"Prompt enhancement failed: {e}", exc_info=True)
        return EnhancePromptResponse(
            original_query=request.query,
            enhanced_query=request.query,
            explanation="Não foi possível analisar o prompt",
            suggestions=[],
            confidence=0.0
        )


class CalibrationFeedbackRequest(BaseModel):
    """Request para feedback de calibração."""
    candidate_id: str = Field(..., description="ID do candidato")
    feedback: str = Field(..., pattern="^(like|dislike)$", description="Tipo: 'like' ou 'dislike'")
    vacancy_id: Optional[str] = Field(None, description="ID da vaga (opcional)")
    session_id: Optional[str] = Field(None, description="ID da sessão de calibração")
    reason: Optional[str] = Field(None, description="Motivo do feedback")
    candidate_snapshot: Optional[Dict[str, Any]] = Field(None, description="Dados do candidato")


class CalibrationFeedbackResponse(BaseModel):
    """Response do feedback de calibração."""
    status: str
    total_feedbacks: int
    likes_count: int
    dislikes_count: int
    calibration_complete: bool
    confidence_level: float
    learned_patterns: Dict[str, Any]
    message: str
    feedback_id: str
    sourcing_blocked: bool = True
    ready_to_source: bool = False
    feedbacks_remaining: int = 0
    min_feedbacks_required: int = 5


class CalibrationStartRequest(BaseModel):
    """Request para iniciar sessão de calibração."""
    vacancy_id: Optional[str] = Field(None, description="ID da vaga")
    search_criteria: Optional[Dict[str, Any]] = Field(None, description="Critérios de busca")
    sample_size: int = Field(5, ge=3, le=10, description="Quantidade de candidatos para avaliar")


class CalibrationStartResponse(BaseModel):
    """Response do início da calibração."""
    session_id: str
    vacancy_id: Optional[str]
    status: str
    candidates: List[CandidateSearchResultDTO]
    message: str


class CalibrationStatusResponse(BaseModel):
    """Response do status da calibração."""
    session_id: str
    vacancy_id: Optional[str]
    status: str
    total_shown: int
    likes_count: int
    dislikes_count: int
    calibration_complete: bool
    confidence_level: float
    learned_patterns: Optional[Dict[str, Any]]
    message: str
    created_at: Optional[str]
    completed_at: Optional[str]
    sourcing_blocked: bool = True
    ready_to_source: bool = False
    feedbacks_remaining: int = 0
    min_feedbacks_required: int = 5


class VacancyGoalRequest(BaseModel):
    """Request para verificar meta da vaga."""
    vacancy_id: str = Field(..., description="ID da vaga")
    current_count: int = Field(..., ge=0, description="Contagem atual de candidatos")
    target_min: int = Field(50, ge=1, description="Meta mínima")
    target_max: int = Field(70, ge=1, description="Meta máxima")


class VacancyGoalResponse(BaseModel):
    """Response da verificação de meta."""
    status: str
    vacancy_id: str
    current_count: int
    target_range: List[int]
    deficit: int
    surplus: int
    progress_percentage: int
    recommendation: str
    message: str
    suggested_actions: List[Dict[str, Any]]


from app.services.candidate_goal_service import candidate_goal_service as _recruiter_agent


@router.post("/calibration/feedback", response_model=CalibrationFeedbackResponse)
async def submit_calibration_feedback(
    request: CalibrationFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Recebe feedback de calibração do recrutador.
    
    O recrutador avalia candidatos com like/dislike para calibrar o perfil ideal.
    Após 5 feedbacks, o sistema:
    1. Analisa padrões dos feedbacks
    2. Salva critérios aprendidos
    3. Confirma status e desbloqueia sourcing automático
    """
    from datetime import datetime
    from sqlalchemy import select
    from app.models.calibration import CalibrationSession, CalibrationFeedback
    
    try:
        session = None
        if request.session_id:
            stmt = select(CalibrationSession).where(CalibrationSession.id == request.session_id)
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
        
        if not session and request.vacancy_id:
            stmt = select(CalibrationSession).where(
                CalibrationSession.vacancy_id == request.vacancy_id,
                CalibrationSession.sourcing_blocked == True
            ).order_by(CalibrationSession.created_at.desc())
            result = await db.execute(stmt)
            session = result.scalars().first()
        
        if not session:
            import uuid
            session = CalibrationSession(
                id=str(uuid.uuid4()),
                vacancy_id=request.vacancy_id,
                status="awaiting_feedback",
                sourcing_blocked=True,
                min_feedbacks_required=5
            )
            db.add(session)
            await db.flush()
        
        feedback_entry = CalibrationFeedback(
            session_id=session.id,
            candidate_id=request.candidate_id,
            feedback_type=request.feedback,
            reason=request.reason,
            candidate_snapshot=request.candidate_snapshot
        )
        db.add(feedback_entry)
        
        if request.feedback.lower() == "like":
            session.likes_count = (session.likes_count or 0) + 1
        else:
            session.dislikes_count = (session.dislikes_count or 0) + 1
        session.total_shown = (session.total_shown or 0) + 1
        
        min_feedbacks = session.min_feedbacks_required or 5
        feedbacks_remaining = max(0, min_feedbacks - session.total_shown)
        calibration_complete = session.total_shown >= min_feedbacks
        
        if calibration_complete and session.sourcing_blocked:
            stmt = select(CalibrationFeedback).where(
                CalibrationFeedback.session_id == session.id
            )
            result = await db.execute(stmt)
            all_feedbacks = result.scalars().all()
            
            feedbacks_for_analysis = [
                {
                    "feedback": f.feedback_type,
                    "candidate_snapshot": f.candidate_snapshot or {}
                } for f in all_feedbacks
            ]
            
            analysis = await _recruiter_agent.analyze_calibration_patterns_for_session(
                session_id=session.id,
                feedbacks=feedbacks_for_analysis
            )
            
            session.learned_criteria = analysis.get("patterns", {})
            session.status = "confirmed"
            session.sourcing_blocked = False
            session.confirmation_message = analysis.get("confirmation_message", "")
            session.completed_at = datetime.now()
            
            confidence_level = analysis.get("confidence", 0.9)
            message = analysis.get("confirmation_message", "Calibração completa! Sourcing automático liberado.")
        else:
            if session.total_shown >= 3:
                session.status = "learning"
                message = f"Entendendo seu perfil... Faltam {feedbacks_remaining} avaliação(ões)."
            else:
                session.status = "awaiting_feedback"
                message = f"Coletando preferências... Avalie mais {feedbacks_remaining} candidato(s)."
            confidence_level = min(0.9, 0.3 + (session.total_shown * 0.12))
        
        await db.commit()
        
        return CalibrationFeedbackResponse(
            status=session.status,
            total_feedbacks=session.total_shown,
            likes_count=session.likes_count,
            dislikes_count=session.dislikes_count,
            calibration_complete=calibration_complete,
            confidence_level=round(confidence_level, 2),
            learned_patterns=session.learned_criteria or {},
            message=message,
            feedback_id=feedback_entry.id if hasattr(feedback_entry, 'id') else str(uuid.uuid4()),
            sourcing_blocked=session.sourcing_blocked,
            ready_to_source=not session.sourcing_blocked,
            feedbacks_remaining=feedbacks_remaining,
            min_feedbacks_required=min_feedbacks
        )
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Calibration feedback failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Calibration feedback failed: {str(e)}")


@router.post("/calibration/start", response_model=CalibrationStartResponse)
async def start_calibration_session(
    request: CalibrationStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Inicia uma sessão de calibração.
    
    Retorna uma amostra de candidatos para o recrutador avaliar com like/dislike.
    Os feedbacks são usados para calibrar o perfil ideal para a busca.
    Bloqueia sourcing automático até a calibração ser completada (5 feedbacks).
    """
    import uuid
    from sqlalchemy import select, func
    from app.models.candidate import Candidate
    from app.models.calibration import CalibrationSession
    
    try:
        session_id = str(uuid.uuid4())
        sample_size = request.sample_size or 5
        
        new_session = CalibrationSession(
            id=session_id,
            vacancy_id=request.vacancy_id,
            search_criteria=request.search_criteria,
            status="awaiting_feedback",
            min_feedbacks_required=sample_size,
            sourcing_blocked=True,
            total_shown=0,
            likes_count=0,
            dislikes_count=0
        )
        db.add(new_session)
        
        query = select(Candidate).order_by(func.random()).limit(sample_size)
        result = await db.execute(query)
        candidates_orm = result.scalars().all()
        
        candidates = []
        for c in candidates_orm:
            candidates.append(CandidateSearchResultDTO(
                id=str(c.id),
                name=c.name or "Candidato",
                first_name=c.name.split()[0] if c.name else None,
                headline=c.headline,
                current_title=c.current_title,
                current_company=c.current_company,
                location=f"{c.location_city or ''}, {c.location_state or ''}".strip(", "),
                total_experience_years=float(c.years_of_experience) if c.years_of_experience else None,
                skills=c.technical_skills[:10] if c.technical_skills else [],
                score=c.lia_score,
                linkedin_url=c.linkedin_url,
                has_email=bool(c.email),
                has_phone=bool(c.phone),
                source="local"
            ))
        
        await db.commit()
        
        if not candidates:
            return CalibrationStartResponse(
                session_id=session_id,
                vacancy_id=request.vacancy_id,
                status="no_candidates",
                candidates=[],
                message="Não há candidatos disponíveis para calibração. Importe candidatos primeiro."
            )
        
        return CalibrationStartResponse(
            session_id=session_id,
            vacancy_id=request.vacancy_id,
            status="awaiting_feedback",
            candidates=candidates,
            message=f"Sessão de calibração iniciada com {len(candidates)} candidatos. Avalie cada um com like ou dislike para liberar o sourcing automático."
        )
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Start calibration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Start calibration failed: {str(e)}")


@router.get("/calibration/{session_id}/status", response_model=CalibrationStatusResponse)
async def get_calibration_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna o status da sessão de calibração.
    
    Mostra progresso, feedbacks recebidos, padrões aprendidos e estado de bloqueio de sourcing.
    """
    from sqlalchemy import select
    from app.models.calibration import CalibrationSession
    
    try:
        stmt = select(CalibrationSession).where(CalibrationSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            return CalibrationStatusResponse(
                session_id=session_id,
                vacancy_id=None,
                status="not_found",
                total_shown=0,
                likes_count=0,
                dislikes_count=0,
                calibration_complete=False,
                confidence_level=0.0,
                learned_patterns=None,
                message="Sessão de calibração não encontrada.",
                created_at=None,
                completed_at=None,
                sourcing_blocked=True,
                ready_to_source=False,
                feedbacks_remaining=5,
                min_feedbacks_required=5
            )
        
        min_feedbacks = session.min_feedbacks_required or 5
        total_shown = session.total_shown or 0
        likes_count = session.likes_count or 0
        dislikes_count = session.dislikes_count or 0
        feedbacks_remaining = max(0, min_feedbacks - total_shown)
        
        calibration_complete = not session.sourcing_blocked
        confidence_level = min(0.9, 0.3 + (total_shown * 0.12))
        
        if calibration_complete:
            message = session.confirmation_message or "Calibração completa! Sourcing automático liberado."
        elif total_shown >= 3:
            message = f"Calibração em andamento. Faltam {feedbacks_remaining} avaliação(ões)."
        else:
            message = f"Coletando preferências. Avalie mais {feedbacks_remaining} candidato(s)."
        
        return CalibrationStatusResponse(
            session_id=session_id,
            vacancy_id=session.vacancy_id,
            status=session.status or "awaiting_feedback",
            total_shown=total_shown,
            likes_count=likes_count,
            dislikes_count=dislikes_count,
            calibration_complete=calibration_complete,
            confidence_level=round(confidence_level, 2),
            learned_patterns=session.learned_criteria if calibration_complete else None,
            message=message,
            created_at=session.created_at.isoformat() if session.created_at else None,
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            sourcing_blocked=session.sourcing_blocked,
            ready_to_source=not session.sourcing_blocked,
            feedbacks_remaining=feedbacks_remaining,
            min_feedbacks_required=min_feedbacks
        )
    
    except Exception as e:
        logger.error(f"Get calibration status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Get calibration status failed: {str(e)}")


@router.post("/vacancy/goal-check", response_model=VacancyGoalResponse)
async def check_vacancy_candidate_goal(
    request: VacancyGoalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica se a vaga atingiu a meta de candidatos.
    
    Retorna status (abaixo, na meta, acima), recomendações e ações sugeridas.
    """
    try:
        result = await _recruiter_agent.check_vacancy_candidate_goal(
            vacancy_id=request.vacancy_id,
            current_count=request.current_count,
            target_min=request.target_min,
            target_max=request.target_max
        )
        
        return VacancyGoalResponse(
            status=result.get("status", "unknown"),
            vacancy_id=result.get("vacancy_id", request.vacancy_id),
            current_count=result.get("current_count", request.current_count),
            target_range=result.get("target_range", [request.target_min, request.target_max]),
            deficit=result.get("deficit", 0),
            surplus=result.get("surplus", 0),
            progress_percentage=result.get("progress_percentage", 0),
            recommendation=result.get("recommendation", ""),
            message=result.get("message", ""),
            suggested_actions=result.get("suggested_actions", [])
        )
    
    except Exception as e:
        logger.error(f"Vacancy goal check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Vacancy goal check failed: {str(e)}")


class AddCandidatesToVacancyRequest(BaseModel):
    """Request para adicionar candidatos a uma vaga."""
    candidate_ids: List[str] = Field(..., min_length=1, description="Lista de IDs de candidatos para adicionar")
    source: str = Field("local", description="Fonte dos candidatos: 'local' ou 'pearch'")
    added_by: Optional[str] = Field(None, description="ID do usuário que adicionou")


class AddCandidatesToVacancyResponse(BaseModel):
    """Response da adição de candidatos a uma vaga."""
    vacancy_id: str
    added_count: int
    total_count: int
    skipped_count: int
    skipped_ids: List[str] = Field(default_factory=list)
    at_capacity: bool = Field(False, description="Indica se a vaga atingiu capacidade máxima (70)")
    goal_check: VacancyGoalResponse
    message: str


@router.post("/vacancy/{vacancy_id}/add-candidates", response_model=AddCandidatesToVacancyResponse)
async def add_candidates_to_vacancy(
    vacancy_id: str,
    request: AddCandidatesToVacancyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Adiciona candidatos a uma vaga e verifica meta automaticamente.
    
    Workflow:
    1. Verifica se calibração foi completada (BLOQUEIO se sourcing_blocked=True)
    2. Conta candidatos atuais na vaga
    3. Adiciona novos candidatos (até limite de 70)
    4. Chama check_vacancy_candidate_goal
    5. Retorna status e recomendações
    
    A meta de candidatos por vaga é de 50-70 candidatos.
    O sistema não permite adicionar além de 70 candidatos.
    """
    from sqlalchemy import select, func
    from app.models.candidate import VacancyCandidate
    from app.models.calibration import CalibrationSession
    from app.models.job_vacancy import JobVacancy
    import uuid
    
    try:
        vacancy_result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == vacancy_id)
        )
        vacancy = vacancy_result.scalar_one_or_none()
        vacancy_company_id = vacancy.company_id if vacancy else None
        
        calibration_stmt = select(CalibrationSession).where(
            CalibrationSession.vacancy_id == vacancy_id,
        ).order_by(CalibrationSession.created_at.desc())
        calibration_result = await db.execute(calibration_stmt)
        calibration_session = calibration_result.scalars().first()
        
        if calibration_session and calibration_session.sourcing_blocked:
            feedbacks_remaining = max(
                0, 
                (calibration_session.min_feedbacks_required or 5) - (calibration_session.total_shown or 0)
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "calibration_required",
                    "message": "Complete a calibração antes de adicionar candidatos automaticamente.",
                    "feedbacks_remaining": feedbacks_remaining,
                    "session_id": calibration_session.id,
                    "current_feedbacks": calibration_session.total_shown or 0,
                    "min_feedbacks_required": calibration_session.min_feedbacks_required or 5
                }
            )
        
        target_min = 50
        target_max = 70
        
        count_result = await db.execute(
            select(func.count(VacancyCandidate.id)).where(
                VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id)
            )
        )
        current_count = count_result.scalar() or 0
        
        max_to_add = max(0, target_max - current_count)
        candidates_to_add = request.candidate_ids[:max_to_add]
        skipped_ids = request.candidate_ids[max_to_add:]
        
        added_count = 0
        for candidate_id in candidates_to_add:
            try:
                existing = await db.execute(
                    select(VacancyCandidate).where(
                        VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id),
                        VacancyCandidate.candidate_id == uuid.UUID(candidate_id)
                    )
                )
                if existing.scalar_one_or_none() is None:
                    new_vc = VacancyCandidate(
                        vacancy_id=uuid.UUID(vacancy_id),
                        candidate_id=uuid.UUID(candidate_id),
                        company_id=vacancy_company_id,
                        source=request.source,
                        added_by=request.added_by,
                        status="sourced",
                        stage="initial"
                    )
                    db.add(new_vc)
                    added_count += 1
                else:
                    skipped_ids.append(candidate_id)
            except ValueError:
                skipped_ids.append(candidate_id)
        
        await db.commit()
        
        if added_count > 0 and vacancy:
            try:
                from app.models.candidate import Candidate
                
                reqs_result = await db.execute(
                    select(JobRequirement).where(JobRequirement.job_vacancy_id == uuid.UUID(vacancy_id))
                )
                job_requirements = reqs_result.scalars().all()
                
                if job_requirements:
                    requirements_list = [
                        JobRequirementCreate(
                            requirement=req.requirement,
                            description=req.description,
                            priority=_normalize_priority(req.priority),
                            category=req.category
                        )
                        for req in job_requirements
                    ]
                    
                    for cand_id in candidates_to_add:
                        try:
                            cand_result = await db.execute(
                                select(Candidate).where(Candidate.id == uuid.UUID(cand_id))
                            )
                            candidate = cand_result.scalar_one_or_none()
                            
                            if candidate:
                                candidate_data = {
                                    "name": candidate.name,
                                    "current_title": candidate.current_title,
                                    "current_company": candidate.current_company,
                                    "years_of_experience": candidate.years_of_experience,
                                    "seniority_level": candidate.seniority_level,
                                    "technical_skills": candidate.technical_skills or [],
                                    "soft_skills": getattr(candidate, 'soft_skills', []) or [],
                                    "certifications": getattr(candidate, 'certifications', []) or [],
                                    "languages": getattr(candidate, 'languages', {}) or {},
                                    "location_city": candidate.location_city,
                                    "location_state": candidate.location_state,
                                    "education": getattr(candidate, 'education', []) or [],
                                    "work_history": getattr(candidate, 'work_history', []) or [],
                                    "resume_text": getattr(candidate, 'resume_text', None),
                                }
                                
                                await rubric_evaluation_service.evaluate_and_create_activity(
                                    candidate_id=cand_id,
                                    candidate_name=candidate.name or "Candidato",
                                    candidate_data=candidate_data,
                                    job_id=vacancy_id,
                                    job_title=vacancy.title or "Vaga",
                                    job_code=getattr(vacancy, 'code', None) or getattr(vacancy, 'job_code', None),
                                    requirements=requirements_list,
                                    company_id=vacancy_company_id,
                                    created_by=request.added_by,
                                )
                        except Exception as eval_err:
                            logger.warning(f"Rubric evaluation failed for candidate {cand_id}: {eval_err}")
                            
            except Exception as rubric_err:
                logger.warning(f"Rubric evaluation setup failed: {rubric_err}")
        
        new_total = current_count + added_count
        at_capacity = new_total >= target_max
        
        goal_result = await _recruiter_agent.check_vacancy_candidate_goal(
            vacancy_id=vacancy_id,
            current_count=new_total,
            target_min=target_min,
            target_max=target_max
        )
        
        goal_check = VacancyGoalResponse(
            status=goal_result.get("status", "unknown"),
            vacancy_id=vacancy_id,
            current_count=goal_result.get("current_count", new_total),
            target_range=goal_result.get("target_range", [target_min, target_max]),
            deficit=goal_result.get("deficit", 0),
            surplus=goal_result.get("surplus", 0),
            progress_percentage=goal_result.get("progress_percentage", 0),
            recommendation=goal_result.get("recommendation", ""),
            message=goal_result.get("message", ""),
            suggested_actions=goal_result.get("suggested_actions", [])
        )
        
        if at_capacity:
            message = f"Vaga atingiu capacidade máxima! {added_count} candidato(s) adicionado(s). Total: {new_total}/{target_max}."
        elif added_count == 0:
            message = "Nenhum candidato novo adicionado. Candidatos já existem na vaga ou IDs inválidos."
        elif goal_result.get("status") == "on_target":
            message = f"{added_count} candidato(s) adicionado(s). Meta atingida! Total: {new_total}."
        else:
            deficit = goal_result.get("deficit", 0)
            message = f"{added_count} candidato(s) adicionado(s). Total: {new_total}. Faltam {deficit} para meta mínima."
        
        return AddCandidatesToVacancyResponse(
            vacancy_id=vacancy_id,
            added_count=added_count,
            total_count=new_total,
            skipped_count=len(skipped_ids),
            skipped_ids=skipped_ids[:10],
            at_capacity=at_capacity,
            goal_check=goal_check,
            message=message
        )
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Add candidates to vacancy failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Add candidates to vacancy failed: {str(e)}")


@router.get("/vacancy/{vacancy_id}/candidates/count")
async def get_vacancy_candidates_count(
    vacancy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna a contagem de candidatos em uma vaga e o status da meta.
    """
    from sqlalchemy import select, func
    from app.models.candidate import VacancyCandidate
    import uuid
    
    try:
        count_result = await db.execute(
            select(func.count(VacancyCandidate.id)).where(
                VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id)
            )
        )
        current_count = count_result.scalar() or 0
        
        goal_result = await _recruiter_agent.check_vacancy_candidate_goal(
            vacancy_id=vacancy_id,
            current_count=current_count,
            target_min=50,
            target_max=70
        )
        
        return {
            "vacancy_id": vacancy_id,
            "current_count": current_count,
            "target_min": 50,
            "target_max": 70,
            "status": goal_result.get("status", "unknown"),
            "progress_percentage": goal_result.get("progress_percentage", 0),
            "recommendation": goal_result.get("recommendation", ""),
            "message": goal_result.get("message", "")
        }
    
    except Exception as e:
        logger.error(f"Get vacancy candidates count failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Get vacancy candidates count failed: {str(e)}")
