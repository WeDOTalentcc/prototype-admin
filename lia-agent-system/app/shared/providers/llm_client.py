"""
Unified LLM Client — LEGACY WRAPPER (Task #93 migration).

All calls now route through LLMProviderFactory for tenant routing,
PII stripping, and audit logging. No direct SDK imports.
"""
import logging

logger = logging.getLogger(__name__)


def get_anthropic_client():
    """LEGACY — Returns a ProviderContainer via LLMProviderFactory (Task #93).
    
    Maintained for backward compatibility. Callers should migrate to
    get_provider_for_tenant() directly.
    """
    from app.shared.providers.llm_factory import get_provider_for_tenant
    return get_provider_for_tenant()


def is_llm_available() -> bool:
    """Check if LLM is available."""
    try:
        get_anthropic_client()
        return True
    except Exception:
        return False


async def llm_complete(
    prompt: str,
    system: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str | None:
    """
    Completion wrapper — routes through LLMProviderFactory (Task #93).
    """
    try:
        from app.shared.providers.llm_factory import get_provider_for_tenant
        container = get_provider_for_tenant()
        return await container.generate_with_fallback(prompt, system=system)
    except Exception as e:
        logger.error(f"[LLM] Completion failed: {e}")
        return None
