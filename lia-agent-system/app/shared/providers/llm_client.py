"""
Unified LLM Client — routes through ProviderContainer (Choose Your AI layer).

All calls route through get_provider_for_tenant() for tenant routing,
PII stripping, and audit logging. No direct SDK imports.
"""
import logging

logger = logging.getLogger(__name__)


def get_anthropic_client():
    """Returns a ProviderContainer via get_provider_for_tenant().

    Convenience wrapper. Callers can also use get_provider_for_tenant() directly.
    """
    from app.shared.providers.llm_factory import get_provider_for_tenant
    return get_provider_for_tenant()


def is_llm_available() -> bool:
    """Check if LLM is available."""
    try:
        get_anthropic_client()
        return True
    except Exception:
        # T-04 Tipo B: probe failure must be visible — return False is the
        # contract, but the reason (missing API key, network, bad config)
        # is critical operator information.
        logger.warning(
            "[llm_client] is_llm_available probe failed",
            exc_info=True,
        )
        return False


async def llm_complete(
    prompt: str,
    system: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str | None:
    """
    Completion wrapper — routes through ProviderContainer.
    """
    try:
        from app.shared.providers.llm_factory import get_provider_for_tenant
        container = get_provider_for_tenant()
        return await container.generate_with_fallback(prompt, system=system, agent_type="LLMClientAgent")
    except Exception as e:
        logger.error(f"[LLM] Completion failed: {e}")
        return None
