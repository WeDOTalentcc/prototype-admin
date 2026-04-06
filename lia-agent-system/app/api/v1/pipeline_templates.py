"""
Pipeline Templates API endpoints.
Manages reusable recruitment process stage templates for job creation.
"""
from uuid import UUID
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.models.pipeline_template import DEFAULT_PIPELINE_TEMPLATES, PipelineTemplate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company/pipeline-templates", tags=["pipeline-templates"])


class PipelineStage(BaseModel):
    name: str
    order: int
    type: str = "manual"
    sla_days: int = 3
    instructions: str | None = None


class PipelineTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    stages: list[PipelineStage]
    is_default: bool = False


class PipelineTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    stages: list[PipelineStage] | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class PipelineTemplateResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: str | None = None
    stages: list[dict[str, Any]]
    is_default: bool
    is_active: bool
    usage_count: int
    created_by: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PipelineTemplateListResponse(BaseModel):
    items: list[PipelineTemplateResponse]
    total: int
    page: int
    size: int


@router.get("/", response_model=PipelineTemplateListResponse)
async def list_pipeline_templates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    List all pipeline templates for the company.
    """
    company_id = current_user.company_id
    
    query = select(PipelineTemplate).where(
        PipelineTemplate.company_id == company_id
    )
    
    if is_active is not None:
        query = query.where(PipelineTemplate.is_active == is_active)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                PipelineTemplate.name.ilike(search_pattern),
                PipelineTemplate.description.ilike(search_pattern)
            )
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(PipelineTemplate.is_default.desc(), PipelineTemplate.usage_count.desc(), PipelineTemplate.name)
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    items = [
        PipelineTemplateResponse(
            id=str(t.id),
            company_id=t.company_id,
            name=t.name,
            description=t.description,
            stages=t.stages or [],
            is_default=t.is_default,
            is_active=t.is_active,
            usage_count=t.usage_count or 0,
            created_by=t.created_by,
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else ""
        )
        for t in templates
    ]
    
    return PipelineTemplateListResponse(
        items=items,
        total=total,
        page=page,
        size=size
    )


@router.post("/", response_model=PipelineTemplateResponse)
async def create_pipeline_template(
    data: PipelineTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Create a new pipeline template.
    """
    company_id = current_user.company_id
    user_email = current_user.email or "demo@example.com"
    
    if data.is_default:
        existing_default = await db.execute(
            select(PipelineTemplate).where(
                PipelineTemplate.company_id == company_id,
                PipelineTemplate.is_default == True
            )
        )
        for t in existing_default.scalars():
            t.is_default = False
    
    template = PipelineTemplate(
        id=uuid.uuid4(),
        company_id=company_id,
        name=data.name,
        description=data.description,
        stages=[s.model_dump() for s in data.stages],
        is_default=data.is_default,
        is_active=True,
        usage_count=0,
        created_by=user_email,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(template)
    await db.flush()
    
    logger.info(f"Created pipeline template: {template.name} for company {company_id}")
    
    return PipelineTemplateResponse(
        id=str(template.id),
        company_id=template.company_id,
        name=template.name,
        description=template.description,
        stages=template.stages or [],
        is_default=template.is_default,
        is_active=template.is_active,
        usage_count=template.usage_count or 0,
        created_by=template.created_by,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else ""
    )


@router.get("/{template_id}", response_model=PipelineTemplateResponse)
async def get_pipeline_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get a specific pipeline template by ID.
    """
    company_id = current_user.company_id
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    result = await db.execute(
        select(PipelineTemplate).where(
            PipelineTemplate.id == template_uuid,
            PipelineTemplate.company_id == company_id
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    
    return PipelineTemplateResponse(
        id=str(template.id),
        company_id=template.company_id,
        name=template.name,
        description=template.description,
        stages=template.stages or [],
        is_default=template.is_default,
        is_active=template.is_active,
        usage_count=template.usage_count or 0,
        created_by=template.created_by,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else ""
    )


@router.put("/{template_id}", response_model=PipelineTemplateResponse)
async def update_pipeline_template(
    template_id: str,
    data: PipelineTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Update a pipeline template.
    """
    company_id = current_user.company_id
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    result = await db.execute(
        select(PipelineTemplate).where(
            PipelineTemplate.id == template_uuid,
            PipelineTemplate.company_id == company_id
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    
    if data.is_default and not template.is_default:
        existing_default = await db.execute(
            select(PipelineTemplate).where(
                PipelineTemplate.company_id == company_id,
                PipelineTemplate.is_default == True,
                PipelineTemplate.id != template_uuid
            )
        )
        for t in existing_default.scalars():
            t.is_default = False
    
    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.stages is not None:
        template.stages = [s.model_dump() for s in data.stages]
    if data.is_default is not None:
        template.is_default = data.is_default
    if data.is_active is not None:
        template.is_active = data.is_active
    
    template.updated_at = datetime.utcnow()
    
    await db.flush()
    
    logger.info(f"Updated pipeline template: {template.name}")
    
    return PipelineTemplateResponse(
        id=str(template.id),
        company_id=template.company_id,
        name=template.name,
        description=template.description,
        stages=template.stages or [],
        is_default=template.is_default,
        is_active=template.is_active,
        usage_count=template.usage_count or 0,
        created_by=template.created_by,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else ""
    )


@router.delete("/{template_id}", response_model=None)
async def delete_pipeline_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Delete (soft delete) a pipeline template.
    """
    company_id = current_user.company_id
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    result = await db.execute(
        select(PipelineTemplate).where(
            PipelineTemplate.id == template_uuid,
            PipelineTemplate.company_id == company_id
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    
    template.is_active = False
    template.updated_at = datetime.utcnow()
    
    await db.flush()
    
    logger.info(f"Deleted pipeline template: {template.name}")
    
    return {"success": True, "message": "Template deleted successfully"}


@router.post("/{template_id}/clone", response_model=PipelineTemplateResponse)
async def clone_pipeline_template(
    template_id: str,
    new_name: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Clone an existing pipeline template.
    """
    company_id = current_user.company_id
    user_email = current_user.email or "demo@example.com"
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    result = await db.execute(
        select(PipelineTemplate).where(
            PipelineTemplate.id == template_uuid,
            PipelineTemplate.company_id == company_id
        )
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    
    cloned = PipelineTemplate(
        id=uuid.uuid4(),
        company_id=company_id,
        name=new_name or f"{original.name} (Cópia)",
        description=original.description,
        stages=original.stages.copy() if original.stages else [],
        is_default=False,
        is_active=True,
        usage_count=0,
        created_by=user_email,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(cloned)
    await db.flush()
    
    logger.info(f"Cloned pipeline template: {original.name} -> {cloned.name}")
    
    return PipelineTemplateResponse(
        id=str(cloned.id),
        company_id=cloned.company_id,
        name=cloned.name,
        description=cloned.description,
        stages=cloned.stages or [],
        is_default=cloned.is_default,
        is_active=cloned.is_active,
        usage_count=cloned.usage_count or 0,
        created_by=cloned.created_by,
        created_at=cloned.created_at.isoformat() if cloned.created_at else "",
        updated_at=cloned.updated_at.isoformat() if cloned.updated_at else ""
    )


@router.post("/seed-defaults", response_model=None)
async def seed_default_templates(
    force: bool = Query(False, description="Force re-seeding even if templates exist"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Seed default pipeline templates for the company.
    Creates standard templates if they don't exist.
    """
    company_id = current_user.company_id
    user_email = current_user.email or "demo@example.com"
    
    existing = await db.execute(
        select(func.count()).select_from(PipelineTemplate).where(
            PipelineTemplate.company_id == company_id,
            PipelineTemplate.is_active == True
        )
    )
    count = existing.scalar() or 0
    
    if count > 0 and not force:
        return {
            "success": True,
            "message": f"Company already has {count} templates. Use force=true to re-seed.",
            "seeded": 0
        }
    
    seeded_count = 0
    
    for template_data in DEFAULT_PIPELINE_TEMPLATES:
        existing_template = await db.execute(
            select(PipelineTemplate).where(
                PipelineTemplate.company_id == company_id,
                PipelineTemplate.name == template_data["name"]
            )
        )
        if existing_template.scalar_one_or_none():
            continue
        
        template = PipelineTemplate(
            id=uuid.uuid4(),
            company_id=company_id,
            name=template_data["name"],
            description=template_data["description"],
            stages=template_data["stages"],
            is_default=template_data["is_default"],
            is_active=True,
            usage_count=0,
            created_by=user_email,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(template)
        seeded_count += 1
    
    await db.flush()
    
    logger.info(f"Seeded {seeded_count} default pipeline templates for company {company_id}")
    
    return {
        "success": True,
        "message": f"Seeded {seeded_count} default templates",
        "seeded": seeded_count
    }


@router.post("/{template_id}/increment-usage", response_model=None)
async def increment_template_usage(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Increment the usage count of a template (called when applied to a job).
    """
    company_id = current_user.company_id
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    result = await db.execute(
        select(PipelineTemplate).where(
            PipelineTemplate.id == template_uuid,
            PipelineTemplate.company_id == company_id
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Pipeline template not found")
    
    template.usage_count = (template.usage_count or 0) + 1
    template.updated_at = datetime.utcnow()
    
    await db.flush()
    
    return {"success": True, "usage_count": template.usage_count}
