"""
Shared imports, constants, helper functions, and Pydantic models for candidate_search package.
"""
import logging
from enum import Enum as PyEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    assert_resource_ownership,  # noqa: F401
    get_current_user_or_demo,  # noqa: F401
    get_user_company_id,  # noqa: F401
)
from app.auth.models import User  # noqa: F401
from app.auth.models import User as ImportUser  # noqa: F401
from app.core.database import get_db  # noqa: F401
from app.domains.cv_screening.services.cv_parser import CVParserService, cv_parser_service, get_cv_parser_service  # noqa: F401
from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService, rubric_evaluation_service, get_rubric_evaluation_service
from app.domains.sourcing.services.pearch_service import PearchService, get_pearch_service, pearch_service  # noqa: F401
from app.domains.sourcing.services.contact_enrichment_service import (  # noqa: F401
    ContactEnrichmentService,
    contact_enrichment_service,
    get_contact_enrichment_service,
)
from app.domains.sourcing.services.search_analytics import search_analytics_service  # noqa: F401
from lia_models.pearch import (  # noqa: F401
    CandidateProfile,
    HybridSearchRequest,
    PearchSearchRequest,
    SearchType,
)
from lia_models.rubric import JobRequirement
from app.schemas.archetype import (
    ArchetypeFromSearchCreate,  # noqa: F401
    ArchetypeFromSearchResponse,  # noqa: F401
    ArchetypeResponse,  # noqa: F401
)
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
from app.shared.services.archetype_builder_service import (
    build_archetype_from_search,  # noqa: F401
    extract_tags_from_search_spec,  # noqa: F401
)

logger = logging.getLogger(__name__)


# TODO(phase2): extract to repository — candidate search shared DB access
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
    contact_source: str | None = None
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


class DiscardedCandidateDTO(BaseModel):
    """Resumo leve de um candidato descartado por não ter contato.

    Task #400: além de contar quantos foram descartados, devolvemos uma lista
    leve para o frontend exibir/exportar e permitir reaproveitamento manual
    (ex.: re-enriquecer pelo LinkedIn ou abrir o perfil para enviar mensagem).
    """
    id: str
    name: str
    headline: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    picture_url: str | None = None
    source: str | None = None


class EnrichmentStats(BaseModel):
    """Estatísticas do passo de enriquecimento de contatos.

    Task #394: o backend filtra silenciosamente candidatos sem email/telefone
    após tentativa de Apify. Estes contadores permitem o frontend explicar ao
    usuário por que o total caiu (ex.: "8 candidatos descartados por não termos
    como contatar").

    Task #400: também devolvemos a lista (`filtered_candidates`) com dados
    mínimos para o usuário inspecionar/exportar quem foi descartado.
    """
    filtered_no_contact: int = 0
    enrichment_attempted: int = 0
    filtered_candidates: list[DiscardedCandidateDTO] = Field(default_factory=list)


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
    degraded_sources: list[str] | None = None
    can_load_more: bool = False
    should_expand_to_global: bool = Field(default=False)
    expansion_message: str | None = Field(default=None)
    high_adherence_count: int = Field(default=0)
    filtered_no_contact: int = Field(default=0)
    enrichment_attempted: int = Field(default=0)
    filtered_candidates: list[DiscardedCandidateDTO] = Field(default_factory=list)
    # Task #403: id da linha em ``candidate_searches`` que registrou esta
    # execução. O frontend persiste esse id no histórico para conseguir
    # recarregar (via GET /search/{id}/discarded) os descartados após refresh.
    search_id: str | None = None


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
    pearch_type: str = Field("fast", description="Tipo de busca (sempre fast)")
    
    # Limites
    local_limit: int = Field(20, ge=1, le=100)
    pearch_limit: int = Field(15, ge=0, le=50)
    
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


async def persist_search_with_discards(
    db: AsyncSession,
    *,
    user: Any,
    query: str,
    search_source: str,
    local_count: int,
    pearch_count: int,
    total_count: int,
    used_global_search: bool,
    discarded: list[DiscardedCandidateDTO],
    search_filters: dict[str, Any] | None = None,
    search_duration_ms: int | None = None,
) -> str | None:
    """Task #403 — registra a execução em ``candidate_searches`` com a lista
    leve de candidatos descartados serializada em JSON.

    Best-effort: qualquer falha (modelo desatualizado, coluna ausente, sessão
    inválida) é logada como warning e o endpoint segue retornando os dados.
    Retorna o ``search_id`` gerado quando a persistência funciona.
    """
    if not user:
        return None

    try:
        from lia_models.candidate import CandidateSearch as _CandidateSearch

        user_id = getattr(user, "id", None) or getattr(user, "email", None)
        if user_id is None:
            return None

        record = _CandidateSearch(
            user_id=str(user_id),
            search_query=query or "",
            search_filters=search_filters or {},
            local_results_count=int(local_count or 0),
            global_results_count=int(pearch_count or 0),
            total_results=int(total_count or 0),
            used_global_search=bool(used_global_search),
            search_source=search_source or "local",
            search_duration_ms=search_duration_ms,
            discarded_candidates=[d.model_dump(mode="json") for d in (discarded or [])],
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return str(record.id)
    except Exception as exc:
        # Não derruba a busca se a persistência falhar — o usuário ainda
        # recebe a resposta normalmente.
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning("[Task403] Failed to persist search record with discards: %s", exc)
        return None


async def load_discarded_for_search(
    db: AsyncSession,
    *,
    user: Any,
    search_id: str,
) -> list[DiscardedCandidateDTO] | None:
    """Task #403 — recupera a lista de descartados de uma execução prévia.

    Retorna ``None`` quando o ``search_id`` não existe ou não pertence ao
    usuário corrente (evita vazar dados entre tenants).
    """
    try:
        from uuid import UUID as _UUID
        from sqlalchemy import select
        from lia_models.candidate import CandidateSearch as _CandidateSearch

        try:
            search_uuid = _UUID(str(search_id))
        except (ValueError, TypeError):
            return None

        user_id = getattr(user, "id", None) or getattr(user, "email", None)
        if user_id is None:
            return None

        result = await db.execute(
            select(_CandidateSearch).where(_CandidateSearch.id == search_uuid)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if str(row.user_id) != str(user_id):
            # Tenant isolation — outro usuário, não revelar.
            return None

        raw = row.discarded_candidates or []
        out: list[DiscardedCandidateDTO] = []
        for item in raw:
            try:
                out.append(DiscardedCandidateDTO(**item))
            except Exception:
                continue
        return out
    except Exception as exc:
        logger.warning("[Task403] Failed to load discarded candidates: %s", exc)
        return None


async def enrich_and_filter_candidates(
    db: AsyncSession,
    candidates: list["CandidateSearchResultDTO"],
) -> tuple[list["CandidateSearchResultDTO"], EnrichmentStats]:
    """Enriquece contatos via Apify quando faltam e filtra quem ficou sem contato.

    Returns:
        Tupla `(kept, stats)` onde `kept` é a lista filtrada e `stats` contém
        `filtered_no_contact` (descartados após enriquecimento) e
        `enrichment_attempted` (quantos passaram pelo Apify).
    """
    from uuid import UUID as _UUID
    from sqlalchemy import select
    from lia_models.candidate import Candidate

    enrichment_svc = get_contact_enrichment_service()

    uuid_enrichment = []
    url_enrichment = []

    for cand in candidates:
        has_email = bool(cand.email or getattr(cand, "best_personal_email", None) or getattr(cand, "best_business_email", None))
        has_phone = bool(getattr(cand, "phone", None) or getattr(cand, "phone_numbers", None))
        if not has_email and not has_phone:
            linkedin = cand.linkedin_url or getattr(cand, "linkedin_slug", None)
            if linkedin and cand.id:
                linkedin_full = linkedin if str(linkedin).startswith("http") else f"https://www.linkedin.com/in/{linkedin}"
                try:
                    _UUID(str(cand.id))
                    uuid_enrichment.append({
                        "id": str(cand.id),
                        "linkedin_url": linkedin_full,
                    })
                except (ValueError, AttributeError):
                    url_enrichment.append({
                        "cand_id": str(cand.id),
                        "linkedin_url": linkedin_full,
                    })

    enriched_ids: set[str] = set()

    if uuid_enrichment:
        logger.info("[EnrichHook] Enriching %d UUID candidates via enrich_batch", len(uuid_enrichment))
        try:
            results = await enrichment_svc.enrich_batch(db, uuid_enrichment)
            for item, res in zip(uuid_enrichment, results):
                if isinstance(res, dict) and res.get("success"):
                    enriched_ids.add(str(item["id"]))
        except Exception as e:
            logger.warning("[EnrichHook] Batch enrichment failed (non-fatal): %s", e)

    if url_enrichment:
        logger.info("[EnrichHook] Enriching %d non-UUID candidates via Apify direct", len(url_enrichment))
        for item in url_enrichment:
            try:
                apify_result = await enrichment_svc.enrich_by_linkedin_url(
                    item["linkedin_url"]
                )
                if apify_result.get("success") and apify_result.get("has_contact"):
                    email = apify_result.get("email")
                    phone = apify_result.get("phone")
                    for cand in candidates:
                        if str(cand.id) == item["cand_id"]:
                            if email and not cand.email:
                                cand.email = email
                                cand.has_email = True
                            if phone and not cand.phone:
                                cand.phone = phone
                                cand.has_phone = True
                            cand.contact_source = "apify"
                            enriched_ids.add(item["cand_id"])
                            break
            except Exception as e:
                logger.warning("[EnrichHook] Apify direct failed for %s: %s", item["cand_id"], e)

    uuid_enriched = {eid for eid in enriched_ids if eid not in {i["cand_id"] for i in url_enrichment}}
    if uuid_enriched:
        try:
            uuid_ids = []
            for eid in uuid_enriched:
                try:
                    uuid_ids.append(_UUID(eid))
                except (ValueError, AttributeError):
                    pass
            if uuid_ids:
                result = await db.execute(
                    select(Candidate).where(Candidate.id.in_(uuid_ids))
                )
                db_candidates = {str(c.id): c for c in result.scalars().all()}
                for cand in candidates:
                    db_cand = db_candidates.get(str(cand.id))
                    if db_cand:
                        if db_cand.email and not cand.email:
                            cand.email = db_cand.email
                            cand.has_email = True
                        if getattr(db_cand, "phone", None) and not cand.phone:
                            cand.phone = db_cand.phone
                            cand.has_phone = True
        except Exception as e:
            logger.warning("[EnrichHook] Failed to reload enriched contacts from DB: %s", e)

    kept = []
    discarded: list[DiscardedCandidateDTO] = []
    for cand in candidates:
        has_email = bool(cand.email or getattr(cand, "best_personal_email", None) or getattr(cand, "best_business_email", None))
        has_phone = bool(getattr(cand, "phone", None) or getattr(cand, "phone_numbers", None))
        if has_email or has_phone:
            if not cand.contact_source:
                if str(cand.id) in enriched_ids:
                    cand.contact_source = "apify"
                elif cand.source == "pearch":
                    cand.contact_source = "pearch"
                else:
                    cand.contact_source = "local"
            kept.append(cand)
        else:
            logger.debug("[EnrichHook] Filtering candidate %s — no contact", cand.id)
            def _s(value: object) -> str | None:
                return value if isinstance(value, str) and value else None
            discarded.append(DiscardedCandidateDTO(
                id=str(cand.id),
                name=_s(getattr(cand, "name", None)) or "",
                headline=_s(getattr(cand, "headline", None)),
                current_title=_s(getattr(cand, "current_title", None)),
                current_company=_s(getattr(cand, "current_company", None)),
                location=_s(getattr(cand, "location", None)),
                linkedin_url=_s(getattr(cand, "linkedin_url", None)),
                picture_url=_s(getattr(cand, "picture_url", None)),
                source=_s(getattr(cand, "source", None)),
            ))

    filtered = len(candidates) - len(kept)
    if filtered > 0:
        logger.info("[EnrichHook] Filtered %d candidates without contact. Returning %d/%d", filtered, len(kept), len(candidates))

    stats = EnrichmentStats(
        filtered_no_contact=filtered,
        enrichment_attempted=len(uuid_enrichment) + len(url_enrichment),
        filtered_candidates=discarded,
    )
    return kept, stats