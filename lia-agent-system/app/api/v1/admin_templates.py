"""
Admin Templates API endpoints for managing system email templates.
Admin-only endpoints for creating and managing templates that can be published to companies.
"""
import logging
import uuid as uuid_module
from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.repositories.admin_template_repository import (
    AdminTemplateRepository,
)
from app.models.email_template import EmailTemplate
from app.schemas.email_template import EmailTemplateResponse
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/templates", tags=["admin-templates"])


class SystemTemplateCreate(WeDoBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    subject: str | None = Field(None, max_length=500)
    body_html: str = Field(..., min_length=1)
    body_text: str | None = None
    category: str | None = Field(None, max_length=50)
    channel: str = Field(default="email")
    situation: str | None = Field(None, max_length=50)
    variables: list[str] = Field(default_factory=list)


class SystemTemplateUpdate(WeDoBaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    subject: str | None = Field(None, max_length=500)
    body_html: str | None = Field(None, min_length=1)
    body_text: str | None = None
    category: str | None = Field(None, max_length=50)
    channel: str | None = Field(None, max_length=20)
    situation: str | None = Field(None, max_length=50)
    variables: list[str] | None = None
    is_active: bool | None = None


class SystemTemplateResponse(EmailTemplateResponse):
    is_system_template: bool = True
    version: int = 1


class SystemTemplateListResponse(BaseModel):
    total: int
    items: list[SystemTemplateResponse]


class PublishResult(BaseModel):
    success: bool
    message: str
    companies_count: int
    template_id: str


def template_to_response(template: EmailTemplate) -> SystemTemplateResponse:
    return SystemTemplateResponse(
        id=cast(uuid_module.UUID, template.id),
        name=cast(str, template.name),
        subject=cast(str | None, template.subject),
        body_html=cast(str, template.body_html),
        body_text=cast(str | None, template.body_text),
        category=cast(str | None, template.category),
        channel=cast(str, template.channel) if template.channel else "email",
        situation=cast(str | None, template.situation),
        variables=cast(list[str], template.variables) if template.variables else [],
        is_active=cast(bool, template.is_active),
        is_system_template=cast(bool, template.is_system_template),
        version=cast(int, template.version) if template.version else 1,
        created_by=cast(str | None, template.created_by),
        created_at=cast(datetime, template.created_at),
        updated_at=cast(datetime, template.updated_at) if template.updated_at else cast(datetime, template.created_at),
    )


@router.get("", response_model=SystemTemplateListResponse)
async def list_system_templates(
    category: str | None = Query(None),
    channel: str | None = Query(None),
    situation: str | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """List all system templates (admin only)."""
    try:
        repo = AdminTemplateRepository(db)
        templates, total = await repo.list_system_templates(
            category=category, channel=channel, situation=situation,
            is_active=is_active, search=search, skip=skip, limit=limit,
        )
        logger.info(f"Listed {len(templates)} system templates")
        return SystemTemplateListResponse(total=total, items=[template_to_response(t) for t in templates])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing system templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=SystemTemplateResponse, status_code=201)
async def create_system_template(
    template_data: SystemTemplateCreate,
    db: AsyncSession = Depends(get_tenant_db),
    _admin: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Create a new system template (admin only)."""
    try:
        repo = AdminTemplateRepository(db)
        if await repo.get_system_template_by_name(template_data.name):
            raise HTTPException(
                status_code=400,
                detail=f"System template with name '{template_data.name}' already exists",
            )
        template = await repo.create_system_template({
            "name": template_data.name,
            "subject": template_data.subject,
            "body_html": template_data.body_html,
            "body_text": template_data.body_text,
            "category": template_data.category,
            "channel": template_data.channel,
            "situation": template_data.situation,
            "variables": template_data.variables,
            "is_active": True,
            "version": 1,
        })
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
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Get a specific system template by ID (admin only)."""
    try:
        repo = AdminTemplateRepository(db)
        template = await repo.get_system_template_by_id(uuid_module.UUID(template_id))
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
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    template_data: SystemTemplateUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    _admin: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Update an existing system template (admin only). Increments version."""
    try:
        repo = AdminTemplateRepository(db)
        tid = uuid_module.UUID(template_id)
        template = await repo.get_system_template_by_id(tid)
        if not template:
            raise HTTPException(status_code=404, detail="System template not found")

        update_data = template_data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != template.name:
            if await repo.get_system_template_by_name(update_data["name"], exclude_id=tid):
                raise HTTPException(
                    status_code=400,
                    detail=f"System template with name '{update_data['name']}' already exists",
                )

        template = await repo.update_system_template(template, update_data)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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


@router.delete("/{template_id}", response_model=None)
async def delete_system_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    hard_delete: bool = Query(False),
    db: AsyncSession = Depends(get_tenant_db),
    _admin: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Delete a system template (admin only). Soft delete by default."""
    try:
        repo = AdminTemplateRepository(db)
        template = await repo.get_system_template_by_id(uuid_module.UUID(template_id))
        if not template:
            raise HTTPException(status_code=404, detail="System template not found")
        msg = await repo.delete_system_template(template, hard=hard_delete)
        logger.info(f"System template {msg}: {template_id}")
        return {"message": f"System template {msg}", "id": template_id}
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
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_ids: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    _admin: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Publish a system template to all or specific companies (admin only)."""
    try:
        repo = AdminTemplateRepository(db)
        template = await repo.get_system_template_by_id(uuid_module.UUID(template_id))
        if not template:
            raise HTTPException(status_code=404, detail="System template not found")
        if not template.is_active:
            raise HTTPException(status_code=400, detail="Cannot publish an inactive template")

        target_companies = company_ids or await repo.get_company_ids_with_active_users()
        if not target_companies:
            return PublishResult(success=True, message="No companies found to publish to", companies_count=0, template_id=template_id)

        published_count = 0
        for company_id in target_companies:
            if await repo.get_company_template_by_name(template.name, company_id):
                continue
            await repo.create_company_copy(template, company_id, created_by="admin")
            published_count += 1

        skipped = len(target_companies) - published_count
        msg = f"Template published to {published_count} companies"
        if skipped:
            msg += f" (skipped {skipped} existing)"
        logger.info(f"System template {template_id} published to {published_count} companies")
        return PublishResult(success=True, message=msg, companies_count=published_count, template_id=template_id)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error publishing template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
