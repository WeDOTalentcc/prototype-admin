"""Agent execution pricing canonical (Wave 4 W4-4 audit 2026-05-22).

ANTES: credits_consumed era 0 (hardcoded) ou listing.credits_per_execution (constante).
DEPOIS: credits_consumed = tokens_input × input_price + tokens_output × output_price.

Pricing tiers refletem custos reais OpenAI/Anthropic GPT-4-class models por 1k tokens.
1 credit = 1 cent USD (R$ 0.05 aprox). Cliente pode ver custo real em "Consumo" tab.

Infraestrutura de billing (Iugu/Vindi BR) permanece inalterada — esta sprint
apenas conserta o cálculo de credits_consumed para refletir uso real.

Wave 4 W4-4 follow-up: integrar com Iugu/Vindi para emitir invoice quando
credits_consumed > tier_threshold.
"""
from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Pricing por 1k tokens — em credits (1 credit = ~$0.01 USD)
# Valores baseados em OpenAI GPT-4o + Anthropic Claude Sonnet 4.5 médio em maio/2026
PRICING_PER_1K_TOKENS = {
    # Free tier — clientes em trial / marketplace agents grátis
    "free": {
        "input": 0,
        "output": 0,
    },
    # Pro tier — pricing real refletindo custo médio LLM + margem
    "pro": {
        "input": 1,   # 1 credit per 1k input tokens
        "output": 3,  # 3 credits per 1k output tokens (output mais caro)
    },
    # Enterprise — pricing premium (modelos mais caros + SLA)
    "enterprise": {
        "input": 2,
        "output": 6,
    },
}


def compute_credits(
    tokens_input: int,
    tokens_output: int,
    tier: str = "pro",
    fallback_credits: Optional[int] = None,
) -> int:
    """Compute credits_consumed real = tokens × price (rounded UP).

    Args:
        tokens_input: input tokens used (do LLM response metadata)
        tokens_output: output tokens generated
        tier: pricing tier (free/pro/enterprise). Default 'pro'.
        fallback_credits: se tokens são 0 (LLM provider não retornou metadata),
                          usa esse valor (provavelmente listing.credits_per_execution).

    Returns:
        Credits consumidos (int, mínimo 0).
    """
    if tier not in PRICING_PER_1K_TOKENS:
        logger.warning("[agent_pricing] tier desconhecido %s, usando 'pro'", tier)
        tier = "pro"

    prices = PRICING_PER_1K_TOKENS[tier]

    # Se tokens ausentes (LLM não retornou metadata), usa fallback
    if tokens_input == 0 and tokens_output == 0:
        return fallback_credits if fallback_credits is not None else 0

    # Ceil-divide para garantir cobrança mínima de 1 credit em uso minúsculo
    input_credits = (tokens_input * prices["input"] + 999) // 1000
    output_credits = (tokens_output * prices["output"] + 999) // 1000

    return max(0, input_credits + output_credits)
