"""
Shared imports, constants, helper functions, and Pydantic models for candidate_search package.
"""
import logging
from enum import Enum as PyEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service
from app.models.pearch import (
    CandidateProfile,
)
from app.models.rubric import JobRequirement
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

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
        parts.append(f'li:{linkedin_id}')
    if email:
        parts.append(f'email:{email.lower()}')
    fingerprint_str = '|'.join(sorted(parts))
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]


async def _get_job_requirements(
    db: AsyncSession,
    job_id: str
) -> list[JobRequirementCreate] | None:
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
    title: str | None = None
    company: str | None = None
    company_name: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_years: float | None = None
    description: str | None = None
    current: bool = False
    industries: list[str] = Field(default_factory=list)
    company_size: str | None = None
    company_size_range: str | None = None
    technologies: list[str] = Field(default_factory=list)
    is_startup: bool | None = None
    company_linkedin_url: str | None = None
    company_domain: str | None = None


class EducationDTO(BaseModel):
    school: str | None = None
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class LanguageDTO(BaseModel):
    language: str | None = None
    name: str | None = None
    proficiency: str | None = None
    level: str | None = None


class CandidateSearchResultDTO(BaseModel):
    """Resultado individual para o frontend."""
    id: str
    name: str
    first_name: str | None = None
    last_name: str | None = None
    picture_url: str | None = None
    headline: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    location: str | None = None
    total_experience_years: float | None = None
    skills: list[str] = Field(default_factory=list)
    score: float | None = None
    match_summary: str | None = None
    linkedin_url: str | None = None
    has_email: bool = False
    has_phone: bool = False
    email: str | None = None
    phone: str | None = None
    source: str = 'local'
    is_open_to_work: bool | None = None
    is_discovered: bool = False
    summary: str | None = None
    experiences: list[ExperienceDTO] = Field(default_factory=list)
    work_history: list[ExperienceDTO] = Field(default_factory=list)
    education: list[EducationDTO] = Field(default_factory=list)
    languages: list[LanguageDTO] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    company_industries: list[str] = Field(default_factory=list)
    company_size: str | None = Field(None)
    rubric_score: float | None = Field(None)
    rubric_match_label: str | None = Field(None)
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

        top_level_company_industries: list[str] = []
        top_level_company_size: str | None = None
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
    thread_id: str | None = None
    candidates: list[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_used: int | None = None
    credits_remaining: int | None = None
    search_time_seconds: float | None = None
    warning_message: str | None = None
    can_load_more: bool = False
    should_expand_to_global: bool = Field(default=False)
    expansion_message: str | None = Field(default=None)
    high_adherence_count: int = Field(default=0)


def _build_candidate_data_from_dto(candidate_dto: 'CandidateSearchResultDTO') -> dict[str, Any]:
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
    candidates: list['CandidateSearchResultDTO'],
    requirements: list[JobRequirementCreate],
) -> list['CandidateSearchResultDTO']:
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
    thread_id: str | None = Field(None, description="Thread ID para refinamento")
    
    # SearchSpec - metadados estruturados extraídos pelo LLM do frontend
    search_spec: dict[str, Any] | None = Field(None, description="Metadados estruturados (location, skills, seniority, etc)")
    
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
    job_vacancy_id: int | None = Field(None)
    exclude_candidate_ids: list[str] = Field(default_factory=list)
    
    # Include discovered candidates from staging table
    include_discovered: bool = Field(True, description="Include discovered candidates from staging table")
    
    # Rubric evaluation - optional job_id to evaluate candidates against job requirements
    job_id: str | None = Field(None, description="Job UUID for rubric evaluation. If provided, candidates will be scored against job requirements.")



class ImportCandidateExperienceDTO(BaseModel):
    """Experiência para importação com dados ricos de empresa."""
    company_name: str
    company_linkedin_url: str | None = None
    company_domain: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_years: float | None = None
    is_current: bool = False
    description: str | None = None
    location: str | None = None
    industries: list[str] = Field(default_factory=list)
    company_size: str | None = None
    company_size_range: str | None = None
    technologies: list[str] = Field(default_factory=list)
    is_startup: bool | None = None
    company_founded_year: int | None = None
    company_annual_revenue: float | None = None
    # Campos de company_info da Pearch
    company_followers_count: int | None = None
    company_keywords: list[str] = Field(default_factory=list)
    company_is_hiring: bool | None = None



class ImportCandidateDTO(BaseModel):
    """Candidato Pearch para importação na base local."""
    pearch_id: str
    name: str
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    avatar_url: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    headline: str | None = None
    summary: str | None = None
    location: str | None = None
    years_of_experience: float | None = None
    skills: list[str] = Field(default_factory=list)
    languages: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    experiences: list[ImportCandidateExperienceDTO] = Field(default_factory=list)
    is_open_to_work: bool | None = None
    is_decision_maker: bool | None = None
    is_top_universities: bool | None = None
    is_hiring: bool | None = None
    expertise: list[str] = Field(default_factory=list)
    # Campos de contato Pearch
    best_personal_email: str | None = None
    best_business_email: str | None = None
    personal_emails: list[str] = Field(default_factory=list)
    business_emails: list[str] = Field(default_factory=list)
    phone_types: dict[str, Any] | None = None
    # Campos de perfil Pearch
    estimated_age: int | None = None
    linkedin_followers_count: int | None = None
    linkedin_connections_count: int | None = None
    # Insights e mensagem
    insights: dict[str, Any] | None = None
    outreach_message: str | None = None
    match_reasoning: str | None = None



class ImportCandidatesRequest(BaseModel):
    """Request para importar candidatos Pearch para base local."""
    candidates: list[ImportCandidateDTO]
    source_search_query: str | None = None
    add_to_vacancy_id: str | None = None


class IdMapping(BaseModel):
    """Mapeamento de pearch_id para local_id."""
    pearch_id: str
    local_id: str


class ImportCandidatesResponse(BaseModel):
    """Response da importação de candidatos."""
    imported_count: int
    skipped_count: int
    updated_count: int = 0
    imported_ids: list[str]
    skipped_ids: list[str]
    mapping: list[IdMapping]
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
    candidate_ids: list[str] = Field(..., description="Lista de UUIDs dos candidatos a avaliar", min_length=1, max_length=100)


class EvaluateForJobResult(BaseModel):
    """Resultado da avaliação de um candidato."""
    candidate_id: str
    rubric_score: float | None = None
    rubric_match_label: str | None = None
    rubric_evaluated: bool = False
    error: str | None = None


class EvaluateForJobResponse(BaseModel):
    """Response da avaliação em batch."""
    job_id: str
    total_candidates: int
    evaluated_count: int
    failed_count: int
    results: list[EvaluateForJobResult]
