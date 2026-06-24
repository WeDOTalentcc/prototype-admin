"""Embedding P2 sensor (2026-06-06).

O proxy Gemini do Replit rejeita batchEmbedContents (INVALID_ENDPOINT), entao o
OpenAI text-embedding-3-small e o provider funcional de fato. A chave canonica
OPENAI_API_KEY ja esta provisionada no ambiente, mas o provider so olhava
AI_INTEGRATIONS_OPENAI_API_KEY. Este sensor pina o fallback p/ OPENAI_API_KEY
(sem ele, a busca semantica fica degradada — todos os providers falham).
"""
from __future__ import annotations

import pytest


def test_openai_provider_uses_openai_api_key_fallback(monkeypatch):
    monkeypatch.delenv("AI_INTEGRATIONS_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AI_INTEGRATIONS_OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fallback-key")
    from app.shared.providers.embedding_openai import OpenAIEmbeddingProvider

    provider = OpenAIEmbeddingProvider()
    # Nao deve levantar: resolve a chave via OPENAI_API_KEY (fallback).
    assert provider._openai_client is not None


def test_openai_provider_raises_when_no_key_anywhere(monkeypatch):
    monkeypatch.delenv("AI_INTEGRATIONS_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.shared.providers.embedding_openai import OpenAIEmbeddingProvider

    provider = OpenAIEmbeddingProvider()
    with pytest.raises(ValueError):
        _ = provider._openai_client
