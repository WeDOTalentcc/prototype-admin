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

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from libs.models.lia_models.retention_policy import CompanyRetentionPolicy
from sqlalchemy import select

router = APIRouter()


class RetentionPolicyRequest(BaseModel):
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
async def update_retention_policy(
    body: RetentionPolicyRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    company_id = current_user.company_id

    # Buscar política existente ou criar nova
    result = await db.execute(
        select(CompanyRetentionPolicy).where(
            CompanyRetentionPolicy.company_id == company_id
        )
    )
    policy = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if policy is None:
        policy = CompanyRetentionPolicy(
            id=str(uuid4()),
            company_id=company_id,
            retention_months=body.retention_months,
            auto_anonymize=body.auto_anonymize,
            activated_at=now if body.auto_anonymize else None,
            activated_by=str(current_user.id) if body.auto_anonymize else None,
        )
        db.add(policy)
    else:
        # Registrar ativação pela primeira vez
        if body.auto_anonymize and not policy.auto_anonymize:
            policy.activated_at = now
            policy.activated_by = str(current_user.id)
        elif not body.auto_anonymize and policy.auto_anonymize:
            # Desativação — não apaga histórico de quando foi ativado
            pass

        policy.retention_months = body.retention_months
        policy.auto_anonymize = body.auto_anonymize

    await db.commit()
    await db.refresh(policy)

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
):
    """Retorna a política de retenção atual da empresa."""
    result = await db.execute(
        select(CompanyRetentionPolicy).where(
            CompanyRetentionPolicy.company_id == current_user.company_id
        )
    )
    policy = result.scalar_one_or_none()

    if policy is None:
        # Retornar defaults (política não configurada = off)
        return RetentionPolicyResponse(
            company_id=current_user.company_id,
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
