"""
Job Templates API endpoints.

Provides Fast Track template management:
- List and search templates
- Get template details
- Use template for wizard (Fast Track)
- Clone and customize templates
- Template usage analytics
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.job_management.services.job_template_service import (
    WSI_QUALITY_GATES,
    JobTemplateService,
    enrich_template_with_ai,
    validate_wsi_quality,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/job-templates", tags=["Job Templates"])


class TemplateSkill(BaseModel):
    """Technical skill in a template."""
    name: str
    category: str = "technical"
    level: str = "intermediate"
    weight: float = 1.0
    required: bool = True


class TemplateBehavioral(BaseModel):
    """Behavioral competency in a template."""
    name: str
    weight: float = 1.0
    justification: str = ""


class TemplateResponse(BaseModel):
    """Template response model."""
    id: str
    company_id: str | None = None
    category: str
    subcategory: str
    title: str
    title_alternatives: list[str] = []
    seniority: str
    default_description: str | None = None
    default_responsibilities: list[str] = []
    default_requirements: str | None = None
    default_nice_to_have: str | None = None
    default_skills: list[dict] = []
    default_behavioral: list[dict] = []
    salary_range: dict = {}
    work_model: str = "hybrid"
    employment_type: str = "clt"
    is_system: bool = False
    usage_count: int = 0
    popularity_score: float = 0.0


class WizardDataResponse(BaseModel):
    """Wizard-compatible template data for Fast Track."""
    title: str
    department: str
    seniority: str
    description: str | None = None
    responsibilities: list[str] = []
    requirements: str | None = None
    niceToHave: str | None = None
    technicalSkills: list[dict] = []
    behavioralCompetencies: list[dict] = []
    salaryInfo: dict = {}
    workModel: str = "hybrid"
    employmentType: str = "clt"


class CategoryResponse(BaseModel):
    """Template category response."""
    name: str
    display_name: str
    icon: str
    color: str
    subcategories: list[dict] = []
    template_count: int = 0


class CreateTemplateRequest(WeDoBaseModel):
    """Request to create a new template."""
    category: str
    subcategory: str
    title: str
    title_alternatives: list[str] = []
    seniority: str
    default_description: str | None = None
    default_responsibilities: list[str] = []
    default_requirements: str | None = None
    default_nice_to_have: str | None = None
    default_skills: list[dict] = []
    default_behavioral: list[dict] = []
    salary_range_min: int | None = None
    salary_range_max: int | None = None
    work_model: str = "hybrid"
    employment_type: str = "clt"


class CloneTemplateRequest(WeDoBaseModel):
    """Request to clone a template for a company."""
    modifications: dict = {}


class TemplateFeedbackRequest(WeDoBaseModel):
    """Template usage feedback request."""
    job_id: str | None = None
    fields_modified: list[str] = []
    time_to_complete_seconds: int | None = None
    feedback_rating: int | None = Field(None, ge=1, le=5)


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all template categories with metadata."""
    service = JobTemplateService(db)
    categories = service.get_categories()
    stats = await service.get_category_stats()
    
    result = []
    for name, data in categories.items():
        result.append(CategoryResponse(
            name=name,
            display_name=data["display_name"],
            icon=data["icon"],
            color=data["color"],
            subcategories=data["subcategories"],
            template_count=stats.get(name, 0),
        ))
    
    return result


@router.get("/", response_model=list[TemplateResponse])
async def list_templates(
    category: str | None = None,
    subcategory: str | None = None,
    seniority: str | None = None,
    company_id: str | None = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List templates with optional filtering."""
    service = JobTemplateService(db)
    
    templates = await service.get_templates(
        company_id=UUID(company_id) if company_id else None,
        category=category,
        subcategory=subcategory,
        seniority=seniority,
        limit=limit,
        offset=offset,
    )
    
    return [TemplateResponse(**t.to_dict()) for t in templates]


@router.get("/search", response_model=None)
async def search_templates(
    q: str = Query(..., min_length=2),
    company_id: str | None = None,
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Search templates by title."""
    service = JobTemplateService(db)
    
    templates = await service.search_templates(
        query=q,
        company_id=UUID(company_id) if company_id else None,
        limit=limit,
    )
    
    return [TemplateResponse(**t.to_dict()) for t in templates]


@router.get("/popular", response_model=list[TemplateResponse])
async def get_popular_templates(
    category: str | None = None,
    company_id: str | None = None,
    limit: int = Query(10, le=20),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get most popular templates."""
    service = JobTemplateService(db)
    
    templates = await service.get_popular_templates(
        company_id=UUID(company_id) if company_id else None,
        category=category,
        limit=limit,
    )
    
    return [TemplateResponse(**t.to_dict()) for t in templates]


@router.get("/quality-gates", response_model=None)
async def get_quality_gates(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get WSI quality gate requirements."""
    return {
        "requirements": WSI_QUALITY_GATES,
        "description": "Minimum requirements for WSI-compliant job templates",
    }


@router.post("/validate", response_model=None)
async def validate_template_data(
    request: CreateTemplateRequest,
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Validate template data against WSI quality gates.
    
    Returns validation result with warnings if template doesn't meet:
    - Minimum 5 technical skills
    - Minimum 3 behavioral competencies
    - Minimum 5 responsibilities
    """
    template_data = request.model_dump()
    result = validate_wsi_quality(template_data)
    
    return {
        "valid": result["valid"],
        "warnings": result["warnings"],
        "scores": result["scores"],
        "requirements": WSI_QUALITY_GATES,
    }


# ─── Static path BEFORE /{template_id} catch-all ──────────────────────────
# Onda 2.2 fix (2026-05-23): FastAPI evaluates routes in declaration order.
# /{template_id} would match "brazilian-market" first and try UUID() → 500.
# Static paths sob /job-templates devem vir ANTES do catch-all.
@router.get("/brazilian-market", response_model=None)
async def get_brazilian_market_templates(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get all curated Brazilian market templates.

    Returns templates without database lookup - useful for preview/documentation.
    """
    from app.data.loader import get_brazilian_templates as _get_br
    BRAZILIAN_TEMPLATES = _get_br()

    return {
        "success": True,
        "count": len(BRAZILIAN_TEMPLATES),
        "templates": [
            {
                "id": t["id"],
                "title": t["title"],
                "department": t.get("department"),
                "seniority": t.get("seniority"),
                "location": t.get("location"),
                "work_model": t.get("work_model"),
                "skills_count": len(t.get("technical_skills", [])),
                "behavioral_count": len(t.get("behavioral_competencies", [])),
                "wsi_questions_count": len(t.get("wsi_questions", [])),
                "salary_range": f"R$ {t.get('salary_min', 0)//1000}k - {t.get('salary_max', 0)//1000}k"
            }
            for t in BRAZILIAN_TEMPLATES
        ]
    }


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get a specific template by ID."""
    service = JobTemplateService(db)
    
    template = await service.get_template_by_id(UUID(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateResponse(**template.to_dict())


@router.post("/{template_id}/use", response_model=WizardDataResponse)
async def use_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(...),
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Use a template for Fast Track job creation.
    
    Returns wizard-compatible data that can be directly applied to the job creation form.
    """
    service = JobTemplateService(db)
    
    try:
        wizard_data = await service.use_template(
            template_id=UUID(template_id),
            company_id=UUID(company_id),
            user_id=UUID(user_id) if user_id else None,
        )
        return WizardDataResponse(**wizard_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{template_id}/clone", response_model=TemplateResponse)
async def clone_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: CloneTemplateRequest,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Clone a template for a company with optional modifications."""
    service = JobTemplateService(db)
    
    try:
        template = await service.clone_template_for_company(
            template_id=UUID(template_id),
            company_id=UUID(company_id),
            modifications=request.modifications,
        )
        return TemplateResponse(**template.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{template_id}/feedback", response_model=None)
async def submit_feedback(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: TemplateFeedbackRequest,
    company_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Submit usage feedback for a template."""
    service = JobTemplateService(db)
    
    await service.log_template_feedback(
        template_id=UUID(template_id),
        company_id=UUID(company_id),
        job_id=UUID(request.job_id) if request.job_id else None,
        fields_modified=request.fields_modified,
        time_to_complete=request.time_to_complete_seconds,
        feedback_rating=request.feedback_rating,
    )
    
    return {"status": "success", "message": "Feedback recorded"}


@router.post("/", response_model=TemplateResponse)
async def create_template(
    request: CreateTemplateRequest,
    company_id: str = Query(...),
    enrich_with_ai: bool = Query(False, description="Use AI to enrich missing fields"),
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new company-specific template."""
    service = JobTemplateService(db)
    
    template_data = request.model_dump()
    template_data["company_id"] = UUID(company_id)
    template_data["is_system"] = False
    
    if enrich_with_ai:
        template_data = await enrich_template_with_ai(template_data)
    
    template = await service.create_template(template_data)
    return TemplateResponse(**template.to_dict())


@router.post("/seed", response_model=None)
async def seed_templates(
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Seed database with system templates (admin only)."""
    service = JobTemplateService(db)
    count = await service.seed_system_templates()
    
    return {
        "status": "success",
        "templates_created": count,
        "message": f"Created {count} system templates",
    }


@router.post("/seed/brazilian-market", response_model=None)
async def seed_brazilian_market_templates(
    company_id: str = Query(...),
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Seed database with curated Brazilian market templates.
    
    Creates templates for common roles in Brazil:
    - Technology (Dev Full Stack, Backend Senior, DevOps, Data Science)
    - Product (PM, UX/UI Designer)
    - Marketing (Analista de Marketing Digital)
    - HR (People Analytics)
    - Sales (Executivo de Vendas B2B, Customer Success)
    """
    from app.data.loader import get_brazilian_templates as _get_br; BRAZILIAN_TEMPLATES = _get_br()
    from app.domains.job_management.services.job_embedding_service import job_embedding_service
    
    created = []
    
    for template in BRAZILIAN_TEMPLATES:
        try:
            result = await job_embedding_service.create_or_update_job_embedding(
                company_id=company_id,
                job_id=template["id"],
                job_title=template["title"],
                department=template.get("department"),
                seniority=template.get("seniority"),
                location=template.get("location"),
                work_model=template.get("work_model"),
                skills=template.get("technical_skills", []),
                behavioral=[c.get("name", c) if isinstance(c, dict) else c for c in template.get("behavioral_competencies", [])],
                description=template.get("description"),
                outcome_status=template.get("outcome_status"),
                time_to_fill_days=template.get("time_to_fill_days"),
                is_template=True
            )
            
            if result.get("success"):
                created.append({
                    "id": template["id"],
                    "title": template["title"],
                    "department": template.get("department")
                })
                
        except Exception as e:
            import logging
            logging.error(f"Error creating template {template['title']}: {e}")
    
    return {
        "status": "success",
        "templates_created": len(created),
        "templates": created,
        "message": f"Created {len(created)} Brazilian market templates for Fast Track"
    }


# Note: GET /brazilian-market handler moved above @router.get("/{template_id}")
# to avoid FastAPI route ordering collision (Onda 2.2 fix 2026-05-23).


@router.post("/import/esco", response_model=None)
async def import_from_esco(
    category: str = Query(...),
    subcategory: str = Query("geral"),
    search_terms: str = Query(..., description="Comma-separated search terms"),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Import templates from ESCO database.
    
    Searches ESCO occupations and creates templates with skills and competencies.
    """
    from app.domains.job_management.services.template_importer_service import TemplateImporterService
    
    importer = TemplateImporterService(db)
    try:
        terms = [t.strip() for t in search_terms.split(",")]
        templates = await importer.import_from_esco(
            category=category,
            subcategory=subcategory,
            search_terms=terms
        )
        
        return {
            "status": "success",
            "templates_created": len(templates),
            "templates": [{"id": str(t.id), "title": t.title} for t in templates]
        }
    finally:
        await importer.close()


@router.get("/import/status", response_model=None)
async def get_import_status(
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get current template import status and progress toward 480 goal."""
    from app.domains.job_management.services.template_importer_service import TemplateImporterService
    
    importer = TemplateImporterService(db)
    try:
        return await importer.get_import_status()
    finally:
        await importer.close()


@router.get("/learning/stats", response_model=None)
async def get_learning_stats(
    company_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get learning statistics for a company."""
    from app.domains.job_management.services.template_learning_service import TemplateLearningService
    
    learning = TemplateLearningService(db)
    return await learning.get_learning_stats(UUID(company_id))


@router.get("/learning/suggestions", response_model=None)
async def get_learning_suggestions(
    company_id: str = Query(...),
    limit: int = Query(5, le=10),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get suggestions for jobs that could benefit from templates."""
    from app.domains.job_management.services.template_learning_service import TemplateLearningService
    
    learning = TemplateLearningService(db)
    return await learning.suggest_templates_for_improvement(UUID(company_id), limit)


class LearnFromJobRequest(WeDoBaseModel):
    """Request to learn from a job creation."""
    title: str
    department: str | None = None
    seniority: str | None = None
    description: str | None = None
    responsibilities: list[str] | None = []
    requirements: str | None = None
    tech_skills: list[dict] | None = []
    behavioral_skills: list[dict] | None = []
    salary_min: int | None = None
    salary_max: int | None = None
    work_model: str | None = "hybrid"
    template_used: str | None = None


@router.post("/learning/learn-from-job", response_model=None)
async def learn_from_job_creation(
    request: LearnFromJobRequest,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Learn from a completed job creation.
    
    This endpoint should be called after a job is successfully created.
    It analyzes the job data and may create a new company-specific template
    if similar jobs have been created before.
    """
    from app.domains.job_management.services.template_learning_service import TemplateLearningService
    
    learning = TemplateLearningService(db)
    
    job_data = request.model_dump()
    template_used = UUID(request.template_used) if request.template_used else None
    
    new_template = await learning.learn_from_job_creation(
        company_id=UUID(company_id),
        job_data=job_data,
        template_used=template_used
    )
    
    if new_template:
        return {
            "learned": True,
            "template_created": True,
            "template_id": str(new_template.id),
            "template_title": new_template.title,
            "message": "New template created from job patterns"
        }
    else:
        return {
            "learned": True,
            "template_created": False,
            "message": "Job recorded for future learning (need 3+ similar jobs to create template)"
        }

reorder_collection_before_item(router)
