"""
LLM Provider Factory — Task #125.

Manages provider instances with environment-based configuration AND
per-tenant dependency injection via ProviderContainer.

Changes from original:
  - LLMProviderFactory preserved for backward compatibility (class-level state).
  - ProviderContainer added: instance-based DI container per tenant.
  - get_provider_for_tenant() returns a container scoped to tenant config.
  - TenantProviderRegistry: singleton mapping tenant_id → ProviderContainer.
"""
import logging
import os
from typing import Optional

from app.shared.providers.llm_provider import LLMProviderABC

logger = logging.getLogger(__name__)

FALLBACK_ORDER: list[str] = ["gemini", "claude", "openai"]


# ---------------------------------------------------------------------------
# Original LLMProviderFactory — kept for backward compatibility
# ---------------------------------------------------------------------------

class LLMProviderFactory:
    """Factory for creating and managing LLM provider instances.

    Class variables serve as a global registry — suitable for single-tenant
    or simple multi-tenant use. For full tenant isolation use ProviderContainer
    via TenantProviderRegistry.
    """

    _providers: dict[str, type] = {}
    _instances: dict[str, LLMProviderABC] = {}

    @classmethod
    def register(cls, provider_class: type):
        """Register a provider class."""
        name = (
            provider_class._provider_name
            if hasattr(provider_class, "_provider_name")
            else provider_class.__name__
        )
        cls._providers[name] = provider_class
        return provider_class

    @classmethod
    def get(cls, provider_name: str) -> LLMProviderABC:
        """Get or create a provider instance."""
        if provider_name not in cls._instances:
            if provider_name not in cls._providers:
                raise ValueError(
                    f"Unknown LLM provider: {provider_name}. "
                    f"Available: {list(cls._providers.keys())}"
                )
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
    async def generate_with_fallback(
        cls, prompt: str, system: str | None = None, **kwargs
    ) -> str:
        """Try providers in fallback order; return first success.

        .. deprecated::
            Use ``get_provider_for_tenant(company_id).generate_with_fallback()``
            instead for proper multi-tenant provider isolation.
            This class-level method uses shared global state and does not
            respect per-tenant provider configuration.

        Args:
            prompt: User message/prompt.
            system: Optional system prompt.
            **kwargs: Additional arguments passed to the provider.

        Returns:
            Generated text from the first available provider.

        Raises:
            Exception: If all providers fail.
        """
        import warnings
        warnings.warn(
            "LLMProviderFactory.generate_with_fallback() is deprecated. "
            "Use get_provider_for_tenant(company_id).generate_with_fallback() "
            "for proper multi-tenant provider isolation.",
            DeprecationWarning,
            stacklevel=2,
        )
        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        errors: list[str] = []
        for provider_name in FALLBACK_ORDER:
            try:
                provider = cls.get(provider_name)
                if system:
                    result = await provider.generate_with_system(system, prompt, **kwargs)
                else:
                    result = await provider.generate(prompt, **kwargs)
                if provider_name != FALLBACK_ORDER[0]:
                    logger.warning(
                        "[LLMFactory] Used fallback provider '%s' after primary failed",
                        provider_name,
                    )
                return result.text
            except CircuitBreakerError as e:
                errors.append(
                    f"{provider_name}: circuit open (retry_after={e.retry_after:.1f}s)"
                )
                logger.warning(
                    "[LLMFactory] Provider '%s' circuit open, trying next", provider_name
                )
            except Exception as e:
                errors.append(f"{provider_name}: {type(e).__name__}: {e}")
                logger.warning("[LLMFactory] Provider '%s' failed: %s", provider_name, e)

        raise Exception(f"All LLM providers failed: {errors}")


# ---------------------------------------------------------------------------
# ProviderContainer — per-tenant DI container
# ---------------------------------------------------------------------------

class ProviderContainer:
    """
    Dependency-injection container for LLM providers scoped to a tenant.

    Accepts explicit provider configuration (primary + fallback order),
    falling back to environment defaults. Provider instances are lazily
    created and cached within this container — isolated from other tenants.

    Usage:
        container = ProviderContainer(
            tenant_id="acme",
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )
        provider = container.get_primary()
        result = await container.generate_with_fallback(prompt)
    """

    def __init__(
        self,
        tenant_id: str | None = None,
        primary_provider: str | None = None,
        fallback_order: list[str] | None = None,
        provider_api_keys: dict[str, str] | None = None,
    ) -> None:
        self._tenant_id = tenant_id
        self._primary = primary_provider or os.environ.get("LLM_DEFAULT_PROVIDER", "gemini")
        raw_order = fallback_order or list(FALLBACK_ORDER)
        self._fallback_order = [self._primary] + [
            p for p in raw_order if p != self._primary
        ]
        self._instances: dict[str, LLMProviderABC] = {}
        self._api_keys: dict[str, str] = provider_api_keys or {}

    @property
    def tenant_id(self) -> str | None:
        return self._tenant_id

    @property
    def primary_provider(self) -> str:
        return self._primary

    @property
    def fallback_order(self) -> list[str]:
        return list(self._fallback_order)

    @property
    def has_custom_keys(self) -> bool:
        return bool(self._api_keys)

    def get(self, provider_name: str) -> LLMProviderABC:
        """Get (or lazily create) a provider instance within this container.
        If tenant API keys are available, creates a provider with the tenant key."""
        if provider_name not in self._instances:
            global_providers = LLMProviderFactory._providers
            if provider_name not in global_providers:
                raise ValueError(
                    f"Unknown LLM provider: {provider_name}. "
                    f"Available: {list(global_providers.keys())}"
                )
            tenant_key = self._api_keys.get(provider_name)
            if tenant_key:
                self._instances[provider_name] = global_providers[provider_name](
                    api_key=tenant_key
                )
                logger.info(
                    "[ProviderContainer] tenant=%s created provider=%s with tenant key",
                    self._tenant_id, provider_name,
                )
            else:
                self._instances[provider_name] = global_providers[provider_name]()
                logger.debug(
                    "[ProviderContainer] tenant=%s created provider=%s with system key",
                    self._tenant_id, provider_name,
                )
        return self._instances[provider_name]

    def get_primary(self) -> LLMProviderABC:
        """Get the primary (preferred) provider for this tenant."""
        return self.get(self._primary)

    def clear(self) -> None:
        """Release cached instances (for testing / hot-reload)."""
        self._instances.clear()

    async def _try_generate(
        self, provider: LLMProviderABC, prompt: str, system: str | None, **kwargs
    ):
        if system:
            return await provider.generate_with_system(system, prompt, **kwargs)
        return await provider.generate(prompt, **kwargs)

    async def generate_with_fallback(
        self, prompt: str, system: str | None = None, **kwargs
    ) -> str:
        """Try providers in tenant fallback order with per-provider credential fallback.
        For each provider: tenant key → system key → next provider."""
        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        errors: list[str] = []
        for provider_name in self._fallback_order:
            try:
                provider = self.get(provider_name)
                result = await self._try_generate(provider, prompt, system, **kwargs)
                if provider_name != self._primary:
                    logger.warning(
                        "[ProviderContainer] tenant=%s used fallback '%s'",
                        self._tenant_id,
                        provider_name,
                    )
                return result.text
            except CircuitBreakerError as e:
                errors.append(
                    f"{provider_name}: circuit open (retry_after={e.retry_after:.1f}s)"
                )
                logger.warning(
                    "[ProviderContainer] tenant=%s provider '%s' circuit open",
                    self._tenant_id,
                    provider_name,
                )
            except Exception as e:
                errors.append(f"{provider_name}(tenant-key): {type(e).__name__}: {e}")
                tenant_key = self._api_keys.get(provider_name)
                if tenant_key:
                    logger.warning(
                        "[ProviderContainer] tenant=%s provider '%s' tenant-key failed, retrying with system key: %s",
                        self._tenant_id, provider_name, e,
                    )
                    try:
                        global_providers = LLMProviderFactory._providers
                        system_provider = global_providers[provider_name]()
                        result = await self._try_generate(system_provider, prompt, system, **kwargs)
                        logger.info(
                            "[ProviderContainer] tenant=%s provider '%s' succeeded with system key (tenant key failed)",
                            self._tenant_id, provider_name,
                        )
                        return result.text
                    except Exception as e2:
                        errors.append(f"{provider_name}(system-key): {type(e2).__name__}: {e2}")
                        logger.warning(
                            "[ProviderContainer] tenant=%s provider '%s' system-key also failed: %s",
                            self._tenant_id, provider_name, e2,
                        )
                else:
                    logger.warning(
                        "[ProviderContainer] tenant=%s provider '%s' failed: %s",
                        self._tenant_id, provider_name, e,
                    )

        raise Exception(
            f"All LLM providers failed for tenant={self._tenant_id}: {errors}"
        )

    def __repr__(self) -> str:
        return (
            f"<ProviderContainer tenant={self._tenant_id!r} "
            f"primary={self._primary!r} "
            f"fallback={self._fallback_order!r}>"
        )


# ---------------------------------------------------------------------------
# TenantProviderRegistry — singleton registry of per-tenant containers
# ---------------------------------------------------------------------------

class TenantProviderRegistry:
    """
    Singleton registry mapping tenant_id → ProviderContainer.

    Integrates with ToolPermissionsLoader so that each tenant's preferred
    LLM provider is driven by the same YAML config as tool permissions.

    Usage:
        registry = TenantProviderRegistry.get_instance()
        container = registry.get_container("acme_corp")
        result = await container.generate_with_fallback(prompt)
    """

    _instance: Optional["TenantProviderRegistry"] = None

    def __init__(self) -> None:
        self._containers: dict[str, ProviderContainer] = {}

    @classmethod
    def get_instance(cls) -> "TenantProviderRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_container(
        self,
        tenant_id: str | None,
        primary_provider: str | None = None,
        fallback_order: list[str] | None = None,
    ) -> ProviderContainer:
        """
        Get or create a ProviderContainer for the given tenant.

        If primary_provider / fallback_order are not passed, the registry
        tries to load them from ToolPermissionsLoader (YAML config).
        Falls back to global env-var defaults.

        **Cache semantics**: the first call for a given tenant_id creates and
        caches the container. Subsequent calls for the same tenant_id return
        the cached container, ignoring any explicit primary_provider/fallback_order
        arguments.  To force a different configuration for an existing tenant,
        call ``remove_container(tenant_id)`` or ``clear()`` before calling
        ``get_container`` again.

        Args:
            tenant_id: Tenant identifier (None = global default container).
            primary_provider: Override primary provider (only applied on first call).
            fallback_order: Override fallback order (only applied on first call).

        Returns:
            ProviderContainer scoped to this tenant.
        """
        key = tenant_id or "__global__"

        if key not in self._containers:
            resolved_primary = primary_provider
            resolved_fallback = fallback_order

            if not resolved_primary or not resolved_fallback:
                resolved_primary, resolved_fallback = self._load_from_permissions(
                    tenant_id, resolved_primary, resolved_fallback
                )

            self._containers[key] = ProviderContainer(
                tenant_id=tenant_id,
                primary_provider=resolved_primary,
                fallback_order=resolved_fallback,
            )
            logger.debug(
                "[TenantProviderRegistry] Created container for tenant=%s provider=%s",
                tenant_id,
                resolved_primary,
            )

        return self._containers[key]

    @staticmethod
    def _load_from_permissions(
        tenant_id: str | None,
        primary_override: str | None,
        fallback_override: list[str] | None,
    ) -> tuple[str, list[str]]:
        """Load provider config from ToolPermissionsLoader (YAML)."""
        try:
            from app.tools.tool_permissions_loader import get_permissions
            cfg = get_permissions(tenant_id)
            primary = primary_override or cfg.llm_provider
            fallback = fallback_override or cfg.llm_fallback_order
            return primary, fallback
        except Exception as exc:
            logger.debug(
                "[TenantProviderRegistry] Could not load permissions for tenant=%s: %s",
                tenant_id,
                exc,
            )
            default = os.environ.get("LLM_DEFAULT_PROVIDER", "gemini")
            return primary_override or default, fallback_override or list(FALLBACK_ORDER)

    async def load_from_db(self, tenant_id: str) -> ProviderContainer | None:
        """Load tenant config from DB and create a container with tenant API keys.
        Falls back to system keys if tenant key fails."""
        try:
            from app.shared.tenant_llm_context import get_tenant_llm_config
            config = await get_tenant_llm_config(tenant_id)
            if not config:
                return None

            primary = config.get("primary_provider", "gemini")
            fallback = config.get("fallback_order", list(FALLBACK_ORDER))
            providers_cfg = config.get("providers", {})

            self.remove_container(tenant_id)

            container = ProviderContainer(
                tenant_id=tenant_id,
                primary_provider=primary,
                fallback_order=fallback,
                provider_api_keys={
                    name: prov.get("api_key")
                    for name, prov in providers_cfg.items()
                    if prov.get("api_key")
                },
            )
            key = tenant_id or "__global__"
            self._containers[key] = container
            logger.info(
                "[TenantProviderRegistry] Loaded DB config for tenant=%s provider=%s",
                tenant_id, primary,
            )
            return container
        except Exception as exc:
            logger.warning(
                "[TenantProviderRegistry] DB load failed for tenant=%s: %s",
                tenant_id, exc,
            )
            return None

    def register_container(
        self, tenant_id: str, container: ProviderContainer
    ) -> None:
        """Explicitly register a pre-built container (for testing / DI wiring)."""
        key = tenant_id or "__global__"
        self._containers[key] = container
        logger.debug(
            "[TenantProviderRegistry] Registered container for tenant=%s", tenant_id
        )

    def remove_container(self, tenant_id: str) -> bool:
        """Remove a cached container (forces re-creation on next access)."""
        key = tenant_id or "__global__"
        if key in self._containers:
            del self._containers[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all containers (for testing)."""
        self._containers.clear()

    @classmethod
    def reset(cls) -> None:
        """Full singleton reset (for testing)."""
        if cls._instance:
            cls._instance.clear()
        cls._instance = None

    def list_tenants(self) -> list[str]:
        """Return list of tenant IDs with active containers."""
        return [k for k in self._containers if k != "__global__"]

    def __repr__(self) -> str:
        return (
            f"<TenantProviderRegistry tenants={self.list_tenants()}>"
        )


# ---------------------------------------------------------------------------
# Convenience accessor
# ---------------------------------------------------------------------------

def get_provider_for_tenant(
    tenant_id: str | None = None,
    primary_provider: str | None = None,
    fallback_order: list[str] | None = None,
) -> ProviderContainer:
    """
    Get a ProviderContainer for the given tenant.

    This is the recommended entry point for multi-tenant provider access.
    Provider config is sourced from tool_permissions.yaml by default.
    """
    return TenantProviderRegistry.get_instance().get_container(
        tenant_id=tenant_id,
        primary_provider=primary_provider,
        fallback_order=fallback_order,
    )


async def get_provider_for_tenant_from_db(
    tenant_id: str,
) -> ProviderContainer:
    """
    Get a ProviderContainer for the given tenant, loading from DB if available.
    Falls back to system defaults if no DB config exists.
    """
    registry = TenantProviderRegistry.get_instance()
    container = await registry.load_from_db(tenant_id)
    if container:
        return container
    return registry.get_container(tenant_id=tenant_id)
