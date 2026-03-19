"""
Admin Templates API endpoints for managing system email templates.
Admin-only endpoints for creating and managing templates that can be published to companies.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, cast
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime
import uuid as uuid_module
from pydantic import BaseModel, Field

from app.models.email_template import EmailTemplate
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
    EmailTemplateListResponse,
)
from app.core.database import get_db
from app.auth.dependencies import require_admin
from app.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/templates", tags=["admin-templates"])


class SystemTemplateCreate(BaseModel):
    """Schema for creating a system template."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    subject: Optional[str] = Field(None, max_length=500, description="Email subject line")
    body_html: str = Field(..., min_length=1, description="HTML body content")
    body_text: Optional[str] = Field(None, description="Plain text body")
    category: Optional[str] = Field(None, max_length=50, description="Template category")
    channel: str = Field(default="email", description="Communication channel: email or whatsapp")
    situation: Optional[str] = Field(None, max_length=50, description="Situation/context")
    variables: List[str] = Field(default_factory=list, description="Template variables")


class SystemTemplateUpdate(BaseModel):
    """Schema for updating a system template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    body_html: Optional[str] = Field(None, min_length=1)
    body_text: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    channel: Optional[str] = Field(None, max_length=20)
    situation: Optional[str] = Field(None, max_length=50)
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SystemTemplateResponse(EmailTemplateResponse):
    """System template response with additional fields."""
    is_system_template: bool = True
    version: int = 1


class SystemTemplateListResponse(BaseModel):
    """Response for listing system templates."""
    total: int
    items: List[SystemTemplateResponse]


class PublishResult(BaseModel):
    """Result of publishing a template to companies."""
    success: bool
    message: str
    companies_count: int
    template_id: str


def template_to_response(template: EmailTemplate) -> SystemTemplateResponse:
    """Convert EmailTemplate model to SystemTemplateResponse."""
    return SystemTemplateResponse(
        id=cast(uuid_module.UUID, template.id),
        name=cast(str, template.name),
        subject=cast(Optional[str], template.subject),
        body_html=cast(str, template.body_html),
        body_text=cast(Optional[str], template.body_text),
        category=cast(Optional[str], template.category),
        channel=cast(str, template.channel) if template.channel else "email",
        situation=cast(Optional[str], template.situation),
        variables=cast(List[str], template.variables) if template.variables else [],
        is_active=cast(bool, template.is_active),
        is_system_template=cast(bool, template.is_system_template),
        version=cast(int, template.version) if template.version else 1,
        created_by=cast(Optional[str], template.created_by),
        created_at=cast(datetime, template.created_at),
        updated_at=cast(datetime, template.updated_at) if template.updated_at else cast(datetime, template.created_at)
    )


@router.get("", response_model=SystemTemplateListResponse)
async def list_system_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    channel: Optional[str] = Query(None, description="Filter by channel: email or whatsapp"),
    situation: Optional[str] = Query(None, description="Filter by situation/context"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and subject"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List all system templates (admin only).
    Only returns templates where is_system_template=true.
    """
    try:
        query = select(EmailTemplate).where(EmailTemplate.is_system_template == True)
        
        if category:
            query = query.where(EmailTemplate.category == category)
        
        if channel:
            query = query.where(EmailTemplate.channel == channel)
        
        if situation:
            query = query.where(EmailTemplate.situation == situation)
        
        if is_active is not None:
            query = query.where(EmailTemplate.is_active == is_active)
        
        if search:
            from sqlalchemy import or_
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    EmailTemplate.name.ilike(search_term),
                    EmailTemplate.subject.ilike(search_term)
                )
            )
        
        count_query = select(func.count(EmailTemplate.id)).where(EmailTemplate.is_system_template == True)
        if category:
            count_query = count_query.where(EmailTemplate.category == category)
        if channel:
            count_query = count_query.where(EmailTemplate.channel == channel)
        if situation:
            count_query = count_query.where(EmailTemplate.situation == situation)
        if is_active is not None:
            count_query = count_query.where(EmailTemplate.is_active == is_active)
        if search:
            from sqlalchemy import or_
            search_term = f"%{search}%"
            count_query = count_query.where(
                or_(
                    EmailTemplate.name.ilike(search_term),
                    EmailTemplate.subject.ilike(search_term)
                )
            )
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.offset(skip).limit(limit).order_by(EmailTemplate.created_at.desc())
        result = await db.execute(query)
        templates = result.scalars().all()
        
        logger.info(f"Listed {len(templates)} system templates")
        
        return SystemTemplateListResponse(
            total=total,
            items=[template_to_response(t) for t in templates]
        )
        
    except Exception as e:
        logger.error(f"Error listing system templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=SystemTemplateResponse, status_code=201)
async def create_system_template(
    template_data: SystemTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new system template (admin only).
    System templates can be published to all companies.
    """
    try:
        logger.info(f"Creating system template: {template_data.name}")
        
        existing = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.name == template_data.name,
                EmailTemplate.is_system_template == True
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"System template with name '{template_data.name}' already exists"
            )
        
        template = EmailTemplate(
            id=uuid_module.uuid4(),
            name=template_data.name,
            subject=template_data.subject,
            body_html=template_data.body_html,
            body_text=template_data.body_text,
            category=template_data.category,
            channel=template_data.channel,
            situation=template_data.situation,
            variables=template_data.variables,
            is_active=True,
            is_system_template=True,
            version=1,
            company_id=None,
            created_by="admin",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"System template created: {template.id}")
        
        return template_to_response(template)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating system template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=SystemTemplateResponse)
async def get_system_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific system template by ID (admin only).
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == uuid_module.UUID(template_id),
                EmailTemplate.is_system_template == True
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="System template not found")
        
        return template_to_response(template)
        
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except Exception as e:
        logger.error(f"Error getting system template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=SystemTemplateResponse)
async def update_system_template(
    template_id: str,
    template_data: SystemTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing system template (admin only).
    Increments the version number on update.
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == uuid_module.UUID(template_id),
                EmailTemplate.is_system_template == True
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="System template not found")
        
        update_data = template_data.model_dump(exclude_unset=True)
        
        if 'name' in update_data and update_data['name'] != template.name:
            existing = await db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.name == update_data['name'],
                    EmailTemplate.is_system_template == True,
                    EmailTemplate.id != uuid_module.UUID(template_id)
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"System template with name '{update_data['name']}' already exists"
                )
        
        for field, value in update_data.items():
            if hasattr(template, field):
                setattr(template, field, value)
        
        template.version = (template.version or 1) + 1
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"System template updated: {template_id} (v{template.version})")
        
        return template_to_response(template)
        
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating system template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_system_template(
    template_id: str,
    hard_delete: bool = Query(False, description="If True, permanently delete. If False, soft delete (deactivate)."),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a system template (admin only).
    By default performs a soft delete (deactivation).
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == uuid_module.UUID(template_id),
                EmailTemplate.is_system_template == True
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="System template not found")
        
        if hard_delete:
            await db.delete(template)
            message = "System template permanently deleted"
            logger.info(f"System template permanently deleted: {template_id}")
        else:
            template.is_active = False
            template.updated_at = datetime.utcnow()
            message = "System template deactivated"
            logger.info(f"System template deactivated: {template_id}")
        
        await db.commit()
        
        return {"message": message, "id": template_id}
        
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting system template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/publish", response_model=PublishResult)
async def publish_template_to_companies(
    template_id: str,
    company_ids: Optional[List[str]] = Query(None, description="Specific company IDs to publish to. If empty, publishes to all companies."),
    db: AsyncSession = Depends(get_db)
):
    """
    Publish a system template to all companies or specific companies (admin only).
    
    Creates a copy of the system template for each company, allowing them to
    customize it while keeping the original system template intact.
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == uuid_module.UUID(template_id),
                EmailTemplate.is_system_template == True
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="System template not found")
        
        if not template.is_active:
            raise HTTPException(status_code=400, detail="Cannot publish an inactive template")
        
        from app.auth.models import User as UserModel
        
        if company_ids:
            target_companies = company_ids
        else:
            companies_result = await db.execute(
                select(UserModel.company_id).where(
                    UserModel.company_id.isnot(None),
                    UserModel.is_active == True
                ).distinct()
            )
            target_companies = [c for c in companies_result.scalars().all() if c]
        
        if not target_companies:
            return PublishResult(
                success=True,
                message="No companies found to publish to",
                companies_count=0,
                template_id=template_id
            )
        
        published_count = 0
        for company_id in target_companies:
            existing = await db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.name == template.name,
                    EmailTemplate.company_id == company_id,
                    EmailTemplate.is_system_template == False
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            company_template = EmailTemplate(
                id=uuid_module.uuid4(),
                name=template.name,
                subject=template.subject,
                body_html=template.body_html,
                body_text=template.body_text,
                category=template.category,
                channel=template.channel,
                situation=template.situation,
                variables=template.variables,
                is_active=True,
                is_system_template=False,
                version=1,
                company_id=company_id,
                created_by=str(current_user.id),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(company_template)
            published_count += 1
        
        await db.commit()
        
        logger.info(
            f"System template {template_id} published to {published_count} companies by admin {current_user.email}"
        )
        
        return PublishResult(
            success=True,
            message=f"Template published to {published_count} companies" + 
                    (f" (skipped {len(target_companies) - published_count} existing)" 
                     if published_count < len(target_companies) else ""),
            companies_count=published_count,
            template_id=template_id
        )
        
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error publishing template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
