"""Tests for create_tracked_llm credential-based provider fallback (Task #965).

Regression: the canonical wizard graph crashed because create_tracked_llm
defaulted to Gemini and tried to use Application Default Credentials when
GEMINI_API_KEY was unset. The fix walks the tenant's fallback chain and picks
the first provider with credentials available.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.shared.providers import llm_factory
from app.shared.providers.llm_factory import (
    TenantProviderRegistry,
    _resolve_provider_api_key,
    create_tracked_llm,
)


_ENV_KEYS = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "AI_INTEGRATIONS_GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
    "AI_INTEGRATIONS_ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "AI_INTEGRATIONS_OPENAI_API_KEY",
    "LLM_DEFAULT_PROVIDER",
)


@pytest.fixture
def clean_env(monkeypatch):
    for k in _ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    TenantProviderRegistry.reset()
    yield monkeypatch
    TenantProviderRegistry.reset()


def test_falls_back_when_primary_provider_missing_key(clean_env):
    """Primary=gemini with no key → falls back to claude when ANTHROPIC_API_KEY is set."""
    clean_env.setenv("LLM_DEFAULT_PROVIDER", "gemini")
    clean_env.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    sentinel = object()
    with patch("langchain_anthropic.ChatAnthropic", return_value=sentinel) as mocked:
        llm = create_tracked_llm(temperature=0.2, service_name="test", operation="op")

    assert llm is sentinel
    mocked.assert_called_once()
    call_kwargs = mocked.call_args.kwargs
    assert call_kwargs["api_key"] == "sk-ant-test"


def test_uses_primary_when_credentials_available(clean_env):
    """Primary=openai with key set → uses openai directly, no fallback."""
    clean_env.setenv("LLM_DEFAULT_PROVIDER", "openai")
    clean_env.setenv("OPENAI_API_KEY", "sk-openai-test")

    sentinel = object()
    with patch("langchain_openai.ChatOpenAI", return_value=sentinel) as mocked:
        llm = create_tracked_llm()

    assert llm is sentinel
    mocked.assert_called_once()
    assert mocked.call_args.kwargs["api_key"] == "sk-openai-test"


def test_raises_runtime_error_when_no_provider_has_credentials(clean_env):
    """No provider has credentials → raises clear RuntimeError instead of ADC crash."""
    clean_env.setenv("LLM_DEFAULT_PROVIDER", "gemini")

    with pytest.raises(RuntimeError, match="no LLM provider has credentials"):
        create_tracked_llm()


def test_resolve_provider_api_key_supports_ai_integrations_prefix(clean_env):
    clean_env.setenv("AI_INTEGRATIONS_GEMINI_API_KEY", "g-key")
    clean_env.setenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "a-key")
    clean_env.setenv("AI_INTEGRATIONS_OPENAI_API_KEY", "o-key")

    assert _resolve_provider_api_key("gemini") == "g-key"
    assert _resolve_provider_api_key("claude") == "a-key"
    assert _resolve_provider_api_key("openai") == "o-key"
    assert _resolve_provider_api_key("unknown") == ""


def test_respects_tenant_provider_container_primary(clean_env):
    """Tenant ProviderContainer config drives provider selection over env default."""
    clean_env.setenv("LLM_DEFAULT_PROVIDER", "gemini")
    clean_env.setenv("ANTHROPIC_API_KEY", "sk-ant-tenant")

    registry = TenantProviderRegistry.get_instance()
    registry.get_container(
        tenant_id="acme",
        primary_provider="claude",
        fallback_order=["claude", "openai", "gemini"],
    )

    sentinel = object()
    with patch("langchain_anthropic.ChatAnthropic", return_value=sentinel) as mocked:
        llm = create_tracked_llm(tenant_id="acme")

    assert llm is sentinel
    mocked.assert_called_once()
