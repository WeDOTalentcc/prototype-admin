"""
Shared imports, constants, helper functions, and Pydantic models for candidate_search package.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.auth.dependencies import get_current_user_or_demo, get_user_company_id, assert_resource_ownership
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
from app.auth.models import User as ImportUser
from app.services.candidate_goal_service import candidate_goal_service as _recruiter_agent

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
        parts.append(f'li:{linkedin_id}')
    if email:
        parts.append(f'email:{email.lower()}')
    fingerprint_str = '|'.join(sorted(parts))
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]


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
        logger.warning(f'Failed to fetch job requirements for job_id={job_id}: {e}')
        return None


def _get_match_label(score: float) -> str:
    """Get match label based on rubric score."""
    if score >= 85:
        return 'Exceeds'
    elif score >= 70:
        return 'Meets'
    elif score >= 40:
        return 'Partial'
    else:
        return 'Missing'


# ============================================================================
# SHARED PYDANTIC MODELS
# ============================================================================

class ExperienceDTO(BaseModel):
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


class EducationDTO(BaseModel):
    school: Optional[str] = None
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class LanguageDTO(BaseModel):
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
    score: Optional[float] = None
    match_summary: Optional[str] = None
    linkedin_url: Optional[str] = None
    has_email: bool = False
    has_phone: bool = False
    email: Optional[str] = None
    phone: Optional[str] = None
    source: str = 'local'
    is_open_to_work: Optional[bool] = None
    is_discovered: bool = False
    summary: Optional[str] = None
    experiences: List[ExperienceDTO] = Field(default_factory=list)
    work_history: List[ExperienceDTO] = Field(default_factory=list)
    education: List[EducationDTO] = Field(default_factory=list)
    languages: List[LanguageDTO] = Field(default_factory=list)
    expertise: List[str] = Field(default_factory=list)
    company_industries: List[str] = Field(default_factory=list)
    company_size: Optional[str] = Field(None)
    rubric_score: Optional[float] = Field(None)
    rubric_match_label: Optional[str] = Field(None)
    rubric_evaluated: bool = Field(False)

    @classmethod
    def from_profile(cls, profile: CandidateProfile, source: str = 'local') -> 'CandidateSearchResultDTO':
        """Converte CandidateProfile para DTO do frontend."""
        experiences_dto = []
        for exp in (profile.experiences or []):
            company_info = exp.company_info
            industries = company_info.industries if company_info else []
            technologies = company_info.technologies if company_info else []
            company_size = str(company_info.num_employees) if company_info and company_info.num_employees else None
            company_size_range = company_info.num_employees_range if company_info else None
            is_startup = company_info.is_startup if company_info else None
            company_linkedin_url = company_info.linkedin_url if company_info else None
            company_domain = company_info.domain if company_info else None

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
                        current=role.end_date is None or role.end_date == '',
                        industries=industries,
                        company_size=company_size,
                        company_size_range=company_size_range,
                        technologies=technologies,
                        is_startup=is_startup,
                        company_linkedin_url=company_linkedin_url,
                        company_domain=company_domain
                    ))
            else:
                experiences_dto.append(ExperienceDTO(
                    title=exp.title,
                    company=exp.company,
                    company_name=exp.company,
                    location=exp.location,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    duration_years=exp.duration_years,
                    description=exp.description,
                    current=exp.end_date is None or exp.end_date == '',
                    industries=industries,
                    company_size=company_size,
                    company_size_range=company_size_range,
                    technologies=technologies,
                    is_startup=is_startup,
                    company_linkedin_url=company_linkedin_url,
                    company_domain=company_domain
                ))

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
            id=profile.docid or '',
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
            summary=profile.summary,
            experiences=experiences_dto,
            work_history=experiences_dto,
            education=education_dto,
            languages=languages_dto,
            expertise=profile.expertise[:10] if profile.expertise else [],
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
    should_expand_to_global: bool = Field(default=False)
    expansion_message: Optional[str] = Field(default=None)
    high_adherence_count: int = Field(default=0)


def _build_candidate_data_from_dto(candidate_dto: 'CandidateSearchResultDTO') -> Dict[str, Any]:
    """Build candidate data dict for rubric evaluation from CandidateSearchResultDTO."""
    work_history = []
    for exp in (candidate_dto.experiences or candidate_dto.work_history or []):
        work_history.append({
            'title': exp.title,
            'company_name': exp.company or exp.company_name,
            'start_date': exp.start_date,
            'end_date': exp.end_date,
            'description': exp.description,
            'technologies': exp.technologies or [],
        })
    education = []
    for edu in (candidate_dto.education or []):
        education.append({
            'degree': edu.degree,
            'institution': edu.school or edu.institution,
            'field_of_study': edu.field_of_study,
        })
    return {
        'id': candidate_dto.id,
        'name': candidate_dto.name,
        'current_title': candidate_dto.current_title,
        'current_company': candidate_dto.current_company,
        'years_of_experience': candidate_dto.total_experience_years,
        'skills': candidate_dto.skills or [],
        'technical_skills': candidate_dto.skills or [],
        'expertise': candidate_dto.expertise or [],
        'work_history': work_history,
        'education': education,
        'self_introduction': candidate_dto.summary,
    }


async def _evaluate_candidates_with_rubrics(
    candidates: List['CandidateSearchResultDTO'],
    requirements: List[JobRequirementCreate],
) -> List['CandidateSearchResultDTO']:
    """Evaluate candidates using rubric evaluation service."""
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
            logger.warning(f'Failed to evaluate candidate {candidate.id} with rubrics: {e}')
            candidate.rubric_evaluated = False
    return candidates


# ============================================================================
# ADDITIONAL MODELS (from core_search preamble)
# ============================================================================

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
