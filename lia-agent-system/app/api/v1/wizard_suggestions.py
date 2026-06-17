"""
Wizard Suggestions API - Learning Loop-powered intelligent suggestions.

Provides field suggestions for the Job Wizard based on the 6-tier priority system:
1. Company Settings (100%) - Configured in company settings
2. LIA History (95%) - Previous jobs created in LIA
3. Imported ATS (85%) - JDs imported from external ATS
4. Workforce Planning (80%) - HRIS/WFP data
5. ETL/Datalakes (75%) - External data sources
6. Curated Templates (70%) - 662 validated templates
"""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.domains.job_management.services.wizard_data_priority_service import (
    JobContext,
    wizard_data_priority_service,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.errors import LIAError

router = APIRouter()
logger = logging.getLogger(__name__)

def parse_company_id(company_id: str) -> UUID:
    """Convert company_id string to UUID."""
    if not company_id:
        raise ValueError("company_id is required")
    try:
        return UUID(company_id)
    except ValueError:
        raise ValueError(f"Invalid company_id: '{company_id}'. A valid UUID is required.")


class SuggestionResponse(BaseModel):
    value: Any
    source: str
    confidence: float
    explanation: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class FieldSuggestionsResponse(BaseModel):
    field: str
    best_suggestion: SuggestionResponse | None = None
    all_suggestions: list[SuggestionResponse] = Field(default_factory=list)


class WizardContextRequest(WeDoBaseModel):
    job_title: str | None = None
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None


class AllFieldSuggestionsResponse(BaseModel):
    suggestions: dict[str, SuggestionResponse] = Field(default_factory=dict)
    data_coverage: dict[str, Any] = Field(default_factory=dict)
    fields_with_suggestions: list[str] = Field(default_factory=list)
    fields_without_suggestions: list[str] = Field(default_factory=list)


class SimilarJobResponse(BaseModel):
    id: str
    source: str
    title: str
    department: str | None = None
    seniority: str | None = None
    was_successful: bool | None = None
    time_to_fill: int | None = None
    created_at: str | None = None
    can_use_as_template: bool = True


@router.get("/suggestion/{field}", response_model=None)
async def get_field_suggestion(
    field: str,
    job_title: str | None = Query(None, description="Job title for context"),
    department: str | None = Query(None, description="Department"),
    seniority: str | None = Query(None, description="Seniority level"),
    location: str | None = Query(None, description="Location"),
    work_model: str | None = Query(None, description="Work model (remote, hybrid, onsite)"),
    include_all_sources: bool = Query(False, description="Return suggestions from all sources"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> FieldSuggestionsResponse:
    """
    Get a suggestion for a specific wizard field.
    
    Uses the Learning Loop priority system to return the best suggestion
    based on data availability and confidence levels.
    
    Fields supported:
    - job_title: Normalized job title suggestions
    - department: Department suggestions from company settings
    - seniority: Seniority level suggestions
    - salary_range: Salary range based on historical data
    - technical_skills: Technical skills based on role
    - behavioral_competencies: Behavioral competencies
    - responsibilities: Job responsibilities
    - benefits: Benefits package
    """
    company_id = get_user_company_id(current_user)
    
    try:
        context = JobContext(
            company_id=parse_company_id(company_id),
            job_title=job_title,
            department=department,
            seniority=seniority,
            location=location,
            work_model=work_model,
            recruiter_id=str(current_user.id) if current_user.id else None,
        )
        
        best_suggestion = await wizard_data_priority_service.get_suggestion(db, field, context)
        
        all_suggestions = []
        if include_all_sources:
            all_suggestions_raw = await wizard_data_priority_service.get_all_suggestions(db, field, context)
            all_suggestions = [
                SuggestionResponse(
                    value=s.value,
                    source=s.source.value,
                    confidence=s.confidence,
                    explanation=s.explanation,
                    metadata=s.metadata,
                )
                for s in all_suggestions_raw
            ]
        
        return FieldSuggestionsResponse(
            field=field,
            best_suggestion=SuggestionResponse(
                value=best_suggestion.value,
                source=best_suggestion.source.value,
                confidence=best_suggestion.confidence,
                explanation=best_suggestion.explanation,
                metadata=best_suggestion.metadata,
            ) if best_suggestion else None,
            all_suggestions=all_suggestions,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestion for field {field}: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/suggestions/all", response_model=None)
async def get_all_field_suggestions(
    request: WizardContextRequest,
    fields: list[str] | None = Query(
        None, 
        description="Fields to get suggestions for (defaults to all)"
    ),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> AllFieldSuggestionsResponse:
    """
    Get suggestions for multiple wizard fields at once.
    
    More efficient than calling individual field endpoints.
    Returns data coverage statistics and which fields have suggestions.
    """
    company_id = get_user_company_id(current_user)
    
    try:
        context = JobContext(
            company_id=parse_company_id(company_id),
            job_title=request.job_title,
            department=request.department,
            seniority=request.seniority,
            location=request.location,
            work_model=request.work_model,
            employment_type=request.employment_type,
            recruiter_id=str(current_user.id) if current_user.id else None,
        )
        
        all_fields = fields or [
            "job_title", "department", "seniority", "salary_range",
            "technical_skills", "behavioral_competencies", 
            "responsibilities", "benefits"
        ]
        
        suggestions_dict = await wizard_data_priority_service.get_field_suggestions(
            db, context, all_fields
        )
        
        coverage = await wizard_data_priority_service.get_data_coverage(
            db, context.company_id
        )
        
        response_suggestions = {}
        fields_with = []
        fields_without = []
        
        for field in all_fields:
            if field in suggestions_dict:
                s = suggestions_dict[field]
                response_suggestions[field] = SuggestionResponse(
                    value=s.value,
                    source=s.source.value,
                    confidence=s.confidence,
                    explanation=s.explanation,
                    metadata=s.metadata,
                )
                fields_with.append(field)
            else:
                fields_without.append(field)
        
        return AllFieldSuggestionsResponse(
            suggestions=response_suggestions,
            data_coverage=coverage,
            fields_with_suggestions=fields_with,
            fields_without_suggestions=fields_without,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all suggestions: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/similar-jobs", response_model=None)
async def get_similar_jobs(
    job_title: str | None = Query(None, description="Job title to match"),
    department: str | None = Query(None, description="Department filter"),
    seniority: str | None = Query(None, description="Seniority filter"),
    limit: int = Query(5, le=20, description="Max results"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> list[SimilarJobResponse]:
    """
    Find similar jobs for Fast Track mode.
    
    Returns previous jobs that can be used as templates,
    sorted by relevance to the provided context.
    """
    company_id = get_user_company_id(current_user)
    
    try:
        context = JobContext(
            company_id=parse_company_id(company_id),
            job_title=job_title,
            department=department,
            seniority=seniority,
        )
        
        similar = await wizard_data_priority_service.get_similar_jobs(db, context, limit)
        
        return [
            SimilarJobResponse(**job)
            for job in similar
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting similar jobs: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/data-coverage", response_model=None)
async def get_data_coverage(
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    """
    Get data coverage statistics for the Learning Loop.
    
    Shows which data sources are available and coverage percentage.
    Helps users understand what actions will improve suggestions.
    """
    company_id = get_user_company_id(current_user)
    
    try:
        coverage = await wizard_data_priority_service.get_data_coverage(
            db, 
            parse_company_id(company_id)
        )
        
        coverage["sources"] = {
            "company_settings": {
                "name": "Configurações da Empresa",
                "precision": "100%",
                "description": "Dados cadastrados no menu Configurações"
            },
            "lia_history": {
                "name": "Histórico LIA",
                "precision": "95%",
                "description": "Vagas criadas anteriormente na plataforma"
            },
            "imported_ats": {
                "name": "ATS Importado",
                "precision": "85%",
                "description": "JDs importados de sistemas externos"
            },
            "workforce_planning": {
                "name": "Planejamento",
                "precision": "80%",
                "description": "Dados de Workforce Planning"
            },
            "curated_templates": {
                "name": "Templates",
                "precision": "70%",
                "description": "662 templates validados"
            },
        }
        
        return coverage
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data coverage: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/sources-priority", response_model=None)
async def get_sources_priority(company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get information about the data sources priority system.
    
    Returns the priority order and confidence levels for each source.
    """
    return {
        "priority_order": [
            {
                "order": 1,
                "source": "company_settings",
                "name": "Configurações da Empresa",
                "confidence": 1.0,
                "description": "Dados cadastrados pelo cliente no menu Configurações"
            },
            {
                "order": 2,
                "source": "lia_history",
                "name": "Histórico LIA",
                "confidence": 0.95,
                "description": "Padrões de vagas criadas anteriormente na plataforma"
            },
            {
                "order": 3,
                "source": "imported_ats",
                "name": "ATS Importado",
                "confidence": 0.85,
                "description": "JDs importados do ATS do cliente (Gupy, Pandapé, etc.)"
            },
            {
                "order": 4,
                "source": "workforce_planning",
                "name": "Workforce Planning",
                "confidence": 0.80,
                "description": "Dados de planejamento de headcount e HRIS"
            },
            {
                "order": 5,
                "source": "etl_datalakes",
                "name": "ETL/Datalakes",
                "confidence": 0.75,
                "description": "Dados de fontes externas via ETL"
            },
            {
                "order": 6,
                "source": "curated_templates",
                "name": "Templates Curados",
                "confidence": 0.70,
                "description": "662 templates validados por especialistas"
            },
        ],
        "minimum_confidence": 0.70,
        "llm_fallback_confidence": 0.60,
    }
