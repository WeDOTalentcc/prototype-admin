"""
FastAPI dependency — Token Budget check (Sprint A / André R6).

Uso:
    @router.post("/chat")
    async def chat_endpoint(
        ...,
        _budget: None = Depends(require_token_budget),
    ):
        ...

O dependency extrai company_id do usuário autenticado,
verifica o budget Redis e bloqueia (HTTP 429) se esgotado.
Falha silenciosa se Redis/DB indisponíveis.
"""
import logging

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user_or_demo
from app.services.token_budget_service import check_budget, get_plan_for_company

logger = logging.getLogger(__name__)


async def require_token_budget(
    current_user=Depends(get_current_user_or_demo),
) -> None:
    """
    FastAPI dependency que bloqueia a request se o budget diário de tokens
    da empresa estiver esgotado.

    Retorna None (não bloqueia) se:
    - Redis indisponível
    - Plano não encontrado
    - Qualquer erro interno (graceful degradation)

    Lança HTTP 429 se budget_exhausted=True.
    """
    company_id: str | None = None
    try:
        company_id = str(
            getattr(current_user, "company_id", None)
            or getattr(current_user, "organization_id", None)
            or ""
        )
        if not company_id:
            return  # sem company_id → não bloquear

        plan_code = await get_plan_for_company(company_id)
        allowed, used_today, daily_limit = await check_budget(company_id, plan_code)

        if not allowed:
            logger.warning(
                "[TokenBudgetDep] Budget esgotado company_id=%s used=%d limit=%d plan=%s",
                company_id, used_today, daily_limit, plan_code,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "budget_exhausted",
                    "message": (
                        f"Limite diário de uso de IA atingido "
                        f"({used_today:,} / {daily_limit:,} tokens). "
                        "O budget será renovado à meia-noite UTC."
                    ),
                    "used_today": used_today,
                    "daily_limit": daily_limit,
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        # Nunca bloquear por falha técnica — graceful degradation
        logger.warning(
            "[TokenBudgetDep] Erro ao verificar budget (company_id=%s) — continuando: %s",
            company_id, exc,
        )
