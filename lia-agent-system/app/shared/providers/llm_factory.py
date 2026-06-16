"""
LLM Provider Factory — Choose Your AI layer.

Multi-tenant LLM provider management:
  - LLMProviderFactory: global class registry (register/get providers).
  - ProviderContainer: per-tenant DI container with fallback chain.
  - TenantProviderRegistry: singleton mapping tenant_id → ProviderContainer.
  - get_provider_for_tenant(): recommended entry point for all LLM access.
"""
import logging
import os
from typing import Optional

from app.domains.credits.services.token_budget_service import check_request_budget_before_llm
from app.shared.providers.llm_provider import LLMProviderABC
from app.shared.observability.llm_metrics import record_fallback, record_circuit_open

logger = logging.getLogger(__name__)

# UC-P1-06: LangSmith @traceable — graceful if package not installed
try:
    from langsmith import traceable as _ls_traceable
    _LANGSMITH_AVAILABLE = True
except ImportError:
    _LANGSMITH_AVAILABLE = False

    def _ls_traceable(**kwargs):
        """No-op decorator when langsmith is not installed."""
        def decorator(fn):
            return fn
        return decorator

# Sprint F.1: claude FIRST because Replit modelfarm proxy (localhost:1106)
# is broken for Gemini and OpenAI, AND langchain_anthropic.ChatAnthropic does
# NOT honor a base_url override → goes straight to api.anthropic.com using
# AI_INTEGRATIONS_ANTHROPIC_API_KEY (a real sk-ant-* key). Restoring this to
# ["gemini", "claude", "openai"] requires either fixing modelfarm or
# setting LLM_DEFAULT_PROVIDER per-tenant.
FALLBACK_ORDER: list[str] = ["claude", "gemini", "openai"]


# ---------------------------------------------------------------------------
# LLMProviderFactory — global provider class registry
# ---------------------------------------------------------------------------

class LLMProviderFactory:
    """Global registry of LLM provider classes.

    Stores provider classes (register) and creates singleton instances (get).
    ProviderContainer uses _providers to create per-tenant instances.
    For multi-tenant access, use get_provider_for_tenant() instead of this class.
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
    def available_providers(cls) -> list:
        """List registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def clear(cls):
        """Clear all instances (for testing)."""
        cls._instances.clear()


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
        region: str | None = None,
    ) -> None:
        self._tenant_id = tenant_id
        # W2-012-B (2026-05-23): per-tenant region pinning (LGPD Art 33).
        # None = sem region constraint (default global do provider).
        self._region = region
        self._primary = primary_provider or os.environ.get("LLM_DEFAULT_PROVIDER", "claude")
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
                # W2-012-B: pass region (None se sem constraint)
                self._instances[provider_name] = global_providers[provider_name](
                    api_key=tenant_key,
                    region=self._region,
                )
                logger.info(
                    "[ProviderContainer] tenant=%s created provider=%s with tenant key",
                    self._tenant_id, provider_name,
                )
            else:
                # W2-012-B: pass region even sem tenant key
                self._instances[provider_name] = global_providers[provider_name](
                    region=self._region,
                )
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

    @_ls_traceable(name="llm.generate", run_type="llm", tags=["lia"])
    async def _try_generate(
        self, provider: LLMProviderABC, prompt: str, system: str | None, **kwargs
    ):
        if system:
            return await provider.generate_with_system(system, prompt, **kwargs)
        return await provider.generate(prompt, **kwargs)

    async def generate_with_fallback(
        self, prompt: str, system: str | None = None, request_id: str | None = None, **kwargs
    ) -> str:  # UC-P2-28: request_id propagated to enrich_llm_span
        """Try providers in tenant fallback order with per-provider credential fallback.
        For each provider: tenant key → system key → next provider.

        Before calling any provider, checks the per-request token ceiling
        (Fase 3 guardrail). If the estimated tokens exceed the ceiling,
        raises RequestBudgetExceededError immediately — no LLM call is made.
        """
        plan_code = kwargs.pop("plan_code", None)
        agent_type = kwargs.pop("agent_type", None)
        company_id = kwargs.pop("company_id", None) or self._tenant_id
        user_id = kwargs.pop("user_id", None)
        expected_output_tokens = kwargs.pop("expected_output_tokens", None)
        # DEBT-002 (Sprint 2): track start of every LLM call inside the factory.
        # domain/operation are optional caller hints; fall back to agent_type.
        domain = kwargs.pop("domain", agent_type or "unknown")
        operation = kwargs.pop("operation", "generate_with_fallback")

        try:
            if plan_code is None and company_id is not None:
                from app.domains.credits.services.token_budget_service import get_plan_for_company
                plan_code = await get_plan_for_company(str(company_id))
        except Exception as exc:
            logger.warning(
                "[ProviderContainer] Plan lookup failed (graceful): %s", exc
            )

        check_request_budget_before_llm(
            prompt,
            system,
            plan_code=plan_code,
            agent_type=agent_type,
            company_id=company_id,
            user_id=user_id,
            expected_output_tokens=expected_output_tokens,
        )

        # WT-2022 P0.AIC1: per-company ai_credits_balance gate (single chokepoint).
        # check_request_budget_before_llm acima cobre teto per-request (Fase 3).
        # check_credit_budget cobre teto mensal per-tenant (overage protection).
        # fail-safe=True por default — outage de DB nao bloqueia LLM call.
        if company_id is not None:
            try:
                from app.shared.services.ai_credit_gate import check_credit_budget, AICreditExhausted
                from lia_config.database import AsyncSessionLocal
                async with AsyncSessionLocal() as _credit_db:
                    await check_credit_budget(
                        _credit_db,
                        str(company_id),
                        estimated_tokens=int(expected_output_tokens or 0),
                    )
            except AICreditExhausted:
                # bubble up — caller (route/agent) decide se converte em 429
                raise
            except Exception as _credit_exc:
                logger.warning(
                    "[ProviderContainer] ai_credit_gate failed (fail-safe ALLOW): %s",
                    _credit_exc,
                )

        # DEBT-002 (Sprint 2): canonical tracking inside the factory so ALL callers
        # get observability automatically — no per-caller wiring needed.
        from app.domains.credits.services.token_budget_service import track_llm_usage_start
        track_llm_usage_start(
            str(company_id) if company_id else None,
            model=self._primary,
            domain=str(domain),
            operation=str(operation),
        )

        from app.shared.resilience.circuit_breaker import CircuitBreakerError
        from app.shared.tracing import enrich_llm_span, get_tracer

        errors: list[str] = []
        _span = get_tracer().create_span("llm.generate_with_fallback")
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
                    record_fallback(self._primary, provider_name, tenant_id=self._tenant_id)
                # UC-P1-07: enrich span with LLM context
                _tokens = getattr(result, "usage", {}).get("total_tokens") if hasattr(result, "usage") else None
                enrich_llm_span(
                    _span,
                    tenant_id=str(company_id) if company_id else None,
                    user_id=str(user_id) if user_id else None,
                    model=provider_name,
                    tokens_used=_tokens,
                    provider=provider_name,
                    domain=str(domain),
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
                record_circuit_open(provider_name)
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

        from app.shared.errors import LIALLMError
        raise LIALLMError(
            message=f"Todos os provedores de LLM falharam para tenant={self._tenant_id}",
            code="LLM_ALL_PROVIDERS_FAILED",
            details={"tenant_id": self._tenant_id, "errors": errors},
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
            default = os.environ.get("LLM_DEFAULT_PROVIDER", "claude")
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
            # W2-012-B (2026-05-23): LGPD Art 33 per-tenant region from DB
            tenant_region = config.get("region")

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
                region=tenant_region,
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


def _resolve_provider_base_url(provider: str) -> str | None:
    """Resolve modelfarm proxy base URL for a provider from env vars.

    Task #1170 — mirror of the Anthropic ``AI_INTEGRATIONS_ANTHROPIC_BASE_URL``
    flow for Gemini. When the wrapper key (``AI_INTEGRATIONS_GEMINI_API_KEY``)
    is in use the SDK must be pointed at the modelfarm proxy, otherwise the
    wrapper key is sent to ``generativelanguage.googleapis.com`` and Google
    rejects it with ``400 API_KEY_INVALID`` — which is exactly what made
    ``jd_enrichment_node`` fall back to the canned "qualidade estimada: 20%"
    reply on every wizard turn.
    """
    if provider == "gemini":
        return os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL") or None
    if provider == "claude":
        return os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL") or None
    if provider == "openai":
        return os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL") or None
    return None


def _resolve_provider_api_key(provider: str) -> str:
    """Resolve API key for a provider from env vars (with AI_INTEGRATIONS_* fallback).

    Task #1170 — when the modelfarm proxy URL is set for Gemini, the wrapper
    key (``AI_INTEGRATIONS_GEMINI_API_KEY``) MUST take precedence over a
    stale ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY`` left over from a previous
    direct-Google setup. Otherwise the proxied endpoint receives a key it
    cannot validate. The same rule applies to Anthropic and OpenAI for
    consistency with the bootstrap injection in ``llm_bootstrap.py``.
    """
    if provider == "gemini":
        proxy = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
        wrapper = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY", "")
        if proxy and wrapper:
            return wrapper
        return (
            os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or wrapper
        )
    if provider == "claude":
        return (
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "")
        )
    if provider == "openai":
        return (
            os.environ.get("OPENAI_API_KEY")
            or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "")
        )
    return ""


def _resolve_provider_chain(
    tenant_id: str | None,
) -> tuple[str, list[str], dict[str, str]]:
    """Resolve (primary, fallback_order, tenant_api_keys) via ProviderContainer.

    Falls back to LLM_DEFAULT_PROVIDER env var + global FALLBACK_ORDER if the
    container lookup fails for any reason. Tenant-scoped API keys (loaded from
    DB by ``TenantProviderRegistry.load_from_db``) take precedence over env
    vars when present.
    """
    try:
        container = TenantProviderRegistry.get_instance().get_container(tenant_id)
        tenant_keys = {
            name: key for name, key in container._api_keys.items() if key
        }
        return container.primary_provider, container.fallback_order, tenant_keys
    except Exception as exc:
        logger.debug(
            "[create_tracked_llm] ProviderContainer lookup failed for tenant=%s: %s",
            tenant_id, exc,
        )
        primary = os.environ.get("LLM_DEFAULT_PROVIDER", "claude")
        return (
            primary,
            [primary] + [p for p in FALLBACK_ORDER if p != primary],
            {},
        )


def create_tracked_llm(
    temperature: float = 0.3,
    service_name: str = "",
    operation: str = "",
    max_output_tokens: int | None = None,
    tenant_id: str | None = None,
):
    """Build a LangChain chat LLM honoring per-tenant provider config.

    Resolution order:
      1. ProviderContainer for tenant_id → primary + fallback_order.
      2. Walk the chain and pick the first provider that has credentials
         available (env var). This avoids falling back to Gemini's
         Application Default Credentials (ADC) when GEMINI_API_KEY is
         missing — which crashed the canonical wizard graph.
      3. Raise a clear error if none of the providers have credentials.
    """
    primary, fallback_chain, tenant_keys = _resolve_provider_chain(tenant_id)

    try:
        from app.core.config import settings as _s
        model_map = {
            "gemini": getattr(_s, "GEMINI_MODEL", "gemini-2.0-flash"),
            "claude": getattr(_s, "ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            "openai": getattr(_s, "OPENAI_MODEL", "gpt-4o"),
        }
    except Exception:
        model_map = {
            "gemini": "gemini-2.0-flash",
            "claude": "claude-sonnet-4-5",
            "openai": "gpt-4o",
        }

    # P1 (audit 2026-06-05): timeout explicito nos clientes LLM. Sem isso o JD
    # enrichment fica exposto ao default ~10min do SDK (raiz do 502/hang do wizard).
    # Espelha app/domains/ai/services/llm.py:191. Resolucao defensiva (independe do _s acima).
    try:
        from app.core.config import settings as _s_timeout
        _llm_timeout = getattr(_s_timeout, "LLM_TIMEOUT_SECONDS", 120)
    except Exception:
        _llm_timeout = 120
    kwargs: dict = {"temperature": temperature, "streaming": True, "timeout": _llm_timeout}
    if max_output_tokens:
        kwargs["max_output_tokens"] = max_output_tokens

    metadata = {}
    if service_name:
        metadata["service_name"] = service_name
    if operation:
        metadata["operation"] = operation

    tried: list[str] = []
    for provider in fallback_chain:
        if provider not in model_map:
            continue
        api_key = tenant_keys.get(provider) or _resolve_provider_api_key(provider)
        if not api_key:
            tried.append(f"{provider}(no-key)")
            continue
        model_name = model_map[provider]
        try:
            if provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                gemini_kwargs = dict(kwargs)
                # Task #1170 — route through modelfarm proxy when configured.
                # ``ChatGoogleGenerativeAI`` merges ``base_url`` into
                # ``client_options.api_endpoint`` (chat_models.py L2025/L2072
                # in langchain-google-genai). Without this the wrapper key
                # from ``AI_INTEGRATIONS_GEMINI_API_KEY`` is sent to
                # ``generativelanguage.googleapis.com`` and Google answers
                # ``400 API_KEY_INVALID`` — the exact failure that made
                # ``jd_enrichment`` fall back to "qualidade estimada: 20%"
                # on every wizard turn.
                gemini_base_url = _resolve_provider_base_url("gemini")
                if gemini_base_url:
                    gemini_kwargs.setdefault("base_url", gemini_base_url)
                    gemini_kwargs.setdefault("transport", "rest")
                llm = ChatGoogleGenerativeAI(
                    model=model_name, google_api_key=api_key, **gemini_kwargs,
                )
            elif provider == "claude":
                from langchain_anthropic import ChatAnthropic
                # Sprint F.1: normalize max_output_tokens (gemini convention)
                # → max_tokens (anthropic/openai convention). Without this
                # remap, ChatAnthropic raises TypeError and the chain falls
                # through to the broken modelfarm proxy for Gemini.
                claude_kwargs = {k: v for k, v in kwargs.items() if k != "max_output_tokens"}
                if "max_output_tokens" in kwargs:
                    claude_kwargs["max_tokens"] = kwargs["max_output_tokens"]
                # Sprint F.1: route through modelfarm proxy when wrapper key
                # is in use (AI_INTEGRATIONS_ANTHROPIC_API_KEY) — the proxy
                # exchanges the wrapper for the real upstream key.
                claude_base = _resolve_provider_base_url("claude")
                if claude_base:
                    claude_kwargs["base_url"] = claude_base
                llm = ChatAnthropic(model=model_name, api_key=api_key, **claude_kwargs)
            else:  # openai
                from langchain_openai import ChatOpenAI
                # Same normalization as claude — OpenAI also uses max_tokens.
                openai_kwargs = {k: v for k, v in kwargs.items() if k != "max_output_tokens"}
                if "max_output_tokens" in kwargs:
                    openai_kwargs["max_tokens"] = kwargs["max_output_tokens"]
                llm = ChatOpenAI(model=model_name, api_key=api_key, **openai_kwargs)
        except Exception as exc:
            tried.append(f"{provider}({type(exc).__name__})")
            logger.warning(
                "[create_tracked_llm] provider=%s instantiation failed: %s",
                provider, exc,
            )
            continue

        if provider != primary:
            logger.warning(
                "[create_tracked_llm] tenant=%s primary=%s missing credentials; "
                "falling back to provider=%s",
                tenant_id, primary, provider,
            )
        return llm

    raise RuntimeError(
        f"create_tracked_llm: no LLM provider has credentials available "
        f"(tenant={tenant_id}, tried={tried})"
    )


# ---------------------------------------------------------------------------
# Voice Provider Registry — auto-selects voice strategy per tenant
# ---------------------------------------------------------------------------

_VOICE_PROVIDER_MAP: dict[str, str] = {
    "gemini": "gemini_live",
    "openai": "openai_realtime",
}


def get_voice_provider_for_tenant(
    tenant_id: str | None = None,
    primary_provider: str | None = None,
) -> "VoiceStreamProviderABC":  # noqa: F821 (forward ref string)
    """
    Get the appropriate VoiceStreamProvider for a tenant based on their LLM config.

    Decision logic:
      - Gemini tenant → GeminiLiveVoiceProvider (native multimodal)
      - OpenAI tenant → OpenAIRealtimeVoiceProvider (native multimodal)
      - Claude / other → CompositeVoiceProvider (STT Gemini + LLM tenant + TTS Gemini)
    """
    from app.shared.providers.voice_composite import CompositeVoiceProvider
    from app.shared.providers.voice_gemini_live import GeminiLiveVoiceProvider
    from app.shared.providers.voice_openai_realtime import OpenAIRealtimeVoiceProvider
    from app.shared.providers.voice_provider import VoiceStreamProviderABC

    resolved_provider = primary_provider
    if not resolved_provider:
        container = get_provider_for_tenant(tenant_id)
        resolved_provider = container.primary_provider

    voice_type = _VOICE_PROVIDER_MAP.get(resolved_provider)

    if voice_type == "gemini_live":
        provider = GeminiLiveVoiceProvider()
        logger.info(
            "[VoiceProviderRegistry] tenant=%s → GeminiLiveVoiceProvider (native)",
            tenant_id,
        )
        return provider

    if voice_type == "openai_realtime":
        provider = OpenAIRealtimeVoiceProvider()
        logger.info(
            "[VoiceProviderRegistry] tenant=%s → OpenAIRealtimeVoiceProvider (native)",
            tenant_id,
        )
        return provider

    provider = CompositeVoiceProvider(
        tenant_id=tenant_id,
        llm_provider_name=resolved_provider or "claude",
    )
    logger.info(
        "[VoiceProviderRegistry] tenant=%s → CompositeVoiceProvider (stt+%s+tts)",
        tenant_id,
        resolved_provider,
    )
    return provider
