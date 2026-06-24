"""
Webhook Event Types — canonical CRUD endpoints.

Audit 2026-05-20 Sprint 5 (catalogos dinamicos):
substitui o catalogo hardcoded em
`plataforma-lia/src/components/pages-agent-studio/custom-agents/webhook-types.ts`
+ `app/schemas/webhook.py:ALLOWED_EVENTS` +
`libs/models/lia_models/webhook.py:WebhookEvent` enum +
`libs/models/lia_models/webhook_registration.py:JOB_STATUS_WEBHOOK_EVENTS`
por modelo per-tenant canonical.

Permissoes (decisao C Paulo 2026-05-20):
- Admin: full CRUD (create/read/update/delete).
- Recrutador: read + create-novos OK; NAO pode update/delete de outros.
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
from app.domains.automation.repositories.webhook_event_type_repository import (
    WebhookEventTypeRepository,
)
from app.schemas.webhook_event_type import (
    CustomizeMasterRequest,
    WebhookEventTypeCreate,
    WebhookEventTypeListResponse,
    WebhookEventTypeResponse,
    WebhookEventTypeUpdate,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhook-event-types",
    tags=["webhook-event-types"],
)


@router.get(
    "",
    response_model=WebhookEventTypeListResponse,
    summary="List webhook event types (master + custom da company)",
)
async def list_event_types(
    include_master: bool = Query(True, description="Inclui master canonical"),
    include_deleted: bool = Query(
        False, description="Inclui soft-deleted (admin only)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Lista canonical: master items (curados WeDOTalent) + customs da company."""
    if include_deleted and current_user.role.value != "admin":
        raise HTTPException(403, "Apenas admin pode listar soft-deleted")

    repo = WebhookEventTypeRepository(db)
    items = await repo.list_for_company(
        company_id=company_id,
        include_master=include_master,
        include_deleted=include_deleted,
    )
    master_count = sum(1 for x in items if x.is_master_template)
    custom_count = sum(1 for x in items if not x.is_master_template)
    return WebhookEventTypeListResponse(
        items=items,
        total=len(items),
        master_count=master_count,
        custom_count=custom_count,
    )


@router.get(
    "/{event_type_id}",
    response_model=WebhookEventTypeResponse,
    summary="Get event type canonical (master OR custom da company)",
)
async def get_event_type(
    event_type_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    repo = WebhookEventTypeRepository(db)
    record = await repo.get_by_id(event_type_id, company_id)
    if not record:
        raise HTTPException(
            404, "Event type não encontrado ou fora do escopo da empresa"
        )
    return record


@router.post(
    "",
    response_model=WebhookEventTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom event type (recrutador + admin OK)",
)
async def create_event_type(
    payload: WebhookEventTypeCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Cria custom canonical (decisao Paulo C: recrutador pode criar)."""
    repo = WebhookEventTypeRepository(db)
    try:
        record = await repo.create_custom(
            company_id=company_id,
            data=payload.data.model_dump(),
            created_by=str(current_user.id) if current_user else None,
        )
        await db.commit()
        logger.info(
            "Webhook event type created: id=%s company=%s by=%s",
            record.id,
            company_id,
            current_user.id if current_user else "unknown",
        )
        return record
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to create webhook event type")
        raise LIAInternalError(f"Falha ao criar event type: {e}")


@router.put(
    "/{event_type_id}",
    response_model=WebhookEventTypeResponse,
    summary="Update custom event type (admin OR owner)",
)
async def update_event_type(
    event_type_id: uuid.UUID,
    payload: WebhookEventTypeUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Update canonical: admin tudo, recrutador apenas seus proprios event types."""
    repo = WebhookEventTypeRepository(db)
    existing = await repo.get_by_id(event_type_id, company_id)
    if not existing:
        raise HTTPException(404, "Event type não encontrado")
    if existing.is_master_template:
        raise HTTPException(403, "Master events são imutáveis. Use POST /customize")
    # Ownership check (decisao Paulo C)
    is_admin = current_user.role.value == "admin"
    is_owner = (
        existing.created_by == str(current_user.id) if current_user else False
    )
    if not is_admin and not is_owner:
        raise HTTPException(
            403, "Você não tem permissão para editar este event type"
        )

    try:
        updated = await repo.update(
            event_type_id=event_type_id,
            company_id=company_id,
            data=payload.data.model_dump(),
        )
        await db.commit()
        return updated
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to update webhook event type")
        raise LIAInternalError(f"Falha ao atualizar event type: {e}")


@router.delete(
    "/{event_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete event type (admin only — decisao Paulo C)",
)
async def delete_event_type(
    event_type_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    company_id: str = Depends(require_company_id),
):
    """Soft-delete canonical — apenas admin (decisao Paulo C 2026-05-20)."""
    repo = WebhookEventTypeRepository(db)
    success = await repo.soft_delete(event_type_id, company_id)
    if not success:
        raise HTTPException(
            404,
            "Event type não encontrado, é master (immutable), ou fora do escopo da empresa",
        )
    await db.commit()
    logger.info(
        "Webhook event type soft-deleted: id=%s by_admin=%s",
        event_type_id,
        current_user.id if current_user else "unknown",
    )
    return None


@router.post(
    "/{master_id}/customize",
    response_model=WebhookEventTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Customize master event type (cópia canonical A1, snapshot B1)",
)
async def customize_master(
    master_id: uuid.UUID,
    payload: CustomizeMasterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Customize master canonical — cópia total snapshot (decisões Paulo A1+B1)."""
    repo = WebhookEventTypeRepository(db)
    overrides = payload.overrides.model_dump() if payload.overrides else None
    try:
        custom = await repo.customize_master(
            master_id=master_id,
            company_id=company_id,
            created_by=str(current_user.id) if current_user else None,
            overrides=overrides,
        )
        if not custom:
            raise HTTPException(
                404, "Master event type não encontrado ou não é master"
            )
        await db.commit()
        logger.info(
            "Master event type customized: master=%s -> custom=%s company=%s",
            master_id,
            custom.id,
            company_id,
        )
        return custom
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to customize master event type")
        raise LIAInternalError(f"Falha ao customizar master: {e}")
