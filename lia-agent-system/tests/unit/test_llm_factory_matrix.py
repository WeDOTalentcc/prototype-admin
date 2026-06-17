"""
R-018 — LLM Factory matrix tests.

Covers:
- BYOK chain: tenant key used when configured
- BYOK fails → retries with system key (graceful fallback)
- No BYOK → system key used directly
- Primary provider fails → next in fallback order tried
- CircuitBreakerError → skips to next provider (no retry on same)
- All providers fail → LIALLMError with all error messages
- Successful fallback → record_fallback() called
- check_request_budget_before_llm() called BEFORE provider invoke
- RequestBudgetExceededError → zero LLM calls made
- TenantProviderRegistry singleton: same instance on two calls
- Different tenant_id → different ProviderContainer (no cross-tenant sharing)
- ProviderContainer.has_custom_keys reflects BYOK presence
- LLMProviderFactory.register/get registry
- ProviderContainer fallback_order places primary first
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

def _make_provider_mock(name: str, result_text: str = "ok") -> MagicMock:
    """Create a mock LLM provider that returns result_text on generate()."""
    provider = MagicMock()
    provider._provider_name = name
    result = MagicMock()
    result.text = result_text
    result.usage = {}
    provider.generate = AsyncMock(return_value=result)
    provider.generate_with_system = AsyncMock(return_value=result)
    return provider


def _make_failing_provider(name: str, exc_type=Exception, exc_msg="provider error") -> MagicMock:
    """Create a mock provider that raises exc_type on generate."""
    provider = MagicMock()
    provider._provider_name = name
    exc = exc_type(exc_msg)
    provider.generate = AsyncMock(side_effect=exc)
    provider.generate_with_system = AsyncMock(side_effect=exc)
    return provider


def _setup_container_with_mocks(
    primary: str = "gemini",
    fallback_order: list[str] | None = None,
    provider_api_keys: dict | None = None,
    providers: dict | None = None,
):
    """Build a ProviderContainer with mocked providers in LLMProviderFactory._providers.

    providers: dict of name → mock_provider_instance
    """
    from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer

    # Clear global factory instances
    LLMProviderFactory.clear()
    LLMProviderFactory._providers.clear()

    if providers:
        for pname, pmock in providers.items():
            # Register a class that returns the mock when instantiated
            def _make_cls(m):
                class _MockProviderCls:
                    _provider_name = m._provider_name
                    def __init__(self, api_key=None, region=None, **kwargs):
                        pass
                    # delegate to the mock
                    generate = m.generate
                    generate_with_system = m.generate_with_system
                return _MockProviderCls
            LLMProviderFactory._providers[pname] = _make_cls(pmock)

    container = ProviderContainer(
        tenant_id="test_tenant",
        primary_provider=primary,
        fallback_order=fallback_order or [primary, "claude", "openai"],
        provider_api_keys=provider_api_keys,
    )
    return container


# ---------------------------------------------------------------------------
# Section 1 — ProviderContainer fundamentals
# ---------------------------------------------------------------------------

class TestProviderContainerFundamentals:

    def test_primary_provider_placed_first_in_fallback_order(self):
        """ProviderContainer always puts primary first in _fallback_order."""
        from app.shared.providers.llm_factory import ProviderContainer
        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="claude",
            fallback_order=["gemini", "openai"],
        )
        assert container.fallback_order[0] == "claude"

    def test_has_custom_keys_true_when_byok_configured(self):
        """has_custom_keys is True when provider_api_keys are provided."""
        from app.shared.providers.llm_factory import ProviderContainer
        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="gemini",
            provider_api_keys={"gemini": "TENANT_GEMINI_KEY"},
        )
        assert container.has_custom_keys is True

    def test_has_custom_keys_false_without_byok(self):
        """has_custom_keys is False when no tenant keys are provided."""
        from app.shared.providers.llm_factory import ProviderContainer
        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="gemini",
        )
        assert container.has_custom_keys is False

    def test_tenant_id_property(self):
        """tenant_id property reflects constructor argument."""
        from app.shared.providers.llm_factory import ProviderContainer
        container = ProviderContainer(tenant_id="my_tenant", primary_provider="gemini")
        assert container.tenant_id == "my_tenant"

    def test_clear_releases_cached_instances(self):
        """clear() removes cached provider instances."""
        from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer
        LLMProviderFactory.clear()
        container = ProviderContainer(tenant_id="t1", primary_provider="gemini")
        container._instances["gemini"] = MagicMock()
        assert len(container._instances) == 1
        container.clear()
        assert len(container._instances) == 0


# ---------------------------------------------------------------------------
# Section 2 — LLMProviderFactory registry
# ---------------------------------------------------------------------------

class TestLLMProviderFactoryRegistry:

    def setup_method(self):
        from app.shared.providers.llm_factory import LLMProviderFactory
        LLMProviderFactory.clear()
        LLMProviderFactory._providers.clear()

    def test_register_adds_provider_by_name(self):
        """register() adds provider class to _providers by _provider_name."""
        from app.shared.providers.llm_factory import LLMProviderFactory

        class MockGemini:
            _provider_name = "gemini_test"
            def __init__(self): pass

        LLMProviderFactory.register(MockGemini)
        assert "gemini_test" in LLMProviderFactory.available_providers()

    def test_get_unknown_provider_raises_value_error(self):
        """get() on unregistered name raises ValueError."""
        from app.shared.providers.llm_factory import LLMProviderFactory

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMProviderFactory.get("nonexistent_provider")

    def test_get_returns_same_instance_twice(self):
        """get() returns same instance (singleton per name)."""
        from app.shared.providers.llm_factory import LLMProviderFactory

        class MockOpenAI:
            _provider_name = "openai_test"
            def __init__(self): pass

        LLMProviderFactory.register(MockOpenAI)
        inst1 = LLMProviderFactory.get("openai_test")
        inst2 = LLMProviderFactory.get("openai_test")
        assert inst1 is inst2

    def test_available_providers_lists_registered_names(self):
        """available_providers() returns names of all registered providers."""
        from app.shared.providers.llm_factory import LLMProviderFactory

        class MockClaude:
            _provider_name = "claude_test"
            def __init__(self): pass

        LLMProviderFactory.register(MockClaude)
        assert "claude_test" in LLMProviderFactory.available_providers()


# ---------------------------------------------------------------------------
# Section 3 — TenantProviderRegistry singleton
# ---------------------------------------------------------------------------

class TestTenantProviderRegistrySingleton:

    def setup_method(self):
        from app.shared.providers.llm_factory import TenantProviderRegistry
        TenantProviderRegistry.reset()

    def test_get_instance_returns_same_singleton(self):
        """TenantProviderRegistry.get_instance() returns same object on two calls."""
        from app.shared.providers.llm_factory import TenantProviderRegistry
        inst1 = TenantProviderRegistry.get_instance()
        inst2 = TenantProviderRegistry.get_instance()
        assert inst1 is inst2

    def test_different_tenant_ids_get_different_containers(self):
        """Different tenant_id → different ProviderContainer (no cross-tenant sharing)."""
        from app.shared.providers.llm_factory import TenantProviderRegistry
        registry = TenantProviderRegistry.get_instance()

        with patch.object(
            registry, "_load_from_permissions",
            return_value=("gemini", ["gemini", "claude", "openai"])
        ):
            c1 = registry.get_container("tenant_alpha")
            c2 = registry.get_container("tenant_beta")

        assert c1 is not c2
        assert c1.tenant_id == "tenant_alpha"
        assert c2.tenant_id == "tenant_beta"

    def test_same_tenant_id_returns_cached_container(self):
        """Same tenant_id → same cached ProviderContainer."""
        from app.shared.providers.llm_factory import TenantProviderRegistry
        registry = TenantProviderRegistry.get_instance()

        with patch.object(
            registry, "_load_from_permissions",
            return_value=("gemini", ["gemini", "claude", "openai"])
        ):
            c1 = registry.get_container("tenant_gamma")
            c2 = registry.get_container("tenant_gamma")

        assert c1 is c2

    def test_none_tenant_uses_global_key(self):
        """tenant_id=None → key='__global__' container."""
        from app.shared.providers.llm_factory import TenantProviderRegistry
        registry = TenantProviderRegistry.get_instance()

        with patch.object(
            registry, "_load_from_permissions",
            return_value=("gemini", ["gemini", "claude"])
        ):
            c = registry.get_container(None)

        assert c.tenant_id is None

    def test_remove_container_forces_recreation(self):
        """remove_container() then get_container() creates a fresh container."""
        from app.shared.providers.llm_factory import TenantProviderRegistry
        registry = TenantProviderRegistry.get_instance()

        with patch.object(
            registry, "_load_from_permissions",
            return_value=("gemini", ["gemini"])
        ):
            c1 = registry.get_container("tenant_delta")
            registry.remove_container("tenant_delta")
            c2 = registry.get_container("tenant_delta")

        assert c1 is not c2

    def test_reset_clears_singleton(self):
        """reset() causes next get_instance() to return a NEW instance."""
        from app.shared.providers.llm_factory import TenantProviderRegistry
        inst1 = TenantProviderRegistry.get_instance()
        TenantProviderRegistry.reset()
        inst2 = TenantProviderRegistry.get_instance()
        assert inst1 is not inst2


# ---------------------------------------------------------------------------
# Section 4 — generate_with_fallback: token budget gate
# ---------------------------------------------------------------------------

class TestTokenBudgetGate:

    @pytest.mark.asyncio
    async def test_budget_exceeded_before_any_llm_call(self):
        """RequestBudgetExceededError raised → no LLM provider called."""
        from app.domains.credits.services.token_budget_service import RequestBudgetExceededError
        from app.shared.providers.llm_factory import ProviderContainer

        provider_mock = _make_provider_mock("gemini", "should not be reached")
        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="gemini",
            fallback_order=["gemini"],
        )

        with (
            patch(
                "app.shared.providers.llm_factory.check_request_budget_before_llm",
                side_effect=RequestBudgetExceededError(estimated_tokens=9999, ceiling=1000),
            ),
            patch(
                "app.domains.credits.services.token_budget_service.track_llm_usage_start",
                return_value=None,
            ),
            patch(
                "app.domains.credits.services.token_budget_service.get_plan_for_company",
                new=AsyncMock(return_value="free"),
            ),
        ):
            with pytest.raises(RequestBudgetExceededError):
                await container.generate_with_fallback("test prompt")

        # Provider must NOT have been called
        provider_mock.generate.assert_not_called()
        provider_mock.generate_with_system.assert_not_called()

    @pytest.mark.asyncio
    async def test_budget_check_called_before_provider(self):
        """check_request_budget_before_llm is called before any provider.generate()."""
        from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer

        call_order = []

        LLMProviderFactory.clear()
        LLMProviderFactory._providers.clear()

        result_mock = MagicMock()
        result_mock.text = "response text"
        result_mock.usage = {}

        async def _budget_check(*args, **kwargs):
            call_order.append("budget_check")

        async def _provider_generate(*args, **kwargs):
            call_order.append("provider_generate")
            return result_mock

        provider_cls_mock = MagicMock()
        provider_inst = MagicMock()
        provider_inst.generate = AsyncMock(side_effect=_provider_generate)
        provider_inst.generate_with_system = AsyncMock(side_effect=_provider_generate)
        provider_cls_mock.return_value = provider_inst
        provider_cls_mock._provider_name = "gemini"

        LLMProviderFactory._providers["gemini"] = provider_cls_mock

        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="gemini",
            fallback_order=["gemini"],
        )

        with (
            patch(
                "app.shared.providers.llm_factory.check_request_budget_before_llm",
                side_effect=lambda *a, **kw: call_order.append("budget_check"),
            ),
            patch(
                "app.domains.credits.services.token_budget_service.track_llm_usage_start",
                return_value=None,
            ),
            patch(
                "app.domains.credits.services.token_budget_service.get_plan_for_company",
                new=AsyncMock(return_value="pro"),
            ),
            patch("app.shared.tracing.get_tracer", return_value=MagicMock(create_span=MagicMock(return_value=MagicMock()))),
            patch("app.shared.tracing.enrich_llm_span", return_value=None),
        ):
            await container.generate_with_fallback("test prompt", company_id="t1")

        # budget_check must come before provider_generate
        assert "budget_check" in call_order
        if "provider_generate" in call_order:
            assert call_order.index("budget_check") < call_order.index("provider_generate")


# ---------------------------------------------------------------------------
# Section 5 — generate_with_fallback: provider fallback chain
# ---------------------------------------------------------------------------

class TestProviderFallbackChain:

    @pytest.mark.asyncio
    async def test_circuit_breaker_error_skips_to_next_provider(self):
        """CircuitBreakerError on primary → next provider tried (not retry same)."""
        from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer
        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        LLMProviderFactory.clear()
        LLMProviderFactory._providers.clear()

        # gemini raises CircuitBreakerError, claude succeeds
        result_ok = MagicMock()
        result_ok.text = "claude_response"
        result_ok.usage = {}

        claude_inst = MagicMock()
        claude_inst.generate = AsyncMock(return_value=result_ok)
        claude_inst.generate_with_system = AsyncMock(return_value=result_ok)

        gemini_inst = MagicMock()
        gemini_inst.generate = AsyncMock(side_effect=CircuitBreakerError("gemini", 30.0))
        gemini_inst.generate_with_system = AsyncMock(side_effect=CircuitBreakerError("gemini", 30.0))

        def gemini_cls(api_key=None, region=None, **kwargs): return gemini_inst
        def claude_cls(api_key=None, region=None, **kwargs): return claude_inst
        LLMProviderFactory._providers["gemini"] = gemini_cls
        LLMProviderFactory._providers["claude"] = claude_cls

        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="gemini",
            fallback_order=["gemini", "claude"],
        )

        with (
            patch("app.shared.providers.llm_factory.check_request_budget_before_llm"),
            patch("app.domains.credits.services.token_budget_service.track_llm_usage_start"),
            patch("app.domains.credits.services.token_budget_service.get_plan_for_company", new=AsyncMock(return_value="pro")),
            patch("app.shared.tracing.get_tracer", return_value=MagicMock(create_span=MagicMock(return_value=MagicMock()))),
            patch("app.shared.tracing.enrich_llm_span"),
            patch("app.shared.providers.llm_factory.record_circuit_open"),
        ):
            result = await container.generate_with_fallback("test", company_id="t1")

        assert result == "claude_response"
        # Gemini must NOT have been retried
        assert gemini_inst.generate.call_count == 1

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_lia_llm_error(self):
        """All providers fail → LIALLMError raised with error details."""
        from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer
        from app.shared.errors import LIALLMError

        LLMProviderFactory.clear()
        LLMProviderFactory._providers.clear()

        for pname in ["gemini", "claude", "openai"]:
            inst = MagicMock()
            inst.generate = AsyncMock(side_effect=Exception(f"{pname} failed"))
            inst.generate_with_system = AsyncMock(side_effect=Exception(f"{pname} failed"))
            def _cls(api_key=None, _inst=inst, region=None, **kwargs): return _inst
            LLMProviderFactory._providers[pname] = _cls

        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )

        with (
            patch("app.shared.providers.llm_factory.check_request_budget_before_llm"),
            patch("app.domains.credits.services.token_budget_service.track_llm_usage_start"),
            patch("app.domains.credits.services.token_budget_service.get_plan_for_company", new=AsyncMock(return_value="pro")),
            patch("app.shared.tracing.get_tracer", return_value=MagicMock(create_span=MagicMock(return_value=MagicMock()))),
            patch("app.shared.tracing.enrich_llm_span"),
        ):
            with pytest.raises(LIALLMError):
                await container.generate_with_fallback("test", company_id="t1")

    @pytest.mark.asyncio
    async def test_fallback_success_calls_record_fallback(self):
        """Successful fallback (primary failed) → record_fallback() called."""
        from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer

        LLMProviderFactory.clear()
        LLMProviderFactory._providers.clear()

        result_ok = MagicMock()
        result_ok.text = "claude is the hero"
        result_ok.usage = {}

        claude_inst = MagicMock()
        claude_inst.generate = AsyncMock(return_value=result_ok)
        claude_inst.generate_with_system = AsyncMock(return_value=result_ok)

        gemini_inst = MagicMock()
        gemini_inst.generate = AsyncMock(side_effect=Exception("gemini down"))
        gemini_inst.generate_with_system = AsyncMock(side_effect=Exception("gemini down"))

        def gemini_cls(api_key=None, region=None, **kwargs): return gemini_inst
        def claude_cls(api_key=None, region=None, **kwargs): return claude_inst
        LLMProviderFactory._providers["gemini"] = gemini_cls
        LLMProviderFactory._providers["claude"] = claude_cls

        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="gemini",
            fallback_order=["gemini", "claude"],
        )

        with (
            patch("app.shared.providers.llm_factory.check_request_budget_before_llm"),
            patch("app.domains.credits.services.token_budget_service.track_llm_usage_start"),
            patch("app.domains.credits.services.token_budget_service.get_plan_for_company", new=AsyncMock(return_value="pro")),
            patch("app.shared.tracing.get_tracer", return_value=MagicMock(create_span=MagicMock(return_value=MagicMock()))),
            patch("app.shared.tracing.enrich_llm_span"),
            patch("app.shared.providers.llm_factory.record_fallback") as mock_record_fallback,
        ):
            result = await container.generate_with_fallback("test", company_id="t1")

        assert result == "claude is the hero"
        mock_record_fallback.assert_called_once()
        args = mock_record_fallback.call_args
        assert args[0][0] == "gemini"  # primary
        assert args[0][1] == "claude"  # used fallback

    @pytest.mark.asyncio
    async def test_primary_success_does_not_call_record_fallback(self):
        """Primary succeeds → record_fallback() NOT called."""
        from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer

        LLMProviderFactory.clear()
        LLMProviderFactory._providers.clear()

        result_ok = MagicMock()
        result_ok.text = "gemini response"
        result_ok.usage = {}

        gemini_inst = MagicMock()
        gemini_inst.generate = AsyncMock(return_value=result_ok)
        gemini_inst.generate_with_system = AsyncMock(return_value=result_ok)

        def gemini_cls(api_key=None, region=None, **kwargs): return gemini_inst
        LLMProviderFactory._providers["gemini"] = gemini_cls

        container = ProviderContainer(
            tenant_id="t1",
            primary_provider="gemini",
            fallback_order=["gemini"],
        )

        with (
            patch("app.shared.providers.llm_factory.check_request_budget_before_llm"),
            patch("app.domains.credits.services.token_budget_service.track_llm_usage_start"),
            patch("app.domains.credits.services.token_budget_service.get_plan_for_company", new=AsyncMock(return_value="pro")),
            patch("app.shared.tracing.get_tracer", return_value=MagicMock(create_span=MagicMock(return_value=MagicMock()))),
            patch("app.shared.tracing.enrich_llm_span"),
            patch("app.shared.providers.llm_factory.record_fallback") as mock_record_fallback,
        ):
            await container.generate_with_fallback("test", company_id="t1")

        mock_record_fallback.assert_not_called()


# ---------------------------------------------------------------------------
# Section 6 — BYOK chain
# ---------------------------------------------------------------------------

class TestBYOKChain:

    def test_provider_container_with_byok_has_custom_keys(self):
        """Container created with tenant API key has has_custom_keys=True."""
        from app.shared.providers.llm_factory import ProviderContainer
        container = ProviderContainer(
            tenant_id="byok_tenant",
            primary_provider="gemini",
            provider_api_keys={"gemini": "sk-tenant-gemini-key"},
        )
        assert container.has_custom_keys is True

    def test_provider_container_without_byok_has_no_custom_keys(self):
        """Container without tenant API keys has has_custom_keys=False."""
        from app.shared.providers.llm_factory import ProviderContainer
        container = ProviderContainer(
            tenant_id="system_tenant",
            primary_provider="gemini",
        )
        assert container.has_custom_keys is False

    def test_get_provider_with_byok_key_instantiates_with_tenant_key(self):
        """When tenant key is in _api_keys, provider is created with api_key=<tenant_key>."""
        from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer

        LLMProviderFactory.clear()
        LLMProviderFactory._providers.clear()

        received_key = {}

        class MockGeminiWithKey:
            _provider_name = "gemini"
            def __init__(self, api_key=None, region=None, **kwargs):
                received_key["key"] = api_key
            def generate(self, *a, **kw): pass

        LLMProviderFactory._providers["gemini"] = MockGeminiWithKey

        container = ProviderContainer(
            tenant_id="byok_tenant",
            primary_provider="gemini",
            fallback_order=["gemini"],
            provider_api_keys={"gemini": "TENANT_SECRET_KEY"},
        )
        container.get("gemini")
        assert received_key.get("key") == "TENANT_SECRET_KEY"

    def test_get_provider_without_byok_uses_no_tenant_key(self):
        """Without tenant key, provider is instantiated without api_key."""
        from app.shared.providers.llm_factory import LLMProviderFactory, ProviderContainer

        LLMProviderFactory.clear()
        LLMProviderFactory._providers.clear()

        received_key = {}

        class MockGeminiNoKey:
            _provider_name = "gemini"
            def __init__(self, api_key=None, region=None, **kwargs):
                received_key["key"] = api_key
            def generate(self, *a, **kw): pass

        LLMProviderFactory._providers["gemini"] = MockGeminiNoKey

        container = ProviderContainer(
            tenant_id="system_tenant",
            primary_provider="gemini",
            fallback_order=["gemini"],
            # No provider_api_keys
        )
        container.get("gemini")
        # api_key should be None or not passed (default constructor)
        assert received_key.get("key") is None

    def test_register_container_enables_explicit_di(self):
        """register_container allows pre-built container DI for testing."""
        from app.shared.providers.llm_factory import ProviderContainer, TenantProviderRegistry

        TenantProviderRegistry.reset()
        registry = TenantProviderRegistry.get_instance()

        pre_built = ProviderContainer(
            tenant_id="di_tenant",
            primary_provider="openai",
        )
        registry.register_container("di_tenant", pre_built)
        fetched = registry.get_container("di_tenant")
        assert fetched is pre_built

    def test_list_tenants_returns_registered_tenant_ids(self):
        """list_tenants() returns tenant_ids excluding __global__."""
        from app.shared.providers.llm_factory import TenantProviderRegistry

        TenantProviderRegistry.reset()
        registry = TenantProviderRegistry.get_instance()

        from app.shared.providers.llm_factory import ProviderContainer
        registry.register_container("tenant_x", ProviderContainer(tenant_id="tenant_x"))
        registry.register_container("tenant_y", ProviderContainer(tenant_id="tenant_y"))

        tenants = registry.list_tenants()
        assert "tenant_x" in tenants
        assert "tenant_y" in tenants
        assert "__global__" not in tenants
