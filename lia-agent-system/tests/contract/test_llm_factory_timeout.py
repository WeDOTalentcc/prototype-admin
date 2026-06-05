"""Sensor — create_tracked_llm DEVE injetar timeout nos clientes LLM (audit 2026-06-05 P1).

Sem timeout, JD enrichment fica exposto ao default ~10min do SDK (raiz do 502/hang
do wizard). Espelha o pattern ja usado em app/domains/ai/services/llm.py:191.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.shared.providers import llm_factory
from app.core.config import settings


def test_create_tracked_llm_injeta_timeout_no_cliente_claude():
    fake_client = MagicMock()
    with patch.object(llm_factory, "_resolve_provider_chain", return_value=("claude", ["claude"], {})), \
         patch.object(llm_factory, "_resolve_provider_api_key", return_value="sk-test"), \
         patch.object(llm_factory, "_resolve_provider_base_url", return_value=None), \
         patch("langchain_anthropic.ChatAnthropic", return_value=fake_client) as MockCA:
        llm_factory.create_tracked_llm(service_name="test", operation="t")
        assert MockCA.called, "ChatAnthropic deveria ter sido instanciado"
        _, kwargs = MockCA.call_args
        expected = getattr(settings, "LLM_TIMEOUT_SECONDS", 120)
        assert kwargs.get("timeout") == expected, f"timeout ausente/errado: {kwargs.get('timeout')!r}"
