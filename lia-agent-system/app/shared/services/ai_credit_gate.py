"""
WT-2022 P0.AIC1: Helper canonical pra check ai_credits_balance antes de LLM call.

Decisão Paulo 2026-05-21: require_token_budget dependency cobre <5% dos LLM callers
(apenas 4 chat endpoints). Agents/orchestrator/screening/scoring/etc chamam LLM
SEM checar budget → overage descontrolado.

Status (2026-05-21):
    ✅ Helper canonical criado (este arquivo)
    ❌ Wire em ~30+ LLM callers fica pra próxima sprint dedicada

## Pattern de uso (qualquer caller LLM)

    from app.shared.services.ai_credit_gate import check_credit_budget, AICreditExhausted

    try:
        await check_credit_budget(db, company_id, estimated_tokens=2000)
    except AICreditExhausted as exc:
        # decidir: bloquear, fila, downgrade pra modelo cheaper, etc.
        raise HTTPException(429, str(exc))

    # ...prosseguir com LLM call

## Sites canonical pra wire (próxima sprint)

- `app/orchestrator/main_orchestrator.py` — entry-point principal
- `app/agents/*` — todos agents que chamam LLM diretamente
- `app/domains/cv_screening/services/wsi_service/*`
- `app/domains/cv_screening/services/pre_wrf_filter_service.py`
- `app/domains/job_creation/services/intake_extractor.py`
- `app/domains/cv_parsing/services/*`
- `app/domains/communication/orchestrator/*`
- `app/domains/ranking/services/*`
- `app/shared/providers/llm_factory.py` (idealmente — single chokepoint)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AICreditExhausted(Exception):
    """Raised when company ai_credits_balance.current_usage >= monthly_limit."""
    pass


async def check_credit_budget(
    db: "AsyncSession",
    company_id: str,
    *,
    estimated_tokens: int = 0,
    fail_safe: bool = True,
) -> dict:
    """Check ai_credits_balance per company. Raise AICreditExhausted se esgotado.

    Args:
        db: AsyncSession
        company_id: tenant scoping
        estimated_tokens: opcional, soma ao current_usage pra projeção forward
        fail_safe: True default — se DB error, ALLOW (não bloqueia em outage Redis/DB)

    Returns dict {monthly_limit, current_usage, remaining} on success.
    """
    try:
        from sqlalchemy import select
        from app.models.observability import AiCreditsBalance

        result = await db.execute(
            select(AiCreditsBalance).where(
                AiCreditsBalance.company_id == company_id
            )
        )
        balance = result.scalar_one_or_none()

        if not balance:
            return {"monthly_limit": 0, "current_usage": 0, "remaining": 0, "unconfigured": True}

        monthly_limit = int(getattr(balance, "monthly_limit", 0))
        current_usage = int(getattr(balance, "current_usage", 0))
        projected = current_usage + estimated_tokens

        if monthly_limit > 0 and projected >= monthly_limit:
            raise AICreditExhausted(
                f"AI credit budget exhausted: usage={current_usage} + estimated={estimated_tokens} "
                f">= limit={monthly_limit} (company={company_id})"
            )

        return {
            "monthly_limit": monthly_limit,
            "current_usage": current_usage,
            "remaining": max(0, monthly_limit - current_usage),
        }
    except AICreditExhausted:
        raise
    except Exception as exc:
        if fail_safe:
            logger.warning(
                "WT-2022 P0.AIC1: credit budget check failed for %s (fail-safe ALLOW): %s",
                company_id, exc,
            )
            return {"error": str(exc)[:200], "fail_safe": True}
        raise
