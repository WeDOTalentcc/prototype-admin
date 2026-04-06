"""
Default Templates API Endpoints.

Provides REST endpoints for managing system-wide default communication templates.
These templates serve as starting points that clients can copy and customize.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.default_templates import (
    AVAILABLE_TEMPLATE_VARIABLES,
    DEFAULT_TEMPLATES_SEED,
    DefaultTemplate,
)
from app.schemas.default_templates import (
    DefaultTemplateCreate,
    DefaultTemplateDuplicateRequest,
    DefaultTemplateListResponse,
    DefaultTemplateResponse,
    DefaultTemplateUpdate,
    SeedTemplatesResponse,
    TemplateVariableResponse,
    TemplateVariablesListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/default-templates", tags=["default-templates"])


def get_user_from_headers(
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role")
) -> dict[str, Any]:
    """Get user context from request headers."""
    return {
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin"
    }


def require_admin(current_user: dict[str, Any]) -> None:
    """Raise exception if user is not admin."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


@router.get("/variables", summary="List available template variables")
async def list_template_variables() -> TemplateVariablesListResponse:
    """
    Get all available template variables that can be used in templates.
    
    Returns a list of variable names with descriptions and example values.
    """
    variables = [
        TemplateVariableResponse(**var)
        for var in AVAILABLE_TEMPLATE_VARIABLES
    ]
    return TemplateVariablesListResponse(variables=variables)


@router.get("", summary="List default templates")
async def list_default_templates(
    category: str | None = Query(None, description="Filter by category: email, sms, whatsapp, push"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status: active, draft, archived"),
    search: str | None = Query(None, description="Search by template name"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
) -> DefaultTemplateListResponse:
    """
    List all default templates with optional filtering.
    """
    try:
        conditions = []
        
        if category:
            conditions.append(DefaultTemplate.category == category)
        
        if status_filter:
            conditions.append(DefaultTemplate.status == status_filter)
        
        if search:
            conditions.append(DefaultTemplate.name.ilike(f"%{search}%"))
        
        query = select(DefaultTemplate)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(DefaultTemplate.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        count_query = select(func.count(DefaultTemplate.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        logger.info(f"Listed {len(templates)} default templates (total: {total})")
        
        return DefaultTemplateListResponse(
            total=total,
            items=[
                DefaultTemplateResponse(
                    id=t.id,
                    name=t.name,
                    category=t.category,
                    subject=t.subject,
                    body=t.body,
                    variables=t.variables or [],
                    status=t.status,
                    client_usage_count=t.client_usage_count or 0,
                    created_by=t.created_by,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in templates
            ]
        )
        
    except Exception as e:
        logger.error(f"Error listing default templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list default templates: {str(e)}"
        )


@router.get("/{template_id}", summary="Get default template")
async def get_default_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DefaultTemplateResponse:
    """
    Get a specific default template by ID.
    """
    try:
        query = select(DefaultTemplate).where(DefaultTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return DefaultTemplateResponse(
            id=template.id,
            name=template.name,
            category=template.category,
            subject=template.subject,
            body=template.body,
            variables=template.variables or [],
            status=template.status,
            client_usage_count=template.client_usage_count or 0,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default template: {str(e)}"
        )


@router.post("", summary="Create default template", status_code=status.HTTP_201_CREATED)
async def create_default_template(
    data: DefaultTemplateCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> DefaultTemplateResponse:
    """
    Create a new default template.
    
    Admin access required.
    """
    try:
        require_admin(current_user)
        
        template = DefaultTemplate(
            name=data.name,
            category=data.category.value,
            subject=data.subject,
            body=data.body,
            variables=data.variables,
            status=data.status.value,
            created_by=data.created_by or current_user.get("user_id"),
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Created default template: {template.id} - {template.name}")
        
        return DefaultTemplateResponse(
            id=template.id,
            name=template.name,
            category=template.category,
            subject=template.subject,
            body=template.body,
            variables=template.variables or [],
            status=template.status,
            client_usage_count=template.client_usage_count or 0,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating default template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create default template: {str(e)}"
        )


@router.put("/{template_id}", summary="Update default template")
async def update_default_template(
    template_id: UUID,
    data: DefaultTemplateUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> DefaultTemplateResponse:
    """
    Update an existing default template.
    
    Admin access required.
    """
    try:
        require_admin(current_user)
        
        query = select(DefaultTemplate).where(DefaultTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        if data.name is not None:
            template.name = data.name
        if data.category is not None:
            template.category = data.category.value
        if data.subject is not None:
            template.subject = data.subject
        if data.body is not None:
            template.body = data.body
        if data.variables is not None:
            template.variables = data.variables
        if data.status is not None:
            template.status = data.status.value
        
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Updated default template: {template.id} - {template.name}")
        
        return DefaultTemplateResponse(
            id=template.id,
            name=template.name,
            category=template.category,
            subject=template.subject,
            body=template.body,
            variables=template.variables or [],
            status=template.status,
            client_usage_count=template.client_usage_count or 0,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating default template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update default template: {str(e)}"
        )


@router.delete("/{template_id}", summary="Delete default template")
async def delete_default_template(
    template_id: UUID,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Delete a default template.
    
    Admin access required.
    """
    try:
        require_admin(current_user)
        
        query = select(DefaultTemplate).where(DefaultTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        template_name = template.name
        await db.delete(template)
        await db.commit()
        
        logger.info(f"Deleted default template: {template_id} - {template_name}")
        
        return {
            "success": True,
            "message": f"Template '{template_name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting default template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete default template: {str(e)}"
        )


@router.post("/{template_id}/duplicate", summary="Duplicate default template")
async def duplicate_default_template(
    template_id: UUID,
    data: DefaultTemplateDuplicateRequest | None = None,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> DefaultTemplateResponse:
    """
    Duplicate an existing default template.
    
    Admin access required.
    """
    try:
        require_admin(current_user)
        
        query = select(DefaultTemplate).where(DefaultTemplate.id == template_id)
        result = await db.execute(query)
        original_template = result.scalar_one_or_none()
        
        if not original_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        new_name = data.new_name if data and data.new_name else f"{original_template.name} (Copy)"
        
        new_template = DefaultTemplate(
            name=new_name,
            category=original_template.category,
            subject=original_template.subject,
            body=original_template.body,
            variables=original_template.variables.copy() if original_template.variables else [],
            status="draft",
            created_by=current_user.get("user_id"),
        )
        
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        
        logger.info(f"Duplicated default template: {template_id} -> {new_template.id}")
        
        return DefaultTemplateResponse(
            id=new_template.id,
            name=new_template.name,
            category=new_template.category,
            subject=new_template.subject,
            body=new_template.body,
            variables=new_template.variables or [],
            status=new_template.status,
            client_usage_count=new_template.client_usage_count or 0,
            created_by=new_template.created_by,
            created_at=new_template.created_at,
            updated_at=new_template.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error duplicating default template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate default template: {str(e)}"
        )


@router.post("/seed", summary="Seed default templates")
async def seed_default_templates(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
) -> SeedTemplatesResponse:
    """
    Seed the database with default recruitment templates.
    Only creates templates that don't already exist (by name).
    
    Admin access required.
    """
    try:
        require_admin(current_user)
        
        created_templates = []
        
        for template_data in DEFAULT_TEMPLATES_SEED:
            existing_query = select(DefaultTemplate).where(
                DefaultTemplate.name == template_data["name"]
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if not existing:
                template = DefaultTemplate(
                    name=template_data["name"],
                    category=template_data["category"],
                    subject=template_data.get("subject"),
                    body=template_data["body"],
                    variables=template_data.get("variables", []),
                    status=template_data.get("status", "active"),
                    created_by="system",
                )
                db.add(template)
                created_templates.append(template)
        
        if created_templates:
            await db.commit()
            for template in created_templates:
                await db.refresh(template)
        
        logger.info(f"Seeded {len(created_templates)} default templates")
        
        return SeedTemplatesResponse(
            created=len(created_templates),
            templates=[
                DefaultTemplateResponse(
                    id=t.id,
                    name=t.name,
                    category=t.category,
                    subject=t.subject,
                    body=t.body,
                    variables=t.variables or [],
                    status=t.status,
                    client_usage_count=t.client_usage_count or 0,
                    created_by=t.created_by,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in created_templates
            ],
            message=f"Successfully created {len(created_templates)} default templates"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding default templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed default templates: {str(e)}"
        )
