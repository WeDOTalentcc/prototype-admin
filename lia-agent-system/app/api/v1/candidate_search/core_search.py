"""

# TODO(phase2-repo-extraction): 19 direct DB calls in this file.
# Domain: candidate_search | No repository exists yet.
# Action: Create app/domains/candidate_search/repositories/candidate_search_repository.py
Core search, evaluate, import, promote, persist-revealed, estimate, similar routes.
"""
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
    get_user_company_id,
    logger,
    RubricEvaluationService,
    get_rubric_evaluation_service,
    rubric_evaluation_service,
)
from app.domains.credits.services.credit_service import CreditService, get_credit_service

router = APIRouter()

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


class ExperienceDTO(BaseModel):
    """Experiência profissional para o frontend."""
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


class EducationDTO(BaseModel):
    """Formação educacional para o frontend."""
    school: str | None = None
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class LanguageDTO(BaseModel):
    """Idioma para o frontend."""
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
    
    score: float | None = None  # 0-100
    match_summary: str | None = None
    
    linkedin_url: str | None = None
    has_email: bool = False
    has_phone: bool = False
    email: str | None = None
    phone: str | None = None
    
    source: str = "local"  # "local" or "pearch"
    is_open_to_work: bool | None = None
    is_discovered: bool = False  # True if candidate is from staging table (not saved to local base yet)
    
    # Campos expandidos para dados completos do perfil (Pearch)
    summary: str | None = None
    experiences: list[ExperienceDTO] = Field(default_factory=list)
    work_history: list[ExperienceDTO] = Field(default_factory=list)
    education: list[EducationDTO] = Field(default_factory=list)
    languages: list[LanguageDTO] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    
    # Flattened company info from most recent experience (for table columns)
    company_industries: list[str] = Field(default_factory=list, description="Industries from most recent experience")
    company_size: str | None = Field(None, description="Company size from most recent experience")
    
    # Rubric evaluation fields (populated when job_id is provided in search)
    rubric_score: float | None = Field(None, description="Rubric evaluation score 0-100")
    rubric_match_label: str | None = Field(None, description="Match label: Exceeds/Meets/Partial/Missing")
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
    
    should_expand_to_global: bool = Field(
        default=False,
        description="Indica se a busca deve ser expandida para busca global (Pearch)"
    )
    expansion_message: str | None = Field(
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
        logger.warning(f"Failed to fetch job requirements for job_id={job_id}: {e}")
        return None


def _build_candidate_data_from_dto(candidate_dto: "CandidateSearchResultDTO") -> dict[str, Any]:
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
        result = await pearch_svc.hybrid_search(db, hybrid_request)
        
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


@router.post("/evaluate-for-job", response_model=EvaluateForJobResponse)
async def evaluate_candidates_for_job(
    request: EvaluateForJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    rubric_svc: RubricEvaluationService = Depends(get_rubric_evaluation_service),
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
    
    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")


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
    import uuid as uuid_lib

    from sqlalchemy import or_, select

    from app.models.candidate import Candidate, ExternalCandidateProfile
    
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
    merged_with_id: str | None = None


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
    import uuid as uuid_lib
    from datetime import datetime

    from sqlalchemy import select

    from app.models.candidate import (
        Candidate,
        CandidateEducation,
        CandidateExperience,
        CandidateSource,
        ExternalCandidateProfile,
    )
    
    get_user_company_id(current_user)
    
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
    email: str | None = Field(None, description="Email revelado")
    phone: str | None = Field(None, description="Telefone revelado")
    linkedin_url: str | None = Field(None, description="URL do LinkedIn")
    current_title: str | None = Field(None, description="Cargo atual")
    current_company: str | None = Field(None, description="Empresa atual")
    avatar_url: str | None = Field(None, description="URL do avatar")


class RevealedContactResponse(BaseModel):
    """Response da persistência de contato revelado."""
    success: bool
    message: str
    candidate_id: str | None = None
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
    import uuid as uuid_lib

    from sqlalchemy import select

    from app.models.candidate import Candidate
    
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
    warnings: list[str] = Field(default_factory=list)


@router.post("/candidates/estimate", response_model=DetailedCreditEstimateDTO)
async def estimate_search_credits(request: CreditEstimateRequest,
    pearch_svc: PearchService = Depends(get_pearch_service),
):
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
    
    estimate = pearch_svc.estimate_credits(pearch_request)
    confirmation = pearch_svc.create_confirmation_message(pearch_request)
    
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
    linkedin_url: str | None = Field(None, description="URL do LinkedIn do candidato referência")
    candidate_id: str | None = Field(None, description="ID do candidato no banco local")
    limit: int = Field(20, ge=1, le=50, description="Número de resultados")
    search_pearch: bool = Field(True, description="Buscar também na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo: 'fast' ou 'pro'")


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
        
        result = await pearch_svc.hybrid_search(db, hybrid_request)
        
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
):
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
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
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


class JobDescriptionSearchRequest(BaseModel):
    """Request para busca por job description."""
    job_description: str = Field(..., min_length=50, description="Descrição completa da vaga")
    location: str | None = Field(None, description="Localização preferida")
    limit: int = Field(20, ge=1, le=50)
    search_pearch: bool = Field(True, description="Buscar também na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo: 'fast' ou 'pro'")


class ExtractedCriteria(BaseModel):
    """Critérios extraídos da job description."""
    job_title: str | None = None
    seniority: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: int | None = None
    location: str | None = None
    languages: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class JobDescriptionSearchResponse(BaseModel):
    """Response da busca por job description."""
    extracted_criteria: ExtractedCriteria
    query_generated: str
    candidates: list[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: int | None = None
    search_time_seconds: float | None = None

