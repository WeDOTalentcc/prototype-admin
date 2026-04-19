"""
EmbeddingProviderFactory — Task #134.

Manages embedding provider instances with environment-based configuration.
Mirrors the structure of LLMProviderFactory for consistency.

Fallback order: tries each registered provider in sequence until one succeeds.
"""
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
        company_id: str | None = None,
    ) -> tuple[list[float], str, str]:
        """Generate embedding with automatic provider fallback.

        Tries providers in the following order:
        1. ``preferred_provider`` (if given and registered).
        2. Default provider (EMBEDDING_DEFAULT_PROVIDER env var).
        3. Remaining providers in EMBEDDING_FALLBACK_ORDER.

        Args:
            text: Text to embed.
            preferred_provider: Provider to try first (optional).
            company_id: Tenant ID for tenant-specific API keys (LGPD).

        Returns:
            Tuple of (vector, provider_name, model_name) from the first
            successful provider.

        Raises:
            Exception: If all providers fail.
        """
        # LIA-BYOK B4: if EMBEDDING_LOCK_PROVIDER is set, never fall back to
        # a different provider — dimension mismatch would silently corrupt the
        # pgvector index.
        _lock_provider = os.environ.get("EMBEDDING_LOCK_PROVIDER", "")

        order = cls._build_fallback_order(preferred_provider)
        _primary_provider = order[0] if order else ""

        errors: list[str] = []
        for provider_name in order:
            try:
                provider = cls._get_tenant_provider(provider_name, company_id)
                result = await provider.embed_text(text)
                if provider_name != _primary_provider:
                    if _lock_provider:
                        from app.shared.errors import LIALLMError
                        raise LIALLMError(
                            message=(
                                f"EMBEDDING_LOCK_PROVIDER={_lock_provider} está activo — "
                                f"fallback para '{provider_name}' bloqueado para evitar "
                                f"corrupção silenciosa do índice pgvector."
                            ),
                            code="EMBEDDING_FALLBACK_LOCKED",
                            details={"locked_provider": _lock_provider, "attempted": provider_name},
                        )
                    logger.critical(
                        "[EmbeddingFactory] ATENÇÃO: provider primário '%s' falhou — "
                        "usando '%s' com dimensão de embedding DIFERENTE. "
                        "O índice pgvector pode ser invalidado silenciosamente. "
                        "Defina EMBEDDING_LOCK_PROVIDER para bloquear este fallback.",
                        _primary_provider, provider_name,
                    )
                return result.vector, result.provider, result.model
            except Exception as exc:
                errors.append(f"{provider_name}: {type(exc).__name__}: {exc}")
                logger.warning(
                    "[EmbeddingFactory] Provider '%s' failed: %s", provider_name, exc
                )

        from app.shared.errors import LIALLMError
        raise LIALLMError(
            message=f"Todos os provedores de embedding falharam: {errors}",
            code="EMBEDDING_ALL_PROVIDERS_FAILED",
            details={"errors": errors},
        )

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
        company_id: str | None = None,
    ) -> tuple[list[list[float]], str, str]:
        """Generate batch embeddings with automatic provider fallback.

        Args:
            texts: Texts to embed.
            preferred_provider: Provider to try first (optional).
            company_id: Tenant ID for tenant-specific API keys (LGPD).

        Returns:
            Tuple of (vectors, provider_name, model_name) from the first
            successful provider.

        Raises:
            Exception: If all providers fail.
        """
        _lock_provider_b = os.environ.get("EMBEDDING_LOCK_PROVIDER", "")

        order = cls._build_fallback_order(preferred_provider)
        _primary_provider_b = order[0] if order else ""

        errors: list[str] = []
        for provider_name in order:
            try:
                provider = cls._get_tenant_provider(provider_name, company_id)
                results = await provider.embed_batch(texts)
                vectors = [r.vector for r in results]
                if results:
                    pname = results[0].provider
                    model = results[0].model
                else:
                    pname = provider_name
                    model = provider.default_model
                if provider_name != _primary_provider_b:
                    if _lock_provider_b:
                        from app.shared.errors import LIALLMError
                        raise LIALLMError(
                            message=(
                                f"EMBEDDING_LOCK_PROVIDER={_lock_provider_b} activo — "
                                f"fallback batch para '{provider_name}' bloqueado."
                            ),
                            code="EMBEDDING_FALLBACK_LOCKED",
                            details={"locked_provider": _lock_provider_b, "attempted": provider_name},
                        )
                    logger.critical(
                        "[EmbeddingFactory] ATENÇÃO batch: provider '%s' falhou — "
                        "usando '%s' com dimensão diferente. Índice pgvector pode ser corrompido.",
                        _primary_provider_b, provider_name,
                    )
                return vectors, pname, model
            except Exception as exc:
                errors.append(f"{provider_name}: {type(exc).__name__}: {exc}")
                logger.warning(
                    "[EmbeddingFactory] Batch provider '%s' failed: %s", provider_name, exc
                )

        from app.shared.errors import LIALLMError
        raise LIALLMError(
            message=f"Todos os provedores de embedding falharam para batch: {errors}",
            code="EMBEDDING_BATCH_ALL_PROVIDERS_FAILED",
            details={"errors": errors},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _get_tenant_provider(
        cls, provider_name: str, company_id: str | None = None
    ) -> "EmbeddingProviderABC":
        """Get provider with tenant-specific config if available (LGPD)."""
        if company_id and provider_name == "gemini":
            try:
                from app.shared.tenant_llm_context import _tenant_configs

                config = _tenant_configs.get(company_id)
                if config:
                    providers = config.get("providers", {})
                    gemini_cfg = providers.get("gemini", {})
                    tenant_key = gemini_cfg.get("api_key")
                    if tenant_key:
                        from app.shared.providers.embedding_gemini import (
                            GeminiEmbeddingProvider,
                        )

                        logger.info(
                            "[EmbeddingFactory] Using tenant key for %s",
                            company_id,
                        )
                        return GeminiEmbeddingProvider(api_key=tenant_key)
            except Exception as exc:
                logger.warning(
                    "[EmbeddingFactory] Tenant key lookup failed for %s: %s",
                    company_id,
                    exc,
                )
        return cls.get(provider_name)

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
