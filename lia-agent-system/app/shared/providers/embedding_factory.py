"""
EmbeddingProviderFactory — Task #134.

Manages embedding provider instances with environment-based configuration.
Mirrors the structure of LLMProviderFactory for consistency.

Fallback order: tries each registered provider in sequence until one succeeds.
"""
from typing import Tuple
import logging
import os

from app.shared.providers.embedding_provider import EmbeddingProviderABC

logger = logging.getLogger(__name__)

EMBEDDING_FALLBACK_ORDER: list[str] = ["gemini", "openai"]


class EmbeddingProviderFactory:
    """Factory for creating and managing embedding provider instances.

    Class variables serve as a global registry.
    Provider instances are created lazily and cached.

    Usage:
        factory = EmbeddingProviderFactory
        provider = factory.get_default()
        result = await provider.embed_text("Software Engineer with Python skills")

        # Or use fallback:
        vector, provider_name, model = await factory.embed_with_fallback("some text")
    """

    _providers: dict[str, type] = {}
    _instances: dict[str, EmbeddingProviderABC] = {}

    @classmethod
    def register(cls, provider_class: type) -> type:
        """Register an embedding provider class.

        The class must have a ``_provider_name`` attribute or its ``__name__``
        will be used as the key.
        """
        name = (
            provider_class._provider_name
            if hasattr(provider_class, "_provider_name")
            else provider_class.__name__
        )
        cls._providers[name] = provider_class
        logger.debug("[EmbeddingFactory] Registered provider: %s", name)
        return provider_class

    @classmethod
    def get(cls, provider_name: str) -> EmbeddingProviderABC:
        """Get or create a provider instance.

        Args:
            provider_name: Registered provider key (e.g. 'gemini', 'openai').

        Returns:
            Cached or freshly-created provider instance.

        Raises:
            ValueError: If provider_name is not registered.
        """
        if provider_name not in cls._instances:
            if provider_name not in cls._providers:
                raise ValueError(
                    f"Unknown embedding provider: {provider_name}. "
                    f"Available: {list(cls._providers.keys())}"
                )
            cls._instances[provider_name] = cls._providers[provider_name]()
            logger.debug("[EmbeddingFactory] Created instance for provider: %s", provider_name)
        return cls._instances[provider_name]

    @classmethod
    def get_default(cls) -> EmbeddingProviderABC:
        """Get the default provider from EMBEDDING_DEFAULT_PROVIDER env var.

        Falls back to 'gemini' if the variable is not set.
        """
        default = os.environ.get("EMBEDDING_DEFAULT_PROVIDER", "gemini")
        return cls.get(default)

    @classmethod
    def available_providers(cls) -> list[str]:
        """Return a list of registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all cached instances (for testing)."""
        cls._instances.clear()

    @classmethod
    async def embed_with_fallback(
        cls,
        text: str,
        preferred_provider: str | None = None,
    ) -> tuple[list[float], str, str]:
        """Generate embedding with automatic provider fallback.

        Tries providers in the following order:
        1. ``preferred_provider`` (if given and registered).
        2. Default provider (EMBEDDING_DEFAULT_PROVIDER env var).
        3. Remaining providers in EMBEDDING_FALLBACK_ORDER.

        Args:
            text: Text to embed.
            preferred_provider: Provider to try first (optional).

        Returns:
            Tuple of (vector, provider_name, model_name) from the first
            successful provider.

        Raises:
            Exception: If all providers fail.
        """
        order = cls._build_fallback_order(preferred_provider)

        errors: list[str] = []
        for provider_name in order:
            try:
                provider = cls.get(provider_name)
                result = await provider.embed_text(text)
                if provider_name != order[0]:
                    logger.warning(
                        "[EmbeddingFactory] Used fallback provider '%s'", provider_name
                    )
                return result.vector, result.provider, result.model
            except Exception as exc:
                errors.append(f"{provider_name}: {type(exc).__name__}: {exc}")
                logger.warning(
                    "[EmbeddingFactory] Provider '%s' failed: %s", provider_name, exc
                )

        raise Exception(f"All embedding providers failed: {errors}")

    @classmethod
    async def generate_with_fallback(
        cls,
        text: str,
        preferred_provider: str | None = None,
    ) -> tuple[list[float], str, str]:
        """Alias for embed_with_fallback() — task spec API name.

        See :meth:`embed_with_fallback` for full documentation.
        """
        return await cls.embed_with_fallback(text, preferred_provider)

    @classmethod
    async def embed_batch_with_fallback(
        cls,
        texts: list[str],
        preferred_provider: str | None = None,
    ) -> tuple[list[list[float]], str, str]:
        """Generate batch embeddings with automatic provider fallback.

        Args:
            texts: Texts to embed.
            preferred_provider: Provider to try first (optional).

        Returns:
            Tuple of (vectors, provider_name, model_name) from the first
            successful provider.

        Raises:
            Exception: If all providers fail.
        """
        order = cls._build_fallback_order(preferred_provider)

        errors: list[str] = []
        for provider_name in order:
            try:
                provider = cls.get(provider_name)
                results = await provider.embed_batch(texts)
                vectors = [r.vector for r in results]
                if results:
                    pname = results[0].provider
                    model = results[0].model
                else:
                    pname = provider_name
                    model = provider.default_model
                if provider_name != order[0]:
                    logger.warning(
                        "[EmbeddingFactory] Batch used fallback provider '%s'", provider_name
                    )
                return vectors, pname, model
            except Exception as exc:
                errors.append(f"{provider_name}: {type(exc).__name__}: {exc}")
                logger.warning(
                    "[EmbeddingFactory] Batch provider '%s' failed: %s", provider_name, exc
                )

        raise Exception(f"All embedding providers failed for batch: {errors}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _build_fallback_order(cls, preferred_provider: str | None) -> list[str]:
        """Build the ordered list of providers to attempt."""
        default = os.environ.get("EMBEDDING_DEFAULT_PROVIDER", "gemini")

        seen = set()
        order: list[str] = []

        for candidate in [preferred_provider, default] + list(EMBEDDING_FALLBACK_ORDER):
            if candidate and candidate not in seen and candidate in cls._providers:
                seen.add(candidate)
                order.append(candidate)

        if not order:
            order = list(cls._providers.keys())

        return order
