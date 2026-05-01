"""
FastAPI dependency — Token Budget check (Sprint A / André R6).

Uso:
    @router.post("/chat")
    async def chat_endpoint(
        ...,
        _budget: None = Depends(require_token_budget),
    ):
        ...

    @router.post("/agent")
    async def agent_endpoint(
        ...,
        _req_budget: None = Depends(require_request_budget),
    ):
        ...

O dependency extrai company_id do usuário autenticado,
verifica o budget Redis e bloqueia (HTTP 429) se esgotado.
Falha silenciosa se Redis/DB indisponíveis.

``require_request_budget`` verifica o ceiling por request individual
antes da chamada LLM (Fase 3).
"""
import logging

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user_or_demo
from app.domains.credits.services.token_budget_service import (
    check_budget,
    check_request_budget,
    check_request_budget_before_llm,
    estimate_request_tokens,
    get_plan_for_company,
)

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
            return

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
        logger.warning(
            "[TokenBudgetDep] Erro ao verificar budget (company_id=%s) — continuando: %s",
            company_id, exc,
        )


async def require_request_budget(
    current_user=Depends(get_current_user_or_demo),
    prompt: str = "",
    system_prompt: str | None = None,
    agent_type: str | None = None,
    expected_output_tokens: int | None = None,
) -> None:
    """
    FastAPI dependency que bloqueia a request se os tokens estimados
    excederem o ceiling por request individual do plano.

    Lança HTTP 413 (Payload Too Large) com detalhes do ceiling e estimativa.
    Falha silenciosa se Redis/DB indisponíveis (graceful degradation).
    """
    company_id: str | None = None
    user_id: str | None = None
    try:
        company_id = str(
            getattr(current_user, "company_id", None)
            or getattr(current_user, "organization_id", None)
            or ""
        )
        user_id = str(getattr(current_user, "id", None) or "")
        if not company_id:
            return

        if not prompt and not system_prompt:
            return

        plan_code = await get_plan_for_company(company_id)
        estimated = estimate_request_tokens(
            prompt, system_prompt, expected_output_tokens
        )
        allowed, estimated_tokens, ceiling = check_request_budget(
            plan_code,
            estimated,
            agent_type=agent_type,
            company_id=company_id,
            user_id=user_id,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "request_too_large",
                    "message": (
                        f"Request excede o limite de tokens por chamada "
                        f"({estimated_tokens:,} estimados / {ceiling:,} permitidos). "
                        "Reduza o tamanho do prompt ou contexto."
                    ),
                    "estimated_tokens": estimated_tokens,
                    "ceiling": ceiling,
                    "agent_type": agent_type,
                    "plan_code": plan_code,
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "[TokenBudgetDep] Erro ao verificar request budget "
            "(company_id=%s) — continuando: %s",
            company_id, exc,
        )


