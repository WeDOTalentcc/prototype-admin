"""
Skills Catalog API Endpoints.

Provides comprehensive API for managing company skills catalogs and suggesting
skills for job wizards based on company preferences and learning patterns.

Endpoints:
- GET /company/skills-catalog - Get company's full skills catalog
- POST /company/skills-catalog - Add new skill to company catalog
- POST /company/skills-catalog/sync - Sync skills from tech stack config
- POST /wizard/suggest-skills - Get intelligent skill suggestions
- POST /wizard/record-skill-usage - Record skill usage for learning loop
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.shared.services.skills_catalog_service import (
    get_skills_catalog_db_service,
    get_skills_catalog_service,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/skills-catalog", tags=["skills-catalog"])
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class SkillDetailResponse(BaseModel):
    """Response model for a single skill."""
    name: str
    subcategory: str | None = None
    default_weight: int
    default_level: str
    is_required_default: bool = False
    description: str | None = None
    usage_count: int = 0
    acceptance_rate: float = 0.0
    source: str


class CompetencyDetailResponse(BaseModel):
    """Response model for a behavioral competency."""
    name: str
    description: str | None = None
    default_weight: int
    category: str | None = None
    usage_count: int = 0
    acceptance_rate: float = 0.0
    wsi_questions: list[dict[str, Any]] = Field(default_factory=list)


class CompanyCatalogResponse(BaseModel):
    """Response model for company's full skills catalog."""
    company_id: str
    skills_by_category: dict[str, list[SkillDetailResponse]]
    competencies: list[CompetencyDetailResponse]
    total_skills: int
    total_competencies: int
    static_areas: list[str]


class AddSkillRequest(WeDoBaseModel):
    """Request model for adding a skill to company catalog."""
    skill_name: str
    category: str
    default_weight: int = Field(default=3, ge=1, le=5)
    default_level: str = Field(default="Intermediário")
    description: str | None = None
    subcategory: str | None = None
    is_required_default: bool = False
    
    @validator("skill_name")
    def validate_skill_name(cls, v):
        if not v or not v.strip():
            raise ValueError("skill_name cannot be empty")
        return v.strip()
    
    @validator("category")
    def validate_category(cls, v):
        if not v or not v.strip():
            raise ValueError("category cannot be empty")
        return v.strip()


class AddSkillResponse(BaseModel):
    """Response model when adding a skill."""
    skill_name: str
    category: str
    subcategory: str | None = None
    default_weight: int
    default_level: str
    is_required_default: bool
    created_at: str
    updated_at: str


class SyncTechStackRequest(WeDoBaseModel):
    """Request model for syncing tech stack."""
    tech_stack: list[str] = Field(..., min_items=1)
    
    @validator("tech_stack")
    def validate_tech_stack(cls, v):
        return [tech.strip() for tech in v if tech and tech.strip()]


class SyncTechStackResponse(BaseModel):
    """Response model for tech stack sync operation."""
    added: int
    updated: int
    skipped: int
    total_processed: int


class SuggestSkillsRequest(WeDoBaseModel):
    """Request model for skill suggestions."""
    job_title: str
    seniority: str | None = None
    department: str | None = None
    include_company_catalog: bool = True
    limit: int = Field(default=10, ge=1, le=20)


class SkillSuggestionResponse(BaseModel):
    """Response model for a single skill suggestion."""
    skill: str
    category: str | None = None
    subcategory: str | None = None
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_weight: int | None = None
    suggested_level: str | None = None
    is_typically_required: bool = False
    usage_count: int = 0


class CompetencySuggestionResponse(BaseModel):
    """Response model for a competency suggestion."""
    key: str
    name: str
    subcategories: list[str]
    relevance: str
    source: str


class SuggestSkillsResponse(BaseModel):
    """Response model for skill suggestions."""
    job_title: str
    seniority: str | None = None
    technical_skills: list[SkillSuggestionResponse]
    behavioral_competencies: list[CompetencySuggestionResponse]
    sources_included: dict[str, int]
    total_suggestions: int


class RecordSkillUsageRequest(WeDoBaseModel):
    """Request model for recording skill usage."""
    skill_name: str
    outcome: str = Field(..., description="'accepted', 'modified', or 'rejected'")
    skill_type: str = Field(default="technical", description="'technical' or 'behavioral'")
    job_title: str | None = None
    department: str | None = None
    seniority: str | None = None
    category: str | None = None
    job_vacancy_id: str | None = None
    job_draft_id: str | None = None
    original_weight: int | None = None
    final_weight: int | None = None
    original_level: str | None = None
    final_level: str | None = None
    was_required: bool | None = None
    suggestion_confidence: float | None = None
    suggestion_reasoning: str | None = None
    
    @validator("outcome")
    def validate_outcome(cls, v):
        valid_outcomes = ["accepted", "modified", "rejected"]
        if v not in valid_outcomes:
            raise ValueError(f"outcome must be one of {valid_outcomes}")
        return v
    
    @validator("skill_type")
    def validate_skill_type(cls, v):
        valid_types = ["technical", "behavioral"]
        if v not in valid_types:
            raise ValueError(f"skill_type must be one of {valid_types}")
        return v


class RecordSkillUsageResponse(BaseModel):
    """Response model for skill usage recording."""
    status: str
    message: str
    skill_name: str
    outcome: str


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/company/skills-catalog", response_model=CompanyCatalogResponse)
async def get_company_catalog(
    company_id: str = Query(..., description="Company identifier"),
    include_inactive: bool = Query(False, description="Include inactive skills"),
    category: str | None = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_tenant_db),
    tenant_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
) -> CompanyCatalogResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get the complete company-specific skills catalog.

    Combines company-configured skills from the database with
    the static global catalog.

    Returns all skills organized by category with behavioral competencies.

    Bug fix 2026-05-25 (read/write consistency): the query param may carry
    company_profiles.id while writes (POST /sync) persist rows under
    client_accounts.id. Read uses the resolved JWT-canonical id so the
    catalog is visible right after a sync, otherwise the UI shows empty
    Tech Stack despite a successful save. Also switched to get_tenant_db
    for RLS read consistency.
    """
    try:
        effective_company_id = tenant_company_id
        db_service = get_skills_catalog_db_service(db)

        catalog = await db_service.get_company_catalog(
            company_id=effective_company_id,
            include_inactive=include_inactive,
            category=category
        )
        
        logger.info(
            f"Retrieved catalog for company {company_id}: "
            f"{catalog['total_skills']} skills, {catalog['total_competencies']} competencies"
        )
        
        return CompanyCatalogResponse(**catalog)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving catalog for company {company_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving skills catalog: {str(e)}"
        )


@router.post("/company/skills-catalog", response_model=AddSkillResponse)
async def add_skill_to_catalog(
    request: AddSkillRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)) -> AddSkillResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Add a new skill to the company's catalog.
    
    Creates or updates a skill entry for the company with default properties
    like weight, level, and description. Skills are immediately active.
    """
    try:
        db_service = get_skills_catalog_db_service(db)
        
        result = await db_service.add_skill_to_catalog(
            company_id=company_id,
            skill_name=request.skill_name,
            category=request.category,
            subcategory=request.subcategory,
            default_weight=request.default_weight,
            default_level=request.default_level,
            description=request.description,
            is_required_default=request.is_required_default,
            created_by=str(current_user.id) if current_user.id else None,
        )
        
        logger.info(
            f"Added skill '{request.skill_name}' to company {company_id} catalog"
        )

        # Audit log LGPD/SOX: escrita em catálogo de skills da empresa (Art. 48 LGPD).
        try:
            from app.shared.compliance.audit_service import AuditService as _AS
            import uuid as _uuid
            await _AS().log_action(
                trace_id=str(_uuid.uuid4()),
                company_id=str(company_id),
                action_type="company_tech_stack_update",
                actor=getattr(current_user, "email", None) or getattr(current_user, "id", "unknown"),
                target_id=str(company_id),
                target_type="company_skills_catalog",
                metadata={
                    "source": "rest_post_add_skill",
                    "fields_updated": ["skill_name", "category"],
                    "skill_name": request.skill_name,
                    "category": request.category,
                },
            )
        except Exception as _audit_err:
            logger.error(
                "Audit log failed for company_tech_stack_update company=%s: %s",
                company_id, _audit_err,
            )

        return AddSkillResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding skill to catalog: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding skill: {str(e)}"
        )


@router.post("/company/skills-catalog/sync", response_model=SyncTechStackResponse)
async def sync_tech_stack_to_catalog(
    request: SyncTechStackRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)) -> SyncTechStackResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Sync skills from company's tech stack configuration.
    
    Takes technologies from company config and adds/updates them
    in the company skills catalog. Intelligently categorizes each
    technology based on the static catalog.
    
    Returns statistics on how many were added, updated, or skipped.
    """
    try:
        db_service = get_skills_catalog_db_service(db)
        
        result = await db_service.sync_from_tech_stack(
            company_id=company_id,
            tech_stack=request.tech_stack
        )
        
        logger.info(
            f"Synced tech stack for company {company_id}: "
            f"added={result['added']}, updated={result['updated']}, skipped={result['skipped']}"
        )

        # Audit log LGPD/SOX: sync de tech stack (escrita em massa no catálogo da empresa).
        try:
            from app.shared.compliance.audit_service import AuditService as _AS
            import uuid as _uuid
            await _AS().log_action(
                trace_id=str(_uuid.uuid4()),
                company_id=str(company_id),
                action_type="company_tech_stack_update",
                actor=getattr(current_user, "email", None) or getattr(current_user, "id", "unknown"),
                target_id=str(company_id),
                target_type="company_skills_catalog",
                metadata={
                    "source": "rest_post_sync_tech_stack",
                    "fields_updated": ["tech_stack"],
                    "added": result.get("added", 0),
                    "updated": result.get("updated", 0),
                    "skipped": result.get("skipped", 0),
                    "total_techs": len(request.tech_stack),
                },
            )
        except Exception as _audit_err:
            logger.error(
                "Audit log failed for company_tech_stack_update (sync) company=%s: %s",
                company_id, _audit_err,
            )

        return SyncTechStackResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing tech stack: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing tech stack: {str(e)}"
        )


@router.post("/wizard/suggest-skills", response_model=SuggestSkillsResponse)
async def suggest_skills_for_wizard(
    request: SuggestSkillsRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> SuggestSkillsResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get intelligent skill suggestions for the job wizard.
    
    Returns skill suggestions combining multiple sources:
    1. Learned patterns from SkillSuggestionPattern (highest confidence)
    2. Company-configured skills from CompanySkillsCatalog
    3. Static catalog suggestions based on role and seniority
    
    Also includes behavioral competency suggestions.
    
    Parameters:
    - company_id: Company identifier
    - job_title: Job title for role-based matching
    - seniority: Seniority level (optional, e.g., junior, pleno, senior, lead)
    - department: Department name (optional)
    - include_company_catalog: Whether to include company catalog skills
    - limit: Maximum number of skills to return (1-20)
    """
    try:
        db_service = get_skills_catalog_db_service(db)
        get_skills_catalog_service()
        
        # Get merged suggestions from database
        merged = await db_service.get_merged_suggestions(
            company_id=company_id,
            job_title=request.job_title,
            seniority=request.seniority,
            limit=request.limit
        )
        
        # Transform technical skills to response format
        technical_skills = [
            SkillSuggestionResponse(
                skill=skill.get("skill"),
                category=skill.get("category"),
                subcategory=skill.get("subcategory"),
                source=skill.get("source", "unknown"),
                confidence=skill.get("confidence", 0.5),
                suggested_weight=skill.get("suggested_weight", 3),
                suggested_level=skill.get("suggested_level"),
                is_typically_required=skill.get("is_typically_required", False),
                usage_count=skill.get("usage_count", 0),
            )
            for skill in merged.get("technical_skills", [])
        ]
        
        # Transform behavioral competencies
        behavioral = merged.get("behavioral_competencies", [])
        behavioral_competencies = [
            CompetencySuggestionResponse(
                key=comp.get("key"),
                name=comp.get("name"),
                subcategories=comp.get("subcategories", []),
                relevance=comp.get("relevance", "medium"),
                source=comp.get("source", "static"),
            )
            for comp in behavioral
        ]
        
        logger.info(
            f"Generated suggestions for company {company_id}, "
            f"job: {request.job_title}: {len(technical_skills)} technical skills, "
            f"{len(behavioral_competencies)} competencies"
        )
        
        return SuggestSkillsResponse(
            job_title=request.job_title,
            seniority=request.seniority,
            technical_skills=technical_skills,
            behavioral_competencies=behavioral_competencies,
            sources_included=merged.get("sources_included", {}),
            total_suggestions=merged.get("total_suggestions", 0),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting skills: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating skill suggestions: {str(e)}"
        )


@router.post("/wizard/record-skill-usage", response_model=RecordSkillUsageResponse)
async def record_skill_usage(
    request: RecordSkillUsageRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)) -> RecordSkillUsageResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Record the usage of a skill in the job wizard.
    
    This endpoint captures user actions (accepted, modified, or rejected)
    on skill suggestions, creating a learning loop that improves future
    suggestions for the company.
    
    Usage data is stored in SkillUsageAnalytics and helps the system
    understand which skills are most relevant for different roles.
    
    Parameters:
    - company_id: Company identifier
    - skill_name: Name of the skill
    - outcome: What happened to the skill ('accepted', 'modified', 'rejected')
    - skill_type: Type of skill ('technical' or 'behavioral')
    - job_title: The job title this skill was suggested for
    - department: Department for context
    - seniority: Seniority level for the position
    - category: Skill category
    - job_vacancy_id: Reference to the job vacancy
    - job_draft_id: Reference to the job draft
    - original_weight: Initial weight before modification
    - final_weight: Final weight after modification
    - original_level: Initial level before modification
    - final_level: Final level after modification
    - was_required: Whether the skill was marked as required
    - suggestion_confidence: Confidence score of the original suggestion (0-1)
    - suggestion_reasoning: Explanation for why the skill was suggested
    """
    try:
        db_service = get_skills_catalog_db_service(db)
        
        # Record the skill usage
        await db_service.record_skill_usage(
            company_id=company_id,
            skill_name=request.skill_name,
            outcome=request.outcome,
            skill_type=request.skill_type,
            job_title=request.job_title,
            department=request.department,
            seniority=request.seniority,
            category=request.category,
            job_vacancy_id=request.job_vacancy_id,
            job_draft_id=request.job_draft_id,
            original_weight=request.original_weight,
            final_weight=request.final_weight,
            original_level=request.original_level,
            final_level=request.final_level,
            was_required=request.was_required,
            suggestion_confidence=request.suggestion_confidence,
            suggestion_reasoning=request.suggestion_reasoning,
            source="wizard",
        )
        
        logger.info(
            f"Recorded {request.skill_name} usage for company {company_id}: "
            f"outcome={request.outcome}, job_title={request.job_title}"
        )
        
        return RecordSkillUsageResponse(
            status="success",
            message=f"Skill '{request.skill_name}' usage recorded successfully",
            skill_name=request.skill_name,
            outcome=request.outcome,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording skill usage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error recording skill usage: {str(e)}"
        )


@router.get("/static/suggest", response_model=None)
async def get_static_skill_suggestions(
    job_title: str = Query(..., description="Job title for suggestions"),
    seniority: str | None = Query(None, description="Seniority level"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of skills"),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get skill suggestions from the static catalog only.
    
    This endpoint doesn't use company-specific data, useful for
    quick suggestions before a company has configured their catalog.
    
    Returns technical skills and behavioral competencies based on
    the job title and seniority level provided.
    """
    try:
        service = get_skills_catalog_service()
        
        suggestions = service.suggest_skills(job_title, seniority, limit)
        
        return {
            "job_title": job_title,
            "seniority": seniority,
            "technical_skills": suggestions.get("technical_skills", []),
            "behavioral_competencies": suggestions.get("behavioral_competencies", []),
            "area": suggestions.get("area"),
            "categories": suggestions.get("categories"),
            "recommended_skill_count": suggestions.get("recommended_skill_count"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error getting static suggestions for {job_title}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating suggestions: {str(e)}"
        )


@router.get("/search", response_model=None)
async def search_skills(
    q: str = Query(..., min_length=2, description="Search query"),
    area: str | None = Query(None, description="Filter by area"),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Search for skills in the static catalog.
    
    Searches across all technical and behavioral skills.
    Returns results sorted by relevance.
    
    Parameters:
    - q: Search query (minimum 2 characters)
    - area: Optional area filter (e.g., 'engineering', 'finance', 'hr', 'marketing', 'sales')
    """
    try:
        service = get_skills_catalog_service()
        
        results = service.search_skills(q, area=area)
        
        return {
            "query": q,
            "area_filter": area,
            "technical_matches": len(results.get("technical", [])),
            "behavioral_matches": len(results.get("behavioral", [])),
            "total_matches": len(results.get("technical", [])) + len(results.get("behavioral", [])),
            "results": results,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching skills for query '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching skills: {str(e)}"
        )
