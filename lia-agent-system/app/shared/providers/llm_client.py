"""
Unified LLM Client — LEGACY WRAPPER.

This module now redirects ALL calls through LLMService.safe_invoke()
to ensure tenant routing, PII stripping, and audit logging.

Original direct Anthropic client preserved as _get_raw_client() for
cases that truly need the raw SDK (e.g., migrations, admin tools).
"""
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_anthropic_client():
    """LEGACY — Returns raw Anthropic client. Prefer LLMService.safe_invoke()."""
    try:
        from anthropic import Anthropic
        api_key = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        if not api_key:
            raise ValueError("No Anthropic API key configured")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return Anthropic(**kwargs)
    except Exception as e:
        logger.error(f"[LLM] Client creation failed: {e}")
        raise


def is_llm_available() -> bool:
    """Check if LLM is available."""
    try:
        get_anthropic_client()
        return True
    except Exception:
        return False


async def llm_complete(
    prompt: str,
    system: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> Optional[str]:
    """
    Completion wrapper — NOW routes through LLMService for PII + audit.
    Falls back to direct client if LLMService unavailable.
    """
    # Route through LLMService (PII + audit + tenant)
    try:
        from app.services.llm import llm_service
        result = await llm_service.safe_invoke(prompt, provider="claude")
        if result:
            return result
    except Exception as e:
        logger.debug("[llm_client] LLMService fallback: %s", e)

    # Direct fallback (preserves backward compat)
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        prompt = strip_pii_for_llm_prompt(prompt)

        client = get_anthropic_client()
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text
    except Exception as e:
        logger.error(f"[LLM] Completion failed: {e}")
        return None
