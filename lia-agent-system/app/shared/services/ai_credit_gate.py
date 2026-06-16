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

ADR-WT-2027 BYOK Strategy (Opcao C, 2026-05-22) — Bug B3 fix:
- Antes: gate bloqueava tenants BYOK quando current_usage >= monthly_limit,
  mesmo tenant pagando direto OpenAI/Anthropic. UI prometia unmetered, backend
  silenciosamente bloqueava (credibility break).
- Depois: BYOK ativo (tenant_llm_configs.providers.{provider}.api_key existe)
  switcha gate para track-only mode. Loga consumption (LGPD Art. 37), nunca
  bloqueia. Tenant configurável soft_cap emite metric `byok_soft_cap_breached_total`
  para alarm Grafana, ainda assim NUNCA bloqueia.

PLUS: Fix import path bug. Existing import `from app.models.observability`
falhava silenciosamente (AiCreditsBalance vive em `app.models.ai_consumption`)
e caia no fail_safe ALLOW. Gate era no-op silencioso. Now corrected.

## Pattern de uso (qualquer caller LLM)

    from app.shared.services.ai_credit_gate import check_credit_budget, AICreditExhausted

    try:
        result = await check_credit_budget(
            db, company_id, estimated_tokens=2000, service="anthropic_sdk"
        )
        # result["byok"] = True -> track-only, gate didn't block
        # result["byok"] = False -> WeDo-paid, hard block enforced
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

import hashlib
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
    provider: Optional[str] = None,
    byok_active: Optional[bool] = None,
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
            "voice_whisper", "multimodal_vision", etc. Tambem usado pra
            inferir provider quando `provider` param e None (BYOK detection).
        provider: explicit provider name ("anthropic" / "openai" / "gemini").
            Quando informado, sobrescreve a inferência por `service`. Usado
            para BYOK detection per-provider.
        byok_active: override explicito (testing only). Quando None (default),
            o gate detecta automaticamente via `is_byok_active`. Quando True,
            forca track-only mode sem fazer DB lookup.

    Returns dict on success:
        - `byok` (bool): True iff tenant em track-only mode (BYOK ativo)
        - `monthly_limit` (int): teto WeDo-paid (irrelevante quando byok=True)
        - `current_usage` (int): consumption atual
        - `remaining` (int|None): tokens restantes (None quando byok=True
          porque unlimited do ponto de vista WeDo)
        - `soft_cap` (int|None, opcional): tenant-managed BYOK soft cap

    Raises:
        AICreditExhausted: somente quando `byok_active=False` e
            `projected >= monthly_limit`. Tenants BYOK NUNCA disparam esta
            exception (track-only).
    """
    # P1.AIC2: normalize audio duration → token-equivalents so callers can
    # use the same budget ledger regardless of price model. The constant
    # mirrors `_WHISPER_TOKEN_EQ_PER_MINUTE` in `app/shared/llm_bootstrap.py`.
    if audio_duration_seconds is not None and audio_duration_seconds > 0:
        estimated_tokens = int(estimated_tokens) + int(
            round((float(audio_duration_seconds) / 60.0) * 2000)
        )

    # ADR-WT-2027 BYOK detection. When byok_active is provided explicitly
    # (testing path), skip the lookup; otherwise consult the canonical
    # detector. Fail-safe: detection error -> (False, provider) (WeDo-paid).
    detected_provider = provider
    if byok_active is None:
        try:
            from app.shared.services.byok_detector import is_byok_active as _detect

            byok_active, detected_provider = await _detect(
                db, company_id, service=service, provider=provider
            )
        except Exception as exc:  # noqa: BLE001 -- fail-safe to WeDo-paid
            logger.warning(
                "BYOK detection helper raised (fail-safe WeDo-paid): %s",
                exc,
                exc_info=True,
            )
            byok_active = False

    try:
        from sqlalchemy import select
        # ADR-WT-2027 fix: AiCreditsBalance is exported from
        # `app.models.ai_consumption` (re-export shim of `lia_models.ai_consumption`),
        # NOT from `app.models.observability`. The previous import was a latent
        # bug that made every call fall into fail_safe ALLOW. Confirmed via
        # `from app.models.observability import AiCreditsBalance` raising
        # ImportError at runtime.
        from app.models.ai_consumption import AiCreditsBalance

        result = await db.execute(
            select(AiCreditsBalance).where(
                AiCreditsBalance.company_id == company_id
            )
        )
        balance = result.scalar_one_or_none()

        if not balance:
            # Unconfigured tenant -- preserve historic behavior (allow but flag).
            # BYOK still respected (track-only also doesn't need balance row).
            return {
                "monthly_limit": 0,
                "current_usage": 0,
                "remaining": 0 if not byok_active else None,
                "unconfigured": True,
                "byok": bool(byok_active),
            }

        monthly_limit = int(getattr(balance, "monthly_limit", 0))
        current_usage = int(getattr(balance, "current_usage", 0))
        projected = current_usage + estimated_tokens
        soft_cap = getattr(balance, "byok_soft_cap", None)
        soft_cap_int = int(soft_cap) if soft_cap is not None else 0

        if byok_active:
            # ADR-WT-2027 Opcao C: TRACK-ONLY MODE.
            # Gate NUNCA bloqueia BYOK tenants -- they pay provider direct.
            # Counter helps Grafana visibility (vs WeDo-paid distribution).
            _emit_track_only_metric(service=service, provider=detected_provider)

            if soft_cap_int > 0 and projected >= soft_cap_int:
                # Soft cap breached -- alarm, but DO NOT raise.
                _emit_soft_cap_breached_metric(
                    company_id,
                    service=service,
                    provider=detected_provider,
                )
                logger.warning(
                    "BYOK soft cap reached company=%s service=%s provider=%s "
                    "usage=%d projected=%d cap=%d (track-only, NOT blocking)",
                    company_id, service, detected_provider,
                    current_usage, projected, soft_cap_int,
                )

            return {
                "monthly_limit": monthly_limit,
                "current_usage": current_usage,
                "remaining": None,  # unlimited from WeDo perspective
                "byok": True,
                "soft_cap": soft_cap_int if soft_cap_int > 0 else None,
                "provider": detected_provider,
            }

        # PATH TRADICIONAL (WeDo-paid) -- hard block as before.
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
            "remaining": max(0, monthly_limit - projected),
            "byok": False,
            "provider": detected_provider,
        }
    except AICreditExhausted:
        raise
    except Exception as exc:
        if fail_safe:
            logger.warning(
                "WT-2022 P0.AIC1: credit budget check failed for %s (fail-safe ALLOW): %s",
                company_id, exc,
            )
            return {"error": str(exc)[:200], "fail_safe": True, "byok": bool(byok_active)}
        raise


def _hash_cid(company_id: str) -> str:
    return hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:12]


def _emit_exhausted_metric(company_id: str, *, service: Optional[str] = None) -> None:
    """Best-effort Prometheus counter emit. Non-blocking."""
    try:
        from app.shared.observability.canary_metrics import ai_credit_exhausted_total
        if ai_credit_exhausted_total is None:
            return
        cid_hash = _hash_cid(company_id)
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


def _emit_track_only_metric(
    *, service: Optional[str] = None, provider: Optional[str] = None
) -> None:
    """Best-effort emit for byok_track_only_total. Non-blocking."""
    try:
        from app.shared.observability.canary_metrics import byok_track_only_total
        if byok_track_only_total is None:
            return
        try:
            byok_track_only_total.labels(
                service=service or "unknown",
                provider=provider or "unknown",
            ).inc()
        except (TypeError, ValueError):
            try:
                byok_track_only_total.labels(service=service or "unknown").inc()
            except Exception:
                pass
    except Exception:
        pass


def _emit_soft_cap_breached_metric(
    company_id: str,
    *,
    service: Optional[str] = None,
    provider: Optional[str] = None,
) -> None:
    """Best-effort emit for byok_soft_cap_breached_total. Non-blocking."""
    try:
        from app.shared.observability.canary_metrics import (
            byok_soft_cap_breached_total,
        )
        if byok_soft_cap_breached_total is None:
            return
        cid_hash = _hash_cid(company_id)
        try:
            byok_soft_cap_breached_total.labels(
                company_id_hash=cid_hash,
                service=service or "unknown",
                provider=provider or "unknown",
            ).inc()
        except (TypeError, ValueError):
            try:
                byok_soft_cap_breached_total.labels(
                    company_id_hash=cid_hash, service=service or "unknown"
                ).inc()
            except Exception:
                pass
    except Exception:
        pass
