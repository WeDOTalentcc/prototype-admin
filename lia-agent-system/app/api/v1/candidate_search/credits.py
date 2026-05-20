"""Credit estimate route: POST /candidates/estimate"""
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

class CreditEstimateRequest(WeDoBaseModel):
    """Request completo para estimativa de créditos."""
    query: str = Field(..., description="Query de busca")
    pearch_type: str = Field("fast", description="Tipo de busca (apenas fast)", pattern="^fast$")
    limit: int = Field(15, ge=1, le=50)
    
    insights: bool = Field(True, description="Incluir insights (+1 crédito)")
    high_freshness: bool = Field(False, description="Dados em tempo real (+2 créditos)")
    profile_scoring: bool = Field(True, description="Scoring (+1 crédito)")
    strict_filters: bool = Field(False, description="Filtros rigorosos")


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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Estima o custo em créditos ANTES de executar a busca.
    
    Use este endpoint para mostrar ao usuário quanto a busca irá custar.
    Aceita todos os parâmetros Pearch para cálculo preciso.
    """
    pearch_request = PearchSearchRequest(
        query=request.query,
        type=SearchType.FAST,
        insights=request.insights,
        high_freshness=request.high_freshness,
        profile_scoring=request.profile_scoring,
        custom_filters=None,
        strict_filters=request.strict_filters,
        require_emails=False,
        show_emails=False,
        require_phone_numbers=False,
        require_phones_or_emails=False,
        show_phone_numbers=False,
        limit=request.limit
    )
    
    estimate = pearch_svc.estimate_credits(pearch_request)
    
    warnings = []
    if estimate.total_estimated > 100:
        warnings.append(f"Custo total estimado alto: {estimate.total_estimated} créditos")
    warnings.append("Contatos enriquecidos via Apify ($0.01/candidato) quando não disponíveis no Pearch")
    
    apify_note = f" + Apify ~$0.01/candidato para enriquecimento de contato"
    confirmation_msg = (
        f"Busca estimada em {estimate.total_estimated} créditos "
        f"({estimate.total_per_candidate}/candidato x {request.limit}){apify_note}"
    )
    
    return DetailedCreditEstimateDTO(
        query=request.query,
        pearch_type=request.pearch_type,
        limit=request.limit,
        base_cost=estimate.base_cost,
        insights_cost=estimate.insights_cost,
        freshness_cost=estimate.freshness_cost,
        email_cost=0,
        phone_cost=0,
        cost_per_candidate=estimate.total_per_candidate,
        total_estimated=estimate.total_estimated,
        breakdown={
            "base": estimate.base_cost,
            "insights": estimate.insights_cost,
            "emails": 0,
            "phones": 0,
            "freshness": estimate.freshness_cost
        },
        confirmation_message=confirmation_msg,
        warnings=warnings
    )


