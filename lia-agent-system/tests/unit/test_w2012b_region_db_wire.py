"""
Anti-regressão · W2-012-B (2026-05-23) — Region DB wiring full path.

Verifica que `region` flui de:
1. LLMConfigRequest payload → upsert → DB row
2. DB row → get_tenant_llm_config dict
3. dict → ProviderContainer(region=...)
4. ProviderContainer → provider class(region=...) on instantiation

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W2-012-B).
"""
from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLLMConfigSchemaHasRegion:
    """LLMConfigRequest/Response têm campo region."""

    def test_request_accepts_region(self) -> None:
        from app.api.v1.llm_config import LLMConfigRequest

        req = LLMConfigRequest(region="sa-east-1")
        assert req.region == "sa-east-1"

    def test_request_region_default_none(self) -> None:
        from app.api.v1.llm_config import LLMConfigRequest

        req = LLMConfigRequest()
        assert req.region is None

    def test_response_has_region_field(self) -> None:
        from app.api.v1.llm_config import LLMConfigResponse

        resp = LLMConfigResponse(
            company_id="t",
            primary_provider="gemini",
            fallback_order=["gemini"],
            providers={},
            routing={},
            is_active=True,
            region="us-east-1",
        )
        assert resp.region == "us-east-1"


class TestLlmConfigRepositoryAcceptsRegion:
    """Repository.upsert aceita region kwarg."""

    def test_upsert_signature_has_region(self) -> None:
        from app.domains.ai.repositories.llm_config_repository import LlmConfigRepository

        sig = inspect.signature(LlmConfigRepository.upsert)
        params = list(sig.parameters.keys())
        assert "region" in params


class TestTenantContextReturnsRegion:
    """get_tenant_llm_config inclui region no dict result."""

    def test_get_tenant_config_dict_has_region_key(self) -> None:
        """Source-level: dict construction inclui chave region."""
        import inspect
        from app.shared import tenant_llm_context

        src = inspect.getsource(tenant_llm_context.get_tenant_llm_config)
        assert "\"region\": row.region" in src, (
            "get_tenant_llm_config DEVE incluir region no dict"
        )


class TestProviderContainerAcceptsRegion:
    """ProviderContainer.__init__ aceita region + propaga para providers."""

    def test_init_accepts_region(self) -> None:
        from app.shared.providers.llm_factory import ProviderContainer

        sig = inspect.signature(ProviderContainer.__init__)
        params = list(sig.parameters.keys())
        assert "region" in params

    def test_region_stored_in_self_region(self) -> None:
        from app.shared.providers.llm_factory import ProviderContainer

        container = ProviderContainer(
            tenant_id="t",
            primary_provider="gemini",
            region="sa-east-1",
        )
        assert container._region == "sa-east-1"

    def test_region_default_none(self) -> None:
        from app.shared.providers.llm_factory import ProviderContainer

        container = ProviderContainer(tenant_id="t", primary_provider="gemini")
        assert container._region is None


class TestProviderContainerPassesRegionToProviderClass:
    """ProviderContainer.get passa region pra provider class no construtor."""

    def test_provider_class_receives_region(self) -> None:
        """Source-level: get method invoca provider class com region kwarg."""
        import inspect
        from app.shared.providers.llm_factory import ProviderContainer

        src = inspect.getsource(ProviderContainer.get)
        assert "region=self._region" in src, (
            "ProviderContainer.get DEVE passar region=self._region "
            "para provider class no construtor"
        )


class TestLoadFromDbReadsRegion:
    """TenantProviderRegistry.load_from_db lê region do DB config."""

    def test_load_from_db_reads_region_from_config_dict(self) -> None:
        import inspect
        from app.shared.providers.llm_factory import TenantProviderRegistry

        src = inspect.getsource(TenantProviderRegistry.load_from_db)
        assert "config.get(\"region\")" in src or "tenant_region" in src, (
            "load_from_db DEVE ler region do config dict (W2-012-B)"
        )
