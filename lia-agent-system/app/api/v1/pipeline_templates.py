"""
Pipeline Templates API endpoints.
Manages reusable recruitment process stage templates for job creation.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Literal
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company/pipeline-templates", tags=["pipeline-templates"])


class PipelineStage(WeDoBaseModel):
    name: str
    order: int
    type: Literal["automatic", "manual", "hybrid"] = "manual"
    sla_days: int = 3
    instructions: str | None = None

    @field_validator("order")
    @classmethod
    def _order_min_1(cls, v: int) -> int:
        if v < 1:
            raise ValueError("order must be >= 1")
        return v

    @field_validator("sla_days")
    @classmethod
    def _sla_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("sla_days must be >= 0")
        return v


class PipelineTemplateCreate(WeDoBaseModel):
    name: str
    description: str | None = None
    stages: list[PipelineStage]
    is_default: bool = False
    # Auto-suggest hints (migration 208 — Sprint Pipeline Templates 2026-05-26)
    department_hint: list[str] | None = None
    seniority_hint: list[str] | None = None
    job_family_hint: list[str] | None = None


class PipelineTemplateUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    stages: list[PipelineStage] | None = None
    is_default: bool | None = None
    is_active: bool | None = None
    is_archived: bool | None = None
    department_hint: list[str] | None = None
    seniority_hint: list[str] | None = None
    job_family_hint: list[str] | None = None


class PipelineTemplateResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: str | None = None
    stages: list[dict[str, Any]]
    is_default: bool
    is_active: bool
    is_archived: bool = False
    usage_count: int
    department_hint: list[str] | None = None
    seniority_hint: list[str] | None = None
    job_family_hint: list[str] | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PipelineTemplateListResponse(BaseModel):
    items: list[PipelineTemplateResponse]
    total: int
    page: int
    size: int


def _to_response(t) -> PipelineTemplateResponse:
    return PipelineTemplateResponse(
        id=str(t.id),
        company_id=t.company_id,
        name=t.name,
        description=t.description,
        stages=t.stages or [],
        is_archived=bool(getattr(t, "is_archived", False)),
        department_hint=getattr(t, "department_hint", None),
        seniority_hint=getattr(t, "seniority_hint", None),
        job_family_hint=getattr(t, "job_family_hint", None),
        updated_by=getattr(t, "updated_by", None),
        is_default=t.is_default,
        is_active=t.is_active,
        usage_count=t.usage_count or 0,
        created_by=t.created_by,
        created_at=t.created_at.isoformat() if t.created_at else "",
        updated_at=t.updated_at.isoformat() if t.updated_at else "",
    )


@router.get("/", response_model=PipelineTemplateListResponse)
async def list_pipeline_templates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all pipeline templates for the company."""
    repo = PipelineTemplateRepository(db)
    templates, total = await repo.list_for_company(
        current_user.company_id,
        is_active=is_active,
        search=search,
        page=page,
        size=size,
    )
    return PipelineTemplateListResponse(
        items=[_to_response(t) for t in templates],
        total=total,
        page=page,
        size=size,
    )


@router.post("/", response_model=PipelineTemplateResponse)
async def create_pipeline_template(
    data: PipelineTemplateCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new pipeline template."""
    repo = PipelineTemplateRepository(db)
    company_id = current_user.company_id
    user_email = current_user.email or "demo@example.com"

    if data.is_default:
        await repo.clear_default(company_id)

    template = await repo.create(
        company_id,
        {
            "name": data.name,
            "description": data.description,
            "stages": [s.model_dump() for s in data.stages],
            "is_default": data.is_default,
        },
        created_by=user_email,
    )

    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Created pipeline template: {template.name} for company {company_id}")
    return _to_response(template)


@router.get("/{template_id}", response_model=PipelineTemplateResponse)
async def get_pipeline_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific pipeline template by ID."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    repo = PipelineTemplateRepository(db)
    template = await repo.get_by_id(template_uuid, current_user.company_id)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    return _to_response(template)


@router.put("/{template_id}", response_model=PipelineTemplateResponse)
async def update_pipeline_template(
    template_id: str,
    data: PipelineTemplateUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a pipeline template."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    repo = PipelineTemplateRepository(db)
    company_id = current_user.company_id
    template = await repo.get_by_id(template_uuid, company_id)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")

    if data.is_default and not template.is_default:
        await repo.clear_default(company_id, exclude_id=template_uuid)

    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.description is not None:
        update_data["description"] = data.description
    if data.stages is not None:
        update_data["stages"] = [s.model_dump() for s in data.stages]
    if data.is_default is not None:
        update_data["is_default"] = data.is_default
    if data.is_active is not None:
        update_data["is_active"] = data.is_active

    template = await repo.update(template, update_data)
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Updated pipeline template: {template.name}")
    return _to_response(template)


@router.delete("/{template_id}", response_model=None)
async def delete_pipeline_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete (soft delete) a pipeline template."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    repo = PipelineTemplateRepository(db)
    template = await repo.get_by_id(template_uuid, current_user.company_id)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")

    await repo.soft_delete(template)
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Deleted pipeline template: {template.name}")
    return {"success": True, "message": "Template deleted successfully"}


@router.post("/{template_id}/clone", response_model=PipelineTemplateResponse)
async def clone_pipeline_template(
    template_id: str,
    new_name: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Clone an existing pipeline template."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    repo = PipelineTemplateRepository(db)
    original = await repo.get_by_id(template_uuid, current_user.company_id)
    if not original:
        raise HTTPException(status_code=404, detail="Pipeline template not found")

    user_email = current_user.email or "demo@example.com"
    cloned = await repo.clone(
        original,
        new_name or f"{original.name} (Cópia)",
        created_by=user_email,
    )
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Cloned pipeline template: {original.name} -> {cloned.name}")
    return _to_response(cloned)


@router.post("/seed-defaults", response_model=None)
async def seed_default_templates(
    force: bool = Query(False, description="Force re-seeding even if templates exist"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Seed default pipeline templates for the company."""
    company_id = current_user.company_id
    user_email = current_user.email or "demo@example.com"
    repo = PipelineTemplateRepository(db)

    count = await repo.count_active(company_id)
    if count > 0 and not force:
        return {
            "success": True,
            "message": f"Company already has {count} templates. Use force=true to re-seed.",
            "seeded": 0,
        }

    seeded = await repo.seed_defaults(company_id, created_by=user_email)
    logger.info(f"Seeded {seeded} default pipeline templates for company {company_id}")
    return {"success": True, "message": f"Seeded {seeded} default templates", "seeded": seeded}


@router.post("/{template_id}/increment-usage", response_model=None)
async def increment_template_usage(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Increment the usage count of a template (called when applied to a job)."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    repo = PipelineTemplateRepository(db)
    template = await repo.get_by_id(template_uuid, current_user.company_id)
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")

    template = await repo.increment_usage(template)
    return {"success": True, "usage_count": template.usage_count}
