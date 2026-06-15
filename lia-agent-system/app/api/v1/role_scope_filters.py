"""
Endpoints RBAC para gerenciar permissoes declarativas (role_scope_filters).

Sprint C 2026-06-13.

GET  /rbac/permissions              -- lista todas as permissoes
POST /rbac/permissions/seed         -- popula DEFAULT_ROLE_PERMISSIONS no banco (wedotalent_admin)
GET  /rbac/permissions/check        -- verifica se role pode action em resource
PUT  /rbac/permissions/{id}         -- atualiza allowed/description (wedotalent_admin)
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from lia_config.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rbac", tags=["RBAC"])


async def _require_wedotalent_admin_or_admin(db=None, current_user=None):
    """Placeholder dependency -- replace with canonical require_wedotalent_admin when available."""
    return True


@router.get("/permissions", summary="Lista todas as permissoes de role_scope_filters")
async def list_permissions(
    role: Optional[str] = Query(None, description="Filtrar por role"),
    resource: Optional[str] = Query(None, description="Filtrar por resource"),
    db: AsyncSession = Depends(get_db),
):
    """Lista permissoes do banco. Filtros opcionais por role e resource."""
    try:
        from lia_models.role_scope_filter import RoleScopeFilter
        stmt = select(RoleScopeFilter)
        if role:
            stmt = stmt.where(RoleScopeFilter.role == role)
        if resource:
            stmt = stmt.where(RoleScopeFilter.resource == resource)
        results = (await db.execute(stmt)).scalars().all()
        return {
            "total": len(results),
            "permissions": [
                {
                    "id": str(r.id),
                    "role": r.role,
                    "resource": r.resource,
                    "action": r.action,
                    "allowed": r.allowed,
                    "conditions": r.conditions,
                    "description": r.description,
                }
                for r in results
            ],
        }
    except Exception as exc:
        logger.error("[RBAC] list_permissions error: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao listar permissoes")


@router.post("/permissions/seed", summary="Popula DEFAULT_ROLE_PERMISSIONS no banco")
async def seed_permissions(db: AsyncSession = Depends(get_db)):
    """
    Insere (ou atualiza via upsert) as permissoes do seed canonico.
    Idempotente: pode ser executado multiplas vezes sem duplicar.
    Requer: wedotalent_admin (TODO: adicionar gate quando auth disponivel).
    """
    try:
        from lia_models.role_scope_filter import RoleScopeFilter, DEFAULT_ROLE_PERMISSIONS
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(RoleScopeFilter).values(
            [
                {
                    "id": uuid.uuid4(),
                    "role": p["role"],
                    "resource": p["resource"],
                    "action": p["action"],
                    "allowed": p["allowed"],
                    "conditions": None,
                    "description": f"Seed canonico Sprint C",
                }
                for p in DEFAULT_ROLE_PERMISSIONS
            ]
        ).on_conflict_do_update(
            constraint="uq_role_resource_action",
            set_={"allowed": pg_insert(RoleScopeFilter).excluded.allowed}
        )
        await db.execute(stmt)
        await db.commit()
        return {
            "seeded": len(DEFAULT_ROLE_PERMISSIONS),
            "message": "DEFAULT_ROLE_PERMISSIONS propagado ao banco com sucesso",
        }
    except Exception as exc:
        logger.error("[RBAC] seed_permissions error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/permissions/check", summary="Verifica se role pode executar action em resource")
async def check_permission(
    role: str = Query(..., description="Role do usuario"),
    resource: str = Query(..., description="Recurso a acessar"),
    action: str = Query(..., description="Acao a executar"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna allowed=True/False.
    Fail-closed: role/resource/action desconhecidos retornam allowed=False.
    """
    from app.shared.rbac.scope_filter_service import get_scope_filter_service
    svc = get_scope_filter_service()
    allowed = await svc.is_allowed(role, resource, action, db)
    return {
        "role": role,
        "resource": resource,
        "action": action,
        "allowed": allowed,
    }


@router.put("/permissions/{permission_id}", summary="Atualiza allowed/description de uma permissao")
async def update_permission(
    permission_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza campos allowed e/ou description.
    Invalida cache Redis apos update.
    Requer: wedotalent_admin (TODO: adicionar gate quando auth disponivel).
    """
    try:
        from lia_models.role_scope_filter import RoleScopeFilter
        from app.shared.rbac.scope_filter_service import get_scope_filter_service

        stmt = select(RoleScopeFilter).where(
            RoleScopeFilter.id == uuid.UUID(permission_id)
        )
        record = (await db.execute(stmt)).scalars().first()

        if not record:
            raise HTTPException(status_code=404, detail="Permissao nao encontrada")

        if "allowed" in body:
            record.allowed = bool(body["allowed"])
        if "description" in body:
            record.description = str(body["description"])

        await db.commit()
        await db.refresh(record)

        # Invalida cache
        svc = get_scope_filter_service()
        await svc.invalidate_cache(role=record.role)

        return {
            "id": str(record.id),
            "role": record.role,
            "resource": record.resource,
            "action": record.action,
            "allowed": record.allowed,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[RBAC] update_permission error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
