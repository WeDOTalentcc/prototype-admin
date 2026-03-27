"""
Unified LLM Client - Centralized access to Anthropic Claude via Replit AI Integrations.
All services should use this helper instead of creating their own Anthropic clients.
"""
import os
import logging
from typing import Optional, Dict, Any
from anthropic import Anthropic

logger = logging.getLogger(__name__)

_client: Optional[Anthropic] = None

def get_anthropic_client() -> Anthropic:
    """Get or create a singleton Anthropic client using Replit AI Integrations."""
    global _client
    if _client is not None:
        return _client
    
    api_key = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
    
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        base_url = None
        if api_key:
            logger.info("[LLM] Using ANTHROPIC_API_KEY fallback (not Replit AI Integrations)")
    
    if not api_key:
        raise ValueError(
            "No Anthropic API key configured. Set AI_INTEGRATIONS_ANTHROPIC_API_KEY "
            "(Replit AI Integrations) or ANTHROPIC_API_KEY."
        )
    
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
        logger.info(f"[LLM] Anthropic client initialized via Replit AI Integrations")
    else:
        logger.info(f"[LLM] Anthropic client initialized with direct API key")
    
    _client = Anthropic(**kwargs)
    return _client


def is_llm_available() -> bool:
    """Check if LLM is available without throwing."""
    try:
        get_anthropic_client()
        return True
    except (ValueError, Exception) as e:
        logger.warning(f"[LLM] Not available: {e}")
        return False


async def llm_complete(
    prompt: str,
    system: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> Optional[str]:
    """Simple completion wrapper with error handling. Returns None on failure."""
    try:
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
        logger.error(f"[LLM] Completion failed: {e}", exc_info=True)
        return None
