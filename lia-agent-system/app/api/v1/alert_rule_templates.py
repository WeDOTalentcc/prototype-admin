"""
Alert Rule Templates - canonical CRUD endpoints.

Audit 2026-05-20 Sprint 3 (catalogos dinamicos):
substitui o catalogo hardcoded DEFAULT_ALERTS (CommunicationHub.constants.ts)
por modelo per-tenant canonical.

Permissoes (decisao C Paulo 2026-05-20):
- Admin: full CRUD (create/read/update/delete).
- Recrutador: read + create-novos OK; nao pode delete; edita apenas seus
  proprios (ownership por created_by).
"""
from __future__ import annotations

import logging
from app.shared.errors import LIAInternalError
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    require_admin,
    require_admin_or_recruiter,
)
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.communication.repositories.alert_rule_template_repository import (
    AlertRuleTemplateRepository,
)
from app.schemas.alert_rule_template import (
    AlertRuleTemplateCreate,
    AlertRuleTemplateListResponse,
    AlertRuleTemplateResponse,
    AlertRuleTemplateUpdate,
    CustomizeMasterRequest,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/alert-rule-templates",
    tags=["alert-rule-templates"],
)


@router.get(
    "",
    response_model=AlertRuleTemplateListResponse,
    summary="List alert rule templates (master + custom da company)",
)
async def list_templates(
    include_master: bool = Query(True, description="Inclui master canonical"),
    include_deleted: bool = Query(False, description="Inclui soft-deleted (admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Lista canonical: master items (curados WeDOTalent) + customs da company."""
    if include_deleted and current_user.role.value != "admin":
        raise HTTPException(403, "Apenas admin pode listar soft-deleted")

    repo = AlertRuleTemplateRepository(db)
    items = await repo.list_for_company(
        company_id=company_id,
        include_master=include_master,
        include_deleted=include_deleted,
    )
    master_count = sum(1 for x in items if x.is_master_template)
    custom_count = sum(1 for x in items if not x.is_master_template)
    return AlertRuleTemplateListResponse(
        items=items,
        total=len(items),
        master_count=master_count,
        custom_count=custom_count,
    )


@router.get(
    "/{template_id}",
    response_model=AlertRuleTemplateResponse,
    summary="Get template canonical (master OR custom da company)",
)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    repo = AlertRuleTemplateRepository(db)
    template = await repo.get_by_id(template_id, company_id)
    if not template:
        raise HTTPException(404, "Template nao encontrado ou fora do escopo da empresa")
    return template


@router.post(
    "",
    response_model=AlertRuleTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom template (recrutador + admin OK)",
)
async def create_template(
    payload: AlertRuleTemplateCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Cria custom canonical (decisao Paulo C: recrutador pode criar)."""
    repo = AlertRuleTemplateRepository(db)
    try:
        template = await repo.create_custom(
            company_id=company_id,
            data=payload.data.model_dump(),
            created_by=str(current_user.id) if current_user else None,
        )
        await db.commit()
        logger.info(
            "Alert rule template created: id=%s company=%s by=%s",
            template.id,
            company_id,
            current_user.id if current_user else "unknown",
        )
        return template
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to create alert rule template")
        raise LIAInternalError(f"Falha ao criar template: {e}")


@router.put(
    "/{template_id}",
    response_model=AlertRuleTemplateResponse,
    summary="Update custom template (admin OR owner)",
)
async def update_template(
    template_id: uuid.UUID,
    payload: AlertRuleTemplateUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Update canonical: admin tudo, recrutador apenas seus proprios templates."""
    repo = AlertRuleTemplateRepository(db)
    existing = await repo.get_by_id(template_id, company_id)
    if not existing:
        raise HTTPException(404, "Template nao encontrado")
    if existing.is_master_template:
        raise HTTPException(403, "Master templates sao imutaveis. Use POST /customize")
    # Ownership check (decisao Paulo C)
    is_admin = current_user.role.value == "admin"
    is_owner = existing.created_by == str(current_user.id) if current_user else False
    if not is_admin and not is_owner:
        raise HTTPException(403, "Voce nao tem permissao para editar este template")

    try:
        updated = await repo.update(
            template_id=template_id,
            company_id=company_id,
            data=payload.data.model_dump(),
        )
        await db.commit()
        return updated
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to update alert rule template")
        raise LIAInternalError(f"Falha ao atualizar template: {e}")


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete template (admin only - decisao Paulo C)",
)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    company_id: str = Depends(require_company_id),
):
    """Soft-delete canonical - apenas admin (decisao Paulo C 2026-05-20)."""
    repo = AlertRuleTemplateRepository(db)
    success = await repo.soft_delete(template_id, company_id)
    if not success:
        raise HTTPException(
            404,
            "Template nao encontrado, e master (immutable), ou fora do escopo da empresa",
        )
    await db.commit()
    logger.info(
        "Alert rule template soft-deleted: id=%s by_admin=%s",
        template_id,
        current_user.id if current_user else "unknown",
    )
    return None


@router.post(
    "/{master_id}/customize",
    response_model=AlertRuleTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Customize master template (copia canonical A1, snapshot B1)",
)
async def customize_master(
    master_id: uuid.UUID,
    payload: CustomizeMasterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Customize master canonical - copia total snapshot (decisoes Paulo A1+B1)."""
    repo = AlertRuleTemplateRepository(db)
    overrides = (
        payload.overrides.model_dump() if payload.overrides else None
    )
    try:
        custom = await repo.customize_master(
            master_id=master_id,
            company_id=company_id,
            created_by=str(current_user.id) if current_user else None,
            overrides=overrides,
        )
        if not custom:
            raise HTTPException(404, "Master template nao encontrado ou nao e master")
        await db.commit()
        logger.info(
            "Master customized: master=%s -> custom=%s company=%s",
            master_id,
            custom.id,
            company_id,
        )
        return custom
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to customize master template")
        raise LIAInternalError(f"Falha ao customizar master: {e}")
