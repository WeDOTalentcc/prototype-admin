"""Agent execution pricing canonical (Wave 4 W4-4 audit 2026-05-22).

ANTES: credits_consumed era 0 (hardcoded) ou listing.credits_per_execution (constante).
DEPOIS: credits_consumed = tokens_input × input_price + tokens_output × output_price.

F-19 P1 (audit 2026-05-22): voice extension. Voice usa Twilio + Deepgram + Gemini
+ OpenAI TTS — todos cobram por minuto/tokens, mas voice era billing ghost.
Estendido para suportar audio metrics:
- audio_seconds_stt: Deepgram + Gemini Flash STT
- audio_seconds_tts: OpenAI TTS
- twilio_seconds: PSTN/VoIP per-minute fee

Pricing tiers refletem custos reais OpenAI/Anthropic GPT-4-class models por 1k tokens
+ Twilio Voice rates por minuto. 1 credit = 1 cent USD (R$ 0.05 aprox).

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


# F-19 P1: pricing por MINUTO audio — em credits (1 credit = ~$0.01 USD)
# Refletindo: Deepgram STT ~$0.0125/min + Gemini Flash STT ~$0.001/min,
# OpenAI TTS ~$0.015/min, Twilio Voice PSTN BR ~$0.085/min.
# Approximacao conservadora em credits inteiros por minuto.
PRICING_PER_AUDIO_MINUTE = {
    "free": {
        "stt": 0,
        "tts": 0,
        "twilio_pstn": 0,
    },
    "pro": {
        "stt": 2,         # 2 credits/min STT (Deepgram + Gemini fallback)
        "tts": 2,         # 2 credits/min TTS (OpenAI)
        "twilio_pstn": 9, # 9 credits/min PSTN (Twilio BR)
    },
    "enterprise": {
        "stt": 3,
        "tts": 3,
        "twilio_pstn": 12,
    },
}


def compute_credits(
    tokens_input: int = 0,
    tokens_output: int = 0,
    audio_seconds_stt: int = 0,
    audio_seconds_tts: int = 0,
    twilio_seconds: int = 0,
    tier: str = "pro",
    fallback_credits: Optional[int] = None,
) -> int:
    """Compute credits_consumed real = tokens × token_price + audio × audio_price.

    F-19 P1 extension: agora suporta voice metrics (audio_seconds_stt/tts +
    twilio_seconds). Backward compat preservado: callers tokens-only continuam
    funcionando identicamente.

    Args:
        tokens_input: input tokens (do LLM response metadata)
        tokens_output: output tokens generated
        audio_seconds_stt: audio segundos para STT (Deepgram + Gemini Flash)
        audio_seconds_tts: audio segundos para TTS (OpenAI)
        twilio_seconds: audio segundos via Twilio PSTN/VoIP
        tier: pricing tier (free/pro/enterprise). Default 'pro'.
        fallback_credits: se TODAS metrics sao 0, usa esse valor.

    Returns:
        Credits consumidos (int, mínimo 0).
    """
    if tier not in PRICING_PER_1K_TOKENS:
        logger.warning("[agent_pricing] tier desconhecido %s, usando 'pro'", tier)
        tier = "pro"

    token_prices = PRICING_PER_1K_TOKENS[tier]
    audio_prices = PRICING_PER_AUDIO_MINUTE[tier]

    # Se TODAS metrics sao 0, usa fallback (LLM provider sem metadata + sem voice)
    all_zero = (
        tokens_input == 0 and tokens_output == 0
        and audio_seconds_stt == 0 and audio_seconds_tts == 0
        and twilio_seconds == 0
    )
    if all_zero:
        return fallback_credits if fallback_credits is not None else 0

    # Token component (ceil-divide para garantir cobranca minima)
    input_credits = (tokens_input * token_prices["input"] + 999) // 1000
    output_credits = (tokens_output * token_prices["output"] + 999) // 1000

    # F-19 audio component (ceil-divide segundos -> minutos)
    stt_credits = (audio_seconds_stt * audio_prices["stt"] + 59) // 60
    tts_credits = (audio_seconds_tts * audio_prices["tts"] + 59) // 60
    twilio_credits = (twilio_seconds * audio_prices["twilio_pstn"] + 59) // 60

    total = input_credits + output_credits + stt_credits + tts_credits + twilio_credits
    return max(0, total)


def compute_voice_credits(
    total_audio_seconds: int,
    tokens_input: int = 0,
    tokens_output: int = 0,
    tier: str = "pro",
) -> int:
    """F-19 P1 canonical helper for voice screening billing.

    Encapsula heuristica padrao voice: STT cobra tempo total, TTS ~1/3 do tempo
    (LIA fala menos que candidato), Twilio cobra tempo total (PSTN connection).
    Tokens vem de Gemini LLM gerando responses.

    Usar em VoiceScreeningOrchestrator.finalize_screening + WSI completion.

    Args:
        total_audio_seconds: duracao total da call em segundos
        tokens_input: Gemini LLM input tokens (audio transcript + system prompt)
        tokens_output: Gemini LLM output tokens (LIA responses)
        tier: pricing tier do company (free/pro/enterprise)

    Returns:
        Credits consumidos canonical.
    """
    # TTS = ~1/3 do tempo total (LIA fala menos que candidato em screening)
    tts_seconds = total_audio_seconds // 3

    return compute_credits(
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        audio_seconds_stt=total_audio_seconds,
        audio_seconds_tts=tts_seconds,
        twilio_seconds=total_audio_seconds,
        tier=tier,
    )
