"""
Integration Catalog — canonical CRUD endpoints.

Audit 2026-05-20 Sprint 4 (catalogos dinamicos):
substitui o catalogo hardcoded `integration-data.ts` (frontend) por
modelo per-tenant canonical.

Permissoes (decisao C Paulo 2026-05-20):
- Admin: full CRUD (create/read/update/delete).
- Recrutador: read + create-novos OK; NAO pode update/delete de outros.

Prefix canonical: /api/v1/integration-catalog
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    require_admin,
    require_admin_or_recruiter,
)
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.ats_integration.repositories.integration_catalog_entry_repository import (
    IntegrationCatalogEntryRepository,
)
from app.schemas.integration_catalog_entry import (
    CustomizeIntegrationMasterRequest,
    IntegrationCatalogEntryCreate,
    IntegrationCatalogEntryListResponse,
    IntegrationCatalogEntryResponse,
    IntegrationCatalogEntryUpdate,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/integration-catalog",
    tags=["integration-catalog"],
)


@router.get(
    "",
    response_model=IntegrationCatalogEntryListResponse,
    summary="List integration catalog (master + custom da company)",
)
async def list_entries(
    include_master: bool = Query(True, description="Inclui master canonical"),
    include_deleted: bool = Query(False, description="Inclui soft-deleted (admin only)"),
    category: str | None = Query(None, description="Filtra por category (ats, ai_models, ...)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Lista canonical: master items (curados WeDOTalent) + customs da company."""
    if include_deleted and current_user.role.value != "admin":
        raise HTTPException(403, "Apenas admin pode listar soft-deleted")

    repo = IntegrationCatalogEntryRepository(db)
    items = await repo.list_for_company(
        company_id=company_id,
        include_master=include_master,
        include_deleted=include_deleted,
        category=category,
    )
    master_count = sum(1 for x in items if x.is_master_template)
    custom_count = sum(1 for x in items if not x.is_master_template)
    return IntegrationCatalogEntryListResponse(
        items=items,
        total=len(items),
        master_count=master_count,
        custom_count=custom_count,
    )


@router.get(
    "/{entry_id}",
    response_model=IntegrationCatalogEntryResponse,
    summary="Get entry canonical (master OR custom da company)",
)
async def get_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    repo = IntegrationCatalogEntryRepository(db)
    entry = await repo.get_by_id(entry_id, company_id)
    if not entry:
        raise HTTPException(404, "Entry não encontrado ou fora do escopo da empresa")
    return entry


@router.post(
    "",
    response_model=IntegrationCatalogEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom integration entry (recrutador + admin OK)",
)
async def create_entry(
    payload: IntegrationCatalogEntryCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Cria custom canonical (decisao Paulo C: recrutador pode criar)."""
    repo = IntegrationCatalogEntryRepository(db)
    try:
        entry = await repo.create_custom(
            company_id=company_id,
            data=payload.data.model_dump(),
            created_by=str(current_user.id) if current_user else None,
        )
        await db.commit()
        logger.info(
            "Integration catalog entry created: id=%s company=%s by=%s",
            entry.id,
            company_id,
            current_user.id if current_user else "unknown",
        )
        return entry
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to create integration catalog entry")
        raise HTTPException(500, detail=f"Falha ao criar entry: {e}")


@router.put(
    "/{entry_id}",
    response_model=IntegrationCatalogEntryResponse,
    summary="Update custom entry (admin OR owner)",
)
async def update_entry(
    entry_id: uuid.UUID,
    payload: IntegrationCatalogEntryUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Update canonical: admin tudo, recrutador apenas seus proprios entries."""
    repo = IntegrationCatalogEntryRepository(db)
    existing = await repo.get_by_id(entry_id, company_id)
    if not existing:
        raise HTTPException(404, "Entry não encontrado")
    if existing.is_master_template:
        raise HTTPException(403, "Master entries são imutáveis. Use POST /customize")
    # Ownership check (decisao Paulo C)
    is_admin = current_user.role.value == "admin"
    is_owner = existing.created_by == str(current_user.id) if current_user else False
    if not is_admin and not is_owner:
        raise HTTPException(403, "Você não tem permissão para editar este entry")

    try:
        updated = await repo.update(
            entry_id=entry_id,
            company_id=company_id,
            data=payload.data.model_dump(),
        )
        await db.commit()
        return updated
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to update integration catalog entry")
        raise HTTPException(500, detail=f"Falha ao atualizar entry: {e}")


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete entry (admin only — decisao Paulo C)",
)
async def delete_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    company_id: str = Depends(require_company_id),
):
    """Soft-delete canonical — apenas admin (decisao Paulo C 2026-05-20)."""
    repo = IntegrationCatalogEntryRepository(db)
    success = await repo.soft_delete(entry_id, company_id)
    if not success:
        raise HTTPException(
            404,
            "Entry não encontrado, é master (immutable), ou fora do escopo da empresa",
        )
    await db.commit()
    logger.info(
        "Integration catalog entry soft-deleted: id=%s by_admin=%s",
        entry_id,
        current_user.id if current_user else "unknown",
    )
    return None


@router.post(
    "/{master_id}/customize",
    response_model=IntegrationCatalogEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Customize master entry (cópia canonical A1, snapshot B1)",
)
async def customize_master(
    master_id: uuid.UUID,
    payload: CustomizeIntegrationMasterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_recruiter),
    company_id: str = Depends(require_company_id),
):
    """Customize master canonical — cópia total snapshot (decisões Paulo A1+B1)."""
    repo = IntegrationCatalogEntryRepository(db)
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
            raise HTTPException(404, "Master entry não encontrado ou não é master")
        await db.commit()
        logger.info(
            "Integration master customized: master=%s -> custom=%s company=%s",
            master_id,
            custom.id,
            company_id,
        )
        return custom
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to customize integration master")
        raise HTTPException(500, detail=f"Falha ao customizar master: {e}")
