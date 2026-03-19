"""
LLM Provider Factory.

Manages provider instances with environment-based configuration.
"""
import os
import logging
from typing import Dict, List, Optional
from app.shared.providers.llm_provider import LLMProviderABC

logger = logging.getLogger(__name__)

FALLBACK_ORDER: List[str] = ["claude", "gemini", "openai"]


class LLMProviderFactory:
    """Factory for creating and managing LLM provider instances."""
    
    _providers: Dict[str, type] = {}
    _instances: Dict[str, LLMProviderABC] = {}
    
    @classmethod
    def register(cls, provider_class: type):
        """Register a provider class."""
        name = provider_class._provider_name if hasattr(provider_class, '_provider_name') else provider_class.__name__
        cls._providers[name] = provider_class
        return provider_class
    
    @classmethod
    def get(cls, provider_name: str) -> LLMProviderABC:
        """Get or create a provider instance."""
        if provider_name not in cls._instances:
            if provider_name not in cls._providers:
                raise ValueError(f"Unknown LLM provider: {provider_name}. Available: {list(cls._providers.keys())}")
            cls._instances[provider_name] = cls._providers[provider_name]()
        return cls._instances[provider_name]
    
    @classmethod
    def get_default(cls) -> LLMProviderABC:
        """Get the default provider based on environment configuration."""
        default = os.environ.get("LLM_DEFAULT_PROVIDER", "gemini")
        return cls.get(default)
    
    @classmethod
    def available_providers(cls) -> list:
        """List registered provider names."""
        return list(cls._providers.keys())
    
    @classmethod
    def clear(cls):
        """Clear all instances (for testing)."""
        cls._instances.clear()

    @classmethod
    async def generate_with_fallback(cls, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Try providers in fallback order; return first success.

        Args:
            prompt: User message/prompt.
            system: Optional system prompt.
            **kwargs: Additional arguments passed to the provider.

        Returns:
            Generated text from the first available provider.

        Raises:
            Exception: If all providers fail.
        """
        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        errors: List[str] = []
        for provider_name in FALLBACK_ORDER:
            try:
                provider = cls.get(provider_name)
                if system:
                    result = await provider.generate_with_system(system, prompt, **kwargs)
                else:
                    result = await provider.generate(prompt, **kwargs)
                if provider_name != FALLBACK_ORDER[0]:
                    logger.warning(f"[LLMFactory] Used fallback provider '{provider_name}' after primary failed")
                return result.text
            except CircuitBreakerError as e:
                errors.append(f"{provider_name}: circuit open (retry_after={e.retry_after:.1f}s)")
                logger.warning(f"[LLMFactory] Provider '{provider_name}' circuit open, trying next")
            except Exception as e:
                errors.append(f"{provider_name}: {type(e).__name__}: {e}")
                logger.warning(f"[LLMFactory] Provider '{provider_name}' failed: {e}")

        raise Exception(f"All LLM providers failed: {errors}")
