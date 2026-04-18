"""
Admin — Token Budget endpoints (Sprint A / André R6/P2).

GET  /api/v1/admin/token-budget/{company_id}
POST /api/v1/admin/token-budget/{company_id}/reset   (forçar reset — apenas superadmin)

Requer autenticação de admin.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.shared.observability.token_budget_service import (
    check_budget,
    get_budget_status,
)
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

router = APIRouter(prefix="/admin/token-budget", tags=["admin-token-budget"])
logger = logging.getLogger(__name__)


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
    company_id: _DualId,
    plan_code: str | None = Query(
        default=None,
        description="Código do plano da assinatura ativa. Se omitido, usa fallback (starter/10k).",
    ),
    current_user=Depends(get_current_user),
):
    """
    Retorna status completo do budget de tokens LLM para a empresa.

    Usado no dashboard admin para monitorar consumo por tenant.
    """
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
    company_id: _DualId,
    plan_code: str | None = Query(default=None),
    current_user=Depends(get_current_user),
):
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

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
