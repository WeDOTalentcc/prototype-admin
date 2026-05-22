"""
WT-2022 P0.AIC1: Helper canonical pra check ai_credits_balance antes de LLM call.

Decisão Paulo 2026-05-21: require_token_budget dependency cobre <5% dos LLM callers
(apenas 4 chat endpoints). Agents/orchestrator/screening/scoring/etc chamam LLM
SEM checar budget → overage descontrolado.

Wave 3 audit (2026-05-21) revelou 7 services bypassando llm_factory chokepoint:
intake_extractor, voice_service, interview_scheduling_nodes, multimodal_service,
agent_quality_evaluator, wsi_question_generator (fallback paths), wizard_supervisor_classifier.

Fix definitivo (2026-05-22): monkey-patch global em llm_bootstrap.py envolve SDK
constructors (anthropic, openai, google.genai) com pre-call gate. Caller-side
context propagation via ContextVar _current_company_id (já populado pelo auth middleware).

## Pattern de uso (qualquer caller LLM)

    from app.shared.services.ai_credit_gate import check_credit_budget, AICreditExhausted

    try:
        await check_credit_budget(db, company_id, estimated_tokens=2000)
    except AICreditExhausted as exc:
        # decidir: bloquear, fila, downgrade pra modelo cheaper, etc.
        raise HTTPException(429, str(exc))

    # ...prosseguir com LLM call

## Sites canonical wired

- `app/orchestrator/main_orchestrator.py:367` — entry-point principal (defense-in-depth)
- `app/orchestrator/agentic_loop.py:104` — agentic tool loop (defense-in-depth)
- `app/shared/providers/llm_factory.py:233` — factory chokepoint (defense-in-depth)
- `app/shared/llm_bootstrap.py` — **UNIVERSAL via SDK monkey-patch** (Wave 3 fix)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AICreditExhausted(Exception):
    """Raised when company ai_credits_balance.current_usage >= monthly_limit."""

    def __init__(
        self,
        message: str,
        *,
        company_id: Optional[str] = None,
        remaining: Optional[int] = None,
        service: Optional[str] = None,
    ):
        super().__init__(message)
        self.company_id = company_id
        self.remaining = remaining
        self.service = service


async def check_credit_budget(
    db: "AsyncSession",
    company_id: str,
    *,
    estimated_tokens: int = 0,
    audio_duration_seconds: Optional[float] = None,
    fail_safe: bool = True,
    service: Optional[str] = None,
) -> dict:
    """Check ai_credits_balance per company. Raise AICreditExhausted se esgotado.

    Args:
        db: AsyncSession
        company_id: tenant scoping
        estimated_tokens: opcional, soma ao current_usage pra projeção forward.
            Use para LLM calls clássicos (chat completions, messages.create).
        audio_duration_seconds: opcional (P1.AIC2, 2026-05-22). Quando informado,
            é convertido para token-equivalents (Whisper $0.006/min ≈ 2000
            token-eq/min @ Claude $3/M input baseline) e somado ao
            estimated_tokens. Use para Whisper STT direct-call sites. Para
            calls via openai.AsyncOpenAI.audio.transcriptions.create, o
            monkey-patch no llm_bootstrap deriva a duração do payload bytes
            sem precisar deste param.
        fail_safe: True default — se DB error, ALLOW (não bloqueia em outage Redis/DB)
        service: identificador de domínio chamador (para métricas/audit). Ex:
            "intake_extractor", "wsi_question_generator", "anthropic_sdk",
            "voice_whisper", "multimodal_vision", etc.

    Returns dict {monthly_limit, current_usage, remaining} on success.
    """
    # P1.AIC2: normalize audio duration → token-equivalents so callers can
    # use the same budget ledger regardless of price model. The constant
    # mirrors `_WHISPER_TOKEN_EQ_PER_MINUTE` in `app/shared/llm_bootstrap.py`.
    if audio_duration_seconds is not None and audio_duration_seconds > 0:
        estimated_tokens = int(estimated_tokens) + int(
            round((float(audio_duration_seconds) / 60.0) * 2000)
        )

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
            _emit_exhausted_metric(company_id, service=service)
            raise AICreditExhausted(
                f"AI credit budget exhausted: usage={current_usage} + estimated={estimated_tokens} "
                f">= limit={monthly_limit} (company={company_id})",
                company_id=company_id,
                remaining=max(0, monthly_limit - current_usage),
                service=service,
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


def _emit_exhausted_metric(company_id: str, *, service: Optional[str] = None) -> None:
    """Best-effort Prometheus counter emit. Non-blocking."""
    try:
        import hashlib
        from app.shared.observability.canary_metrics import ai_credit_exhausted_total
        if ai_credit_exhausted_total is None:
            return
        cid_hash = hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:12]
        svc_label = service or "unknown"
        try:
            ai_credit_exhausted_total.labels(
                company_id_hash=cid_hash, service=svc_label
            ).inc()
        except (TypeError, ValueError):
            # Counter declared sem label `service` — fallback compat
            try:
                ai_credit_exhausted_total.labels(company_id_hash=cid_hash).inc()
            except Exception:
                pass
    except Exception:
        pass  # observability é always non-blocking
