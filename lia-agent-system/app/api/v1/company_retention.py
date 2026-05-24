"""
ARQUIVO NOVO: app/api/v1/company_retention.py

Endpoint para configurar política de retenção de dados por empresa.
Admin/owner apenas.

COMO APLICAR:
  1. Copiar para app/api/v1/company_retention.py
  2. Registrar em app/main.py:
     from app.api.v1.company_retention import router as retention_router
     app.include_router(retention_router, prefix="/api/v1", tags=["Company Settings"])
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db, get_tenant_db
from app.domains.company.repositories.company_retention_repository import CompanyRetentionRepository
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter()


class RetentionPolicyRequest(WeDoBaseModel):
    retention_months: int = Field(
        default=24,
        ge=6,
        le=120,
        description="Meses para manter dados de candidatos não contratados (6–120 meses)",
    )
    auto_anonymize: bool = Field(
        default=False,
        description="Ativar anonimização automática. OFF por default (opt-in).",
    )


class RetentionPolicyResponse(BaseModel):
    company_id: str
    retention_months: int
    auto_anonymize: bool
    activated_at: datetime | None
    activated_by: str | None
    last_cleanup_at: datetime | None
    last_cleanup_count: int | None
    message: str


@router.patch("/company/retention-policy", response_model=RetentionPolicyResponse)
# TODO(phase2): extract to repository — company retention data
async def update_retention_policy(
    body: RetentionPolicyRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Configura a política de retenção de dados da empresa.

    Requer role: admin ou owner.
    auto_anonymize=True ativa a anonimização mensal de candidatos não contratados
    após retention_months meses.

    AVISO: uma vez ativado e o job executado, a anonimização é IRREVERSÍVEL.
    Os dados pessoais são zerados permanentemente.
    """
    # Verificar permissão (apenas admin/owner)
    if not hasattr(current_user, "role") or current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar esta política.")

    # P1.1 (Onda 4.2a 2026-05-23): removido overwrite. company_id JA vem do JWT (Depends require_company_id) — fonte autoritativa unica.

    repo = CompanyRetentionRepository(db)
    policy = await repo.upsert(
        company_id=company_id,
        retention_months=body.retention_months,
        auto_anonymize=body.auto_anonymize,
        activated_by=str(current_user.id),
    )

    return RetentionPolicyResponse(
        company_id=policy.company_id,
        retention_months=policy.retention_months,
        auto_anonymize=policy.auto_anonymize,
        activated_at=policy.activated_at,
        activated_by=policy.activated_by,
        last_cleanup_at=policy.last_cleanup_at,
        last_cleanup_count=policy.last_cleanup_count,
        message=(
            "Política de retenção atualizada. "
            "A anonimização automática está ATIVA e rodará mensalmente."
            if policy.auto_anonymize
            else "Política de retenção atualizada. Anonimização automática DESATIVADA."
        ),
    )


@router.get("/company/retention-policy", response_model=RetentionPolicyResponse)
async def get_retention_policy(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Retorna a política de retenção atual da empresa."""
    repo = CompanyRetentionRepository(db)
    policy = await repo.get_by_company_id(company_id)

    if policy is None:
        # Retornar defaults (política não configurada = off)
        return RetentionPolicyResponse(
            company_id=company_id,
            retention_months=24,
            auto_anonymize=False,
            activated_at=None,
            activated_by=None,
            last_cleanup_at=None,
            last_cleanup_count=None,
            message="Nenhuma política configurada. Padrão: 24 meses, anonimização desativada.",
        )

    return RetentionPolicyResponse(
        company_id=policy.company_id,
        retention_months=policy.retention_months,
        auto_anonymize=policy.auto_anonymize,
        activated_at=policy.activated_at,
        activated_by=policy.activated_by,
        last_cleanup_at=policy.last_cleanup_at,
        last_cleanup_count=policy.last_cleanup_count,
        message="Política carregada com sucesso.",
    )
