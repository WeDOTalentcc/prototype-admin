"""Tests for A2+A3: EmbeddingService company_id wiring + factory OpenAI BYOK branch.

A2: EmbeddingService passes company_id to EmbeddingProviderFactory
A3: embedding_factory respects routing["embedding"] + api_keys["openai"] for BYOK
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBuildFallbackOrderRouting:
    """A3 Gap 2: _build_fallback_order respects tenant routing config."""

    def setup_method(self):
        """Clear factory instances before each test."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory
        EmbeddingProviderFactory.clear()
        # Register mock providers so they appear in _providers
        mock_gemini = MagicMock()
        mock_gemini._provider_name = "gemini"
        mock_openai = MagicMock()
        mock_openai._provider_name = "openai"
        EmbeddingProviderFactory._providers["gemini"] = lambda: MagicMock(
            provider_name="gemini", default_model="gemini-embed", dimensions=768
        )
        EmbeddingProviderFactory._providers["openai"] = lambda: MagicMock(
            provider_name="openai", default_model="text-embedding-3-small", dimensions=768
        )

    def teardown_method(self):
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory
        EmbeddingProviderFactory.clear()
        EmbeddingProviderFactory._providers.pop("gemini", None)
        EmbeddingProviderFactory._providers.pop("openai", None)

    def test_routing_openai_puts_openai_first(self):
        """tenant_config routing["embedding"]="openai" → openai first in fallback order."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        tenant_config = {"routing": {"embedding": "openai"}}
        order = EmbeddingProviderFactory._build_fallback_order(
            None, tenant_config=tenant_config
        )
        assert order[0] == "openai", (
            f"Expected openai first when routing=[openai], got: {order}"
        )

    def test_routing_gemini_puts_gemini_first(self):
        """tenant_config routing["embedding"]="gemini" → gemini first in fallback order."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory
        import os
        with patch.dict(os.environ, {"EMBEDDING_DEFAULT_PROVIDER": "openai"}):
            tenant_config = {"routing": {"embedding": "gemini"}}
            order = EmbeddingProviderFactory._build_fallback_order(
                None, tenant_config=tenant_config
            )
        assert order[0] == "gemini", (
            f"Expected gemini first when routing=[gemini], got: {order}"
        )

    def test_preferred_provider_overrides_routing(self):
        """Explicit preferred_provider always wins over routing config."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        tenant_config = {"routing": {"embedding": "openai"}}
        order = EmbeddingProviderFactory._build_fallback_order(
            "gemini", tenant_config=tenant_config
        )
        assert order[0] == "gemini", (
            f"Explicit preferred_provider should override routing, got: {order}"
        )

    def test_no_routing_uses_env_default(self):
        """When tenant_config has no routing, falls back to EMBEDDING_DEFAULT_PROVIDER."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory
        import os
        with patch.dict(os.environ, {"EMBEDDING_DEFAULT_PROVIDER": "gemini"}):
            order = EmbeddingProviderFactory._build_fallback_order(
                None, tenant_config=None
            )
        assert "gemini" in order


class TestGetTenantProviderOpenAI:
    """A3 Gap 1: _get_tenant_provider returns OpenAIEmbeddingProvider for BYOK openai key."""

    def test_openai_byok_key_returns_openai_provider(self):
        """tenant_config with api_keys["openai"] → _get_tenant_provider returns OpenAI provider."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory
        from app.shared.providers.embedding_openai import OpenAIEmbeddingProvider

        tenant_id = "test-company-byok-001"
        tenant_config = {
            "providers": {
                "openai": {"api_key": "sk-test-byok-key-123"}
            },
            "routing": {"embedding": "openai"},
        }

        with patch("app.shared.tenant_llm_context._tenant_configs", {tenant_id: tenant_config}):
            provider = EmbeddingProviderFactory._get_tenant_provider("openai", company_id=tenant_id)

        assert isinstance(provider, OpenAIEmbeddingProvider), (
            f"Expected OpenAIEmbeddingProvider, got {type(provider)}"
        )
        # Verify tenant key was passed (stored as _tenant_api_key)
        assert provider._tenant_api_key == "sk-test-byok-key-123"

    def test_no_byok_key_returns_global_provider(self):
        """Tenant without openai key → falls back to global provider instance."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        EmbeddingProviderFactory._providers["openai"] = lambda: MagicMock(
            provider_name="openai", default_model="text-embedding-3-small", dimensions=768
        )

        tenant_id = "test-company-no-byok"
        tenant_config = {"providers": {}}  # no openai key

        with patch("app.shared.tenant_llm_context._tenant_configs", {tenant_id: tenant_config}):
            # Should not raise, should return global provider
            provider = EmbeddingProviderFactory._get_tenant_provider("openai", company_id=tenant_id)

        # It should return whatever global provider is registered (not OpenAIEmbeddingProvider with tenant key)
        assert provider is not None

        EmbeddingProviderFactory._providers.pop("openai", None)
        EmbeddingProviderFactory.clear()


class TestEmbeddingServiceCompanyIdWiring:
    """A2: EmbeddingService methods accept and forward company_id."""

    def test_generate_embedding_accepts_company_id(self):
        """generate_embedding has company_id kwarg in signature."""
        import inspect
        from app.shared.intelligence.embedding_service import EmbeddingService

        sig = inspect.signature(EmbeddingService.generate_embedding)
        assert "company_id" in sig.parameters, (
            "generate_embedding must accept company_id kwarg for BYOK routing"
        )

    def test_generate_embedding_with_metadata_accepts_company_id(self):
        """generate_embedding_with_metadata has company_id kwarg."""
        import inspect
        from app.shared.intelligence.embedding_service import EmbeddingService

        sig = inspect.signature(EmbeddingService.generate_embedding_with_metadata)
        assert "company_id" in sig.parameters

    def test_generate_batch_embeddings_accepts_company_id(self):
        """generate_batch_embeddings has company_id kwarg."""
        import inspect
        from app.shared.intelligence.embedding_service import EmbeddingService

        sig = inspect.signature(EmbeddingService.generate_batch_embeddings)
        assert "company_id" in sig.parameters

    def test_generate_batch_embeddings_with_metadata_accepts_company_id(self):
        """generate_batch_embeddings_with_metadata has company_id kwarg."""
        import inspect
        from app.shared.intelligence.embedding_service import EmbeddingService

        sig = inspect.signature(EmbeddingService.generate_batch_embeddings_with_metadata)
        assert "company_id" in sig.parameters
