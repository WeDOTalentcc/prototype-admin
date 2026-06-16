"""TDD — orquestrador honra chave Anthropic por-tenant via LLM Factory (BYOK).

Opção B (Paulo): _build_anthropic_client resolve a config por-tenant via a
factory (chave do tenant > chave global), mantendo o loop nativo.
"""
from __future__ import annotations
from unittest.mock import patch
import pytest

from app.domains.job_creation.orchestrator.wizard_orchestrator import WizardOrchestrator


@pytest.mark.medium
def test_tenant_key_takes_precedence():
    """Chave do tenant (BYOK) vence a global."""
    with patch(
        "app.shared.providers.llm_factory._resolve_provider_chain",
        return_value=("claude", ["claude"], {"claude": "sk-ant-TENANT-key"}),
    ), patch(
        "app.shared.providers.llm_factory._resolve_provider_api_key",
        return_value="sk-ant-GLOBAL-key",
    ), patch(
        "app.shared.providers.llm_factory._resolve_provider_base_url",
        return_value="https://proxy.example",
    ):
        key, base = WizardOrchestrator._resolve_anthropic_config("tenant-123")
    assert key == "sk-ant-TENANT-key"  # BYOK precede
    assert base == "https://proxy.example"


@pytest.mark.medium
def test_falls_back_to_global_when_no_tenant_key():
    with patch(
        "app.shared.providers.llm_factory._resolve_provider_chain",
        return_value=("claude", ["claude"], {}),  # tenant sem chave própria
    ), patch(
        "app.shared.providers.llm_factory._resolve_provider_api_key",
        return_value="sk-ant-GLOBAL-key",
    ), patch(
        "app.shared.providers.llm_factory._resolve_provider_base_url",
        return_value=None,
    ):
        key, base = WizardOrchestrator._resolve_anthropic_config("tenant-123")
    assert key == "sk-ant-GLOBAL-key"


@pytest.mark.medium
def test_factory_failure_falls_back_to_env(monkeypatch):
    """Se a factory explodir, cai no env global (fail-open)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-ENV")
    monkeypatch.delenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", raising=False)
    with patch(
        "app.shared.providers.llm_factory._resolve_provider_chain",
        side_effect=RuntimeError("factory down"),
    ):
        key, base = WizardOrchestrator._resolve_anthropic_config("t")
    assert key == "sk-ant-ENV"
    assert base is None
