"""Endpoint REST canonical pra AgentTemplateCatalog.

Reads (GET) abertos a qualquer tenant autenticado — catálogo global V1.
Writes (POST/PUT/DELETE) gated por UserRole.wedotalent_admin (staff WeDOTalent).

Canonical patterns aplicados:
- Pydantic conventions REGRA 1 (WeDoBaseModel extra='forbid')
- Pydantic conventions REGRA 2 (sem company_id no payload — vem do JWT)
- Pydantic conventions REGRA 3 (UUID path via type alias)
- ADR-001 (zero SQL inline — só repo)
- Audit canonical via AuditService.log_decision em mutations
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_wedotalent_admin
from app.auth.models import User
from app.core.database import get_tenant_db
from app.schemas.agent_template_catalog import (
    AgentCategoryResponse,
    AgentSectorResponse,
    AgentTemplateCatalogRequest,
    AgentTemplateCatalogResponse,
)
from app.shared.security.require_company_id import require_company_id

router = APIRouter(prefix="/agent-template-catalog", tags=["agent-template-catalog"])


# Type alias canonical pra path UUID (Pydantic conventions REGRA 3)
TemplateIdParam = Annotated[
    str,
    Path(
        ...,
        pattern=r"^[0-9a-fA-F-]{36}$",
        description="AgentTemplateCatalog ID — UUID v4",
    ),
]


def _get_repo(db: AsyncSession):
    from app.domains.ai.repositories.agent_template_catalog_repository import (
        AgentTemplateCatalogRepository,
    )
    return AgentTemplateCatalogRepository(db)


def _log_audit_safe(action: str, *, company_id: str, payload: dict) -> None:
    """Audit best-effort — não bloqueia request se audit falhar."""
    try:
        from app.shared.services.audit_service import AuditService

        AuditService.log_decision(
            action=action,
            company_id=company_id,
            reasoning=[payload],
        )
    except Exception:  # pragma: no cover — audit fail não pode quebrar feature
        import logging

        logging.getLogger(__name__).exception(
            "audit log_decision failed for action=%s", action
        )


# ─────────────────────────────────────────────────────────────────────────────
# READ endpoints — abertos a qualquer tenant autenticado
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/categories", response_model=list[AgentCategoryResponse])
async def list_categories(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
    user: User = Depends(get_current_user),
):
    """Lista categorias do catálogo (extensibilidade NPS via INSERT)."""
    repo = _get_repo(db)
    items = await repo.list_categories(active_only=active_only)
    return items


@router.get("/sectors", response_model=list[AgentSectorResponse])
async def list_sectors(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
    user: User = Depends(get_current_user),
):
    repo = _get_repo(db)
    items = await repo.list_sectors(active_only=active_only)
    return items


@router.get("", response_model=list[AgentTemplateCatalogResponse])
async def list_templates(
    category: str | None = Query(None, description="slug de agent_categories"),
    sector: str | None = Query(None, description="slug de agent_sectors"),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
    user: User = Depends(get_current_user),
):
    """GET /agent-template-catalog — catálogo seed global.

    Query: category=screening, sector=tech, active_only=true (default).
    Categoria inexistente retorna [] (extensibilidade canonical).
    """
    repo = _get_repo(db)
    items = await repo.list(category=category, sector=sector, active_only=active_only)
    return items


@router.get("/{template_id}", response_model=AgentTemplateCatalogResponse)
async def get_template(
    template_id: TemplateIdParam,
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
    user: User = Depends(get_current_user),
):
    repo = _get_repo(db)
    template = await repo.get_by_id(UUID(template_id))
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    return template


# ─────────────────────────────────────────────────────────────────────────────
# WRITE endpoints — UserRole.wedotalent_admin only
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=AgentTemplateCatalogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    payload: AgentTemplateCatalogRequest,
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
    user: User = Depends(require_wedotalent_admin),
):
    repo = _get_repo(db)
    # Slug deve ser único globalmente
    existing = await repo.get_by_slug(payload.slug)
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"slug {payload.slug!r} already exists")

    created = await repo.create(payload.model_dump(), company_id=None)
    _log_audit_safe(
        "agent_template_catalog_create",
        company_id=company_id,
        payload={"slug": payload.slug, "actor_user_id": str(user.id)},
    )
    return created


@router.put("/{template_id}", response_model=AgentTemplateCatalogResponse)
async def update_template(
    template_id: TemplateIdParam,
    payload: AgentTemplateCatalogRequest,
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
    user: User = Depends(require_wedotalent_admin),
):
    repo = _get_repo(db)
    template = await repo.get_by_id(UUID(template_id))
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    updated = await repo.update(template, payload.model_dump())
    _log_audit_safe(
        "agent_template_catalog_update",
        company_id=company_id,
        payload={"id": template_id, "slug": payload.slug, "actor_user_id": str(user.id)},
    )
    return updated


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: TemplateIdParam,
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
    user: User = Depends(require_wedotalent_admin),
):
    repo = _get_repo(db)
    template = await repo.get_by_id(UUID(template_id))
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    await repo.delete(template)
    _log_audit_safe(
        "agent_template_catalog_delete",
        company_id=company_id,
        payload={"id": template_id, "actor_user_id": str(user.id)},
    )
    return None
