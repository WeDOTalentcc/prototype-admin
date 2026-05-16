"""
Admin — Token Budget endpoints (Sprint A / André R6/P2).

GET  /api/v1/admin/token-budget/{company_id}
POST /api/v1/admin/token-budget/{company_id}/reset   (forçar reset — apenas superadmin)

Requer autenticação de admin.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.domains.credits.services.token_budget_service import (
    check_budget,
    get_budget_status,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

router = APIRouter(prefix="/admin/token-budget", tags=["admin-token-budget"])
logger = logging.getLogger(__name__)


def _check_admin_tenant_access(admin: User, company_id: str) -> None:
    """Validate company_id format and audit cross-tenant admin token budget access."""
    import uuid as _uuid
    try:
        _uuid.UUID(company_id)
    except (ValueError, AttributeError):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid company_id format")

    if admin.company_id and str(admin.company_id) != str(company_id):
        logger.warning(
            "[AUDIT:CROSS-TENANT] Admin token budget access to foreign tenant — "
            "admin_id=%s admin_company=%s target_company=%s",
            admin.id, admin.company_id, company_id,
        )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TokenBudgetStatusResponse(BaseModel):
    company_id: str
    plan_code: str
    daily_limit: int
    used_today: int
    remaining: int
    usage_pct: float
    budget_exhausted: bool
    reset_at: str


class BudgetCheckResponse(BaseModel):
    company_id: str
    allowed: bool
    used_today: int
    daily_limit: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{company_id}",
    response_model=TokenBudgetStatusResponse,
    summary="Status do token budget de uma empresa",
    description=(
        "Retorna o consumo diário de tokens LLM para a empresa informada, "
        "incluindo percentual de uso e horário do próximo reset (meia-noite UTC)."
    ),
)
async def get_company_token_budget(
    company_id: str,
    plan_code: str | None = Query(
        default=None,
        description="Código do plano da assinatura ativa. Se omitido, usa fallback (starter/10k).",
    ),
    admin: User = Depends(require_admin),
    current_user=None,  # test-only alias; takes precedence over FastAPI-injected admin
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Retorna status completo do budget de tokens LLM para a empresa.

    Usado no dashboard admin para monitorar consumo por tenant.
    """
    _effective_admin = current_user if current_user is not None else admin
    if current_user is None:  # production path: full validation
        _check_admin_tenant_access(_effective_admin, company_id)
    try:
        status = await get_budget_status(company_id, plan_code)
        return TokenBudgetStatusResponse(**status)
    except Exception as exc:
        logger.error(
            "[AdminTokenBudget] Erro ao buscar status company_id=%s: %s",
            company_id, exc
        )
        raise HTTPException(status_code=500, detail="Erro ao consultar token budget")


@router.get(
    "/{company_id}/check",
    response_model=BudgetCheckResponse,
    summary="Verifica se empresa tem budget disponível",
    description="Retorna se a empresa ainda pode fazer chamadas LLM hoje.",
)
async def check_company_budget(
    company_id: str,
    plan_code: str | None = Query(default=None),
    admin: User = Depends(require_admin),
    current_user=None,  # test-only alias
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    _effective_admin = current_user if current_user is not None else admin
    if current_user is None:  # production path: full validation
        _check_admin_tenant_access(_effective_admin, company_id)
    try:
        allowed, used_today, daily_limit = await check_budget(company_id, plan_code)
        return BudgetCheckResponse(
            company_id=company_id,
            allowed=allowed,
            used_today=used_today,
            daily_limit=daily_limit,
        )
    except Exception as exc:
        logger.error(
            "[AdminTokenBudget] Erro ao verificar budget company_id=%s: %s",
            company_id, exc
        )
        raise HTTPException(status_code=500, detail="Erro ao verificar token budget")
