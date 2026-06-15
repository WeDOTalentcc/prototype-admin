"""
Default Templates API Endpoints.

Provides REST endpoints for managing system-wide default communication templates.
These templates serve as starting points that clients can copy and customize.
"""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.repositories.default_template_repository import (
    DefaultTemplateRepository,
)
from app.models.default_templates import (
    AVAILABLE_TEMPLATE_VARIABLES,
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
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/default-templates", tags=["default-templates"])


def get_user_from_headers(
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    return {
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin",
    }


def require_admin(current_user: dict[str, Any]) -> None:
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def _to_response(t: DefaultTemplate) -> DefaultTemplateResponse:
    return DefaultTemplateResponse(
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


@router.get("/variables", response_model=None)
async def list_template_variables(company_id: str = Depends(require_company_id)) -> TemplateVariablesListResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all available template variables."""
    variables = [TemplateVariableResponse(**var) for var in AVAILABLE_TEMPLATE_VARIABLES]
    return TemplateVariablesListResponse(variables=variables)


@router.get("", response_model=None)
async def list_default_templates(
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> DefaultTemplateListResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all default templates with optional filtering."""
    try:
        conditions = []
        if category:
            conditions.append(DefaultTemplate.category == category)
        if status_filter:
            conditions.append(DefaultTemplate.status == status_filter)
        if search:
            conditions.append(DefaultTemplate.name.ilike(f"%{search}%"))

        repo = DefaultTemplateRepository(db)
        templates, total = await repo.list_templates(conditions=conditions, limit=limit, offset=offset)
        logger.info(f"Listed {len(templates)} default templates (total: {total})")
        return DefaultTemplateListResponse(total=total, items=[_to_response(t) for t in templates])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing default templates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{template_id}", response_model=None)
async def get_default_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> DefaultTemplateResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get a specific default template by ID."""
    try:
        repo = DefaultTemplateRepository(db)
        template = await repo.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return _to_response(template)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_default_template(
    data: DefaultTemplateCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)) -> DefaultTemplateResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new default template. Admin access required."""
    try:
        require_admin(current_user)
        repo = DefaultTemplateRepository(db)
        template = await repo.create({
            "name": data.name,
            "category": data.category.value,
            "subject": data.subject,
            "body": data.body,
            "variables": data.variables,
            "status": data.status.value,
            "created_by": data.created_by or current_user.get("user_id"),
        })
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created default template: {template.id} - {template.name}")
        return _to_response(template)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating default template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{template_id}", response_model=None)
async def update_default_template(
    template_id: UUID,
    data: DefaultTemplateUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)) -> DefaultTemplateResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing default template. Admin access required."""
    try:
        require_admin(current_user)
        repo = DefaultTemplateRepository(db)
        template = await repo.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.category is not None:
            update_data["category"] = data.category.value
        if data.subject is not None:
            update_data["subject"] = data.subject
        if data.body is not None:
            update_data["body"] = data.body
        if data.variables is not None:
            update_data["variables"] = data.variables
        if data.status is not None:
            update_data["status"] = data.status.value

        template = await repo.update(template, update_data)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Updated default template: {template.id} - {template.name}")
        return _to_response(template)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating default template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{template_id}", response_model=None)
async def delete_default_template(
    template_id: UUID,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete a default template. Admin access required."""
    try:
        require_admin(current_user)
        repo = DefaultTemplateRepository(db)
        template = await repo.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        template_name = template.name
        await repo.delete(template)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Deleted default template: {template_id} - {template_name}")
        return {"success": True, "message": f"Template '{template_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting default template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{template_id}/duplicate", response_model=None)
async def duplicate_default_template(
    template_id: UUID,
    data: DefaultTemplateDuplicateRequest | None = None,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> DefaultTemplateResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Duplicate an existing default template. Admin access required."""
    try:
        require_admin(current_user)
        repo = DefaultTemplateRepository(db)
        original = await repo.get_by_id(template_id)
        if not original:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        new_name = data.new_name if data and data.new_name else f"{original.name} (Copy)"
        copy = await repo.duplicate(original, new_name, created_by=current_user.get("user_id", "system"))
        logger.info(f"Duplicated default template: {template_id} -> {copy.id}")
        return _to_response(copy)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error duplicating default template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/seed", response_model=None)
async def seed_default_templates(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> SeedTemplatesResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Seed the database with default recruitment templates. Admin access required."""
    try:
        require_admin(current_user)
        repo = DefaultTemplateRepository(db)
        created = await repo.seed_defaults(created_by=current_user.get("user_id", "system"))
        logger.info(f"Seeded {len(created)} default templates")
        return SeedTemplatesResponse(
            created=len(created),
            templates=[_to_response(t) for t in created],
            message=f"Successfully created {len(created)} default templates",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding default templates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
