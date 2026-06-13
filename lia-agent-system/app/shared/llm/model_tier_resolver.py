"""
ModelTierResolver — shim de retrocompatibilidade.

EXTRACTED TO: libs/lia-llm/lia_llm/model_tier.py
Este arquivo é shim — remover quando todos os consumers migrarem para:
    from lia_llm.model_tier import ModelTierResolver, resolve_model_tier
    from lia_llm import ModelTierResolver
"""
# ruff: noqa: F401, F403
from lia_llm.model_tier import *  # noqa: F401, F403
from lia_llm.model_tier import (  # noqa: F401 — re-export explícito para IDEs
    DOMAIN_TIER_DEFAULTS,
    MODEL_TIERS,
    TIER_FAST,
    TIER_HEAVY,
    TIER_STANDARD,
    ModelTierResolver,
    get_model_tier_resolver,
    resolve_model_tier,
)
