"""
lia-llm — LLM tier routing, token budget, model config — WeDOTalent.

Lib standalone extraída do monolito lia-agent-system.

Módulos extraídos (zero deps app.*):
    lia_llm.models        — CANONICAL_HAIKU_MODEL, CANONICAL_SONNET_MODEL, CANONICAL_GEMINI_FLASH_MODEL
    lia_llm.model_tier    — ModelTierResolver, resolve_model_tier, DOMAIN_TIER_DEFAULTS, MODEL_TIERS
    lia_llm.safe_response — LLMResponseEnvelope, safe_llm_with_flag, safe_llm_with_flag_async, LLMFailureMode

Módulos shim (monolito-dependentes, disponíveis dentro do lia-agent-system):
    lia_llm.shims — token budget (re-export de app.domains.credits.services.token_budget_service)

Quick import:
    from lia_llm import ModelTierResolver, resolve_model_tier
    from lia_llm import CANONICAL_HAIKU_MODEL, CANONICAL_SONNET_MODEL
    from lia_llm import LLMResponseEnvelope, safe_llm_with_flag, LLMFailureMode
"""

# ── Model identifiers ─────────────────────────────────────────────────────────
from lia_llm.models import (  # noqa: F401
    CANONICAL_GEMINI_FLASH_MODEL,
    CANONICAL_HAIKU_MODEL,
    CANONICAL_SONNET_MODEL,
)

# ── Model tier resolver ───────────────────────────────────────────────────────
from lia_llm.model_tier import (  # noqa: F401
    DOMAIN_TIER_DEFAULTS,
    MODEL_TIERS,
    TIER_FAST,
    TIER_HEAVY,
    TIER_STANDARD,
    ModelTierResolver,
    get_model_tier_resolver,
    resolve_model_tier,
)

# ── Safe response envelope ────────────────────────────────────────────────────
from lia_llm.safe_response import (  # noqa: F401
    LLMFailureMode,
    LLMResponseEnvelope,
    safe_llm_with_flag,
    safe_llm_with_flag_async,
)

__all__ = [
    # models
    "CANONICAL_HAIKU_MODEL",
    "CANONICAL_SONNET_MODEL",
    "CANONICAL_GEMINI_FLASH_MODEL",
    # model tier
    "ModelTierResolver",
    "get_model_tier_resolver",
    "resolve_model_tier",
    "DOMAIN_TIER_DEFAULTS",
    "MODEL_TIERS",
    "TIER_FAST",
    "TIER_STANDARD",
    "TIER_HEAVY",
    # safe response
    "LLMResponseEnvelope",
    "safe_llm_with_flag",
    "safe_llm_with_flag_async",
    "LLMFailureMode",
]
