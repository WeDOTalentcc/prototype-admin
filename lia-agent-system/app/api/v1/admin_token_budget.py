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
from app.shared.admin.cross_tenant_session import (
    cross_tenant_session,
    require_superadmin,
)
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

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
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    plan_code: str | None = Query(
        default=None,
        description="Código do plano da assinatura ativa. Se omitido, usa fallback (starter/10k).",
    ),
    admin: User = Depends(require_admin),
    current_user=None,  # test-only alias; takes precedence over FastAPI-injected admin
):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required.
    # Task #1148: cross-tenant lookups (admin queries a foreign tenant) are
    # gated server-side by ``require_superadmin`` (called explicitly in the
    # ``is_cross_tenant`` branch so non-superadmins get HTTP 403) and audited
    # via ``cross_tenant_session``. Same-tenant lookups keep the legacy
    # ``require_admin`` behavior so tenant admins are not regressed.
    #
    # NOTE: ``require_company_id_strict_match`` was intentionally REMOVED here
    # because it would 403 every cross-tenant request before the handler runs,
    # making the audited bypass path unreachable in production.
    """
    Retorna status completo do budget de tokens LLM para a empresa.

    Usado no dashboard admin para monitorar consumo por tenant.
    """
    _effective_admin = current_user if current_user is not None else admin
    if current_user is None:  # production path: full validation
        _check_admin_tenant_access(_effective_admin, company_id)
    try:
        actor_company = str(getattr(_effective_admin, "company_id", "") or "")
        # SECURITY: missing/empty actor tenant context is treated as
        # cross-tenant (fail-closed) — otherwise an admin whose JWT lacks a
        # ``company_id`` could query arbitrary tenants without superadmin
        # gating or audit. Same-tenant fast-path requires a NON-empty match.
        is_cross_tenant = (not actor_company) or actor_company != str(company_id)
        if is_cross_tenant:
            # Enforce platform-superadmin server-side ONLY for the cross-tenant
            # path, then enter the audited bypass context.
            #
            # NOTE: ``get_budget_status`` below is Redis-only and does NOT
            # consume ``bypass_db``. The bypass context is still required
            # because (a) it emits the start/end ``audit_logs`` rows that
            # SOX/EU-AI-Act traceability depends on and (b) the cross-tenant
            # ``SELECT 1`` below proves the foreign company exists under
            # bypassed RLS, which is the operation that needs auditing.
            await require_superadmin(current_user=_effective_admin)
            from sqlalchemy import text as _sa_text
            async with cross_tenant_session(
                reason="admin_token_budget_status",
                audit_user_id=str(getattr(_effective_admin, "id", "") or ""),
            ) as bypass_db:
                # Use the bypass session for a real cross-tenant SELECT —
                # validate the target tenant exists under the postgres role
                # (RLS would hide it from the actor's own session).
                await bypass_db.execute(
                    _sa_text("SELECT 1 FROM companies WHERE id = :cid"),
                    {"cid": str(company_id)},
                )
                status = await get_budget_status(company_id, plan_code)
        else:
            status = await get_budget_status(company_id, plan_code)
        return TokenBudgetStatusResponse(**status)
    except HTTPException:
        raise
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
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    plan_code: str | None = Query(default=None),
    admin: User = Depends(require_admin),
    current_user=None,  # test-only alias
):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required.
    # Task #1148: cross-tenant lookups gated by ``require_superadmin`` +
    # audited via ``cross_tenant_session``. Same-tenant lookups keep the
    # legacy ``require_admin`` behavior (no regression for tenant admins).
    # ``require_company_id_strict_match`` removed — see ``get_company_token_budget``
    # for the rationale (it would 403 the audited bypass path).
    _effective_admin = current_user if current_user is not None else admin
    if current_user is None:  # production path: full validation
        _check_admin_tenant_access(_effective_admin, company_id)
    try:
        actor_company = str(getattr(_effective_admin, "company_id", "") or "")
        # SECURITY: see ``get_company_token_budget`` — empty actor tenant
        # context is fail-closed (treated as cross-tenant).
        is_cross_tenant = (not actor_company) or actor_company != str(company_id)
        if is_cross_tenant:
            await require_superadmin(current_user=_effective_admin)
            async with cross_tenant_session(
                reason="admin_token_budget_check",
                audit_user_id=str(getattr(_effective_admin, "id", "") or ""),
            ):
                allowed, used_today, daily_limit = await check_budget(company_id, plan_code)
        else:
            allowed, used_today, daily_limit = await check_budget(company_id, plan_code)
        return BudgetCheckResponse(
            company_id=company_id,
            allowed=allowed,
            used_today=used_today,
            daily_limit=daily_limit,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "[AdminTokenBudget] Erro ao verificar budget company_id=%s: %s",
            company_id, exc
        )
        raise HTTPException(status_code=500, detail="Erro ao verificar token budget")

reorder_collection_before_item(router)
