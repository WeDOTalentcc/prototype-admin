"""Canonical BYOK (Bring-Your-Own-Key) detection per-provider.

ADR-WT-2027 BYOK Strategy (Opcao C, decidido por Paulo 2026-05-22):
  When tenant supplies own API key for a provider (anthropic / openai /
  gemini), WeDOTalent AI credit gate switches to **track-only mode**:
  - We still record usage in ``ai_consumption`` (LGPD Art. 37 compliance
    + audit trail + Grafana visibility).
  - We DO NOT raise ``AICreditExhausted`` even if ``current_usage`` exceeds
    ``monthly_limit`` (tenant pays the provider directly).
  - Tenant can optionally configure ``byok_soft_cap`` for self-managed
    spend alarm (emits ``byok_soft_cap_breached_total`` metric, never
    blocks).

Default WeDo-paid path is unchanged: hard block when ``projected
>= monthly_limit``. Fail-safe: if BYOK detection raises (DB/cache error),
we assume WeDo-paid (safer -- fail-closed against accidental cost leak).

REGRA 4 (fail-loud em config invalido, fail-safe em detection error):
  - Returns ``(False, provider)`` on detection error (NOT raises) so the
    gate continues to enforce.
  - Logs the exception with ``exc_info=True`` so Grafana/Sentry catches.

Pattern de uso (call site):

    from app.shared.services.byok_detector import is_byok_active

    byok_active, provider = await is_byok_active(
        db, company_id, service="anthropic_sdk"
    )
    if byok_active:
        # track-only mode -- log but don't block
        ...

Single source of truth -- used by:
- ``app/shared/services/ai_credit_gate.py:check_credit_budget`` (gate skip)
- ``app/shared/llm_bootstrap.py`` (monkey-patch reconciliation path)
- Future BYOK soft-cap endpoint at ``/api/v1/ai-credits/byok-soft-cap``

Multi-tenancy: company_id is mandatory. Empty/None returns
``(False, None)`` (treated as WeDo-paid, gate enforces normally).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Service identifier -> provider inference. Mirrors _SERVICE_TO_PROVIDER
# usage across LLM bootstrap. Keep in sync when adding a new service.
_SERVICE_TO_PROVIDER: dict[str, str] = {
    # OpenAI sub-services
    "voice_realtime": "openai",
    "voice_whisper_stt": "openai",
    "voice_whisper": "openai",
    "voice_tts": "openai",
    "openai_sdk": "openai",
    # Anthropic sub-services
    "wsi_question_generation": "anthropic",
    "candidate_ranking": "anthropic",
    "cv_pre_wrf_filter": "anthropic",
    "intake_extraction": "anthropic",
    "anthropic_sdk": "anthropic",
    "agent_quality_evaluator": "anthropic",
    "wizard_supervisor_classifier": "anthropic",
    # Multimodal -- Anthropic default but tenant override possible
    "multimodal_vision": "anthropic",
    "multimodal_service": "anthropic",
    # Gemini sub-services
    "gemini_sdk": "gemini",
    "google_genai": "gemini",
}


async def is_byok_active(
    db: "AsyncSession",
    company_id: str,
    *,
    service: str | None = None,
    provider: str | None = None,
) -> tuple[bool, str | None]:
    """Detect whether BYOK is active for tenant + provider.

    Args:
        db: AsyncSession scoped to tenant. Currently unused by direct DB
            read (``get_tenant_llm_config`` opens its own session via
            ``AsyncSessionLocal``) but kept in signature for future
            session-scoped query optimization + symmetry with other gate
            helpers.
        company_id: tenant scoping (REGRA ZERO -- required, empty returns False).
        service: service identifier from caller (e.g. ``"anthropic_sdk"``,
            ``"voice_realtime"``). Used to infer provider when ``provider``
            param is None. See ``_SERVICE_TO_PROVIDER`` for canonical map.
        provider: explicit provider name (``"anthropic"`` / ``"openai"`` /
            ``"gemini"``). Takes precedence over ``service`` inference.

    Returns:
        ``(byok_active, provider_resolved)`` tuple where:
        - ``byok_active`` = True iff tenant has a non-empty API key stored
          for the resolved provider in ``tenant_llm_configs.providers``.
        - ``provider_resolved`` = the provider used for the lookup, or
          ``None`` when both ``provider`` and ``service`` failed to resolve.

    Fail-safe contract:
        Any exception during config read returns ``(False, provider)`` --
        assumes WeDo-paid (gate enforces normally). The exception is logged
        at WARNING with ``exc_info=True`` so it surfaces in Sentry/Grafana
        WITHOUT leaking money silently to a misdetected BYOK tenant.
    """
    if not company_id:
        return (False, None)

    # Service -> provider inference when provider not explicit.
    if provider is None and service:
        provider = _SERVICE_TO_PROVIDER.get(service)

    if not provider:
        # No known provider -> assume WeDo-paid (default safe).
        return (False, None)

    try:
        from app.shared.tenant_llm_context import get_tenant_llm_config

        config = await get_tenant_llm_config(company_id)
        if not config:
            return (False, provider)

        providers_config = config.get("providers") or {}
        provider_data = providers_config.get(provider) or {}
        api_key = provider_data.get("api_key")

        if (
            api_key
            and isinstance(api_key, str)
            and len(api_key.strip()) > 0
            and "..." not in api_key  # masked key returned by GET endpoint
        ):
            return (True, provider)
        return (False, provider)
    except Exception as exc:  # noqa: BLE001 -- fail-safe
        logger.warning(
            "BYOK detection failed for company=%s provider=%s (fail-safe WeDo-paid): %s",
            company_id,
            provider,
            exc,
            exc_info=True,
        )
        return (False, provider)
