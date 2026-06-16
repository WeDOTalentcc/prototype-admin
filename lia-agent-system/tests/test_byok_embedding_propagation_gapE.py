"""TDD Gap E: call sites de embedding propagam company_id (BYOK).

Gap E (auditoria enterprise-readiness 2026-06-08, verificado adversarial
PARTIALLY_CONFIRMED). EmbeddingProviderFactory.embed_with_fallback aceita
company_id e roteia para a chave BYOK do tenant — mas 3 call sites upstream
nunca passavam company_id, fazendo embeddings de tenants BYOK consumirem a
chave global WeDOTalent (vazamento de custo + quebra do contrato BYOK):

  Gap 1 (hot path): VectorSemanticCache — roteamento semântico de TODA mensagem.
  Gap 2 (hot path): rag_pipeline_service.generate_embedding — busca RAG.
  Gap 3 (1 linha): memory_service.store_message — ingestão de memória.
  Gap 4 (dead code): generate_with_fallback alias — zero callers, NAO tocado.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_vector_cache_propagates_company_id_to_embedding():
    """Gap 1: VectorSemanticCache._generate_embedding propaga company_id."""
    from app.orchestrator.memory.vector_semantic_cache import VectorSemanticCache

    captured = {}

    async def fake_embed(text, preferred_provider=None, company_id=None):
        captured["company_id"] = company_id
        return ([0.1] * 1536, "openai", "text-embedding-3-small")

    cache = VectorSemanticCache()
    with patch(
        "app.shared.providers.embedding_factory.EmbeddingProviderFactory.embed_with_fallback",
        new=fake_embed,
    ):
        await cache._generate_embedding("hello", company_id="comp-123")

    assert captured.get("company_id") == "comp-123", (
        "VectorSemanticCache nao propagou company_id para embed_with_fallback (Gap E.1 BYOK)"
    )


@pytest.mark.asyncio
async def test_rag_generate_embedding_propagates_company_id():
    """Gap 2: rag_pipeline_service.generate_embedding aceita e propaga company_id."""
    from app.domains.ai.services import rag_pipeline_service

    captured = {}

    async def fake_embed(text, preferred_provider=None, company_id=None):
        captured["company_id"] = company_id
        return ([0.1] * 1536, "openai", "text-embedding-3-small")

    from unittest.mock import AsyncMock

    # Forca cache-miss para o fluxo chegar ao embed_with_fallback (o cache
    # Redis intercepta antes; aqui isolamos a propagacao de company_id).
    with patch(
        "app.shared.providers.embedding_factory.EmbeddingProviderFactory.embed_with_fallback",
        new=fake_embed,
    ), patch(
        "app.shared.services.embedding_cache_service.embedding_cache.get_embedding",
        new=AsyncMock(return_value=None),
    ), patch(
        "app.shared.services.embedding_cache_service.embedding_cache.cache_embedding",
        new=AsyncMock(return_value=None),
    ):
        await rag_pipeline_service.generate_embedding("hello", company_id="comp-xyz")

    assert captured.get("company_id") == "comp-xyz", (
        "rag_pipeline_service.generate_embedding nao propagou company_id (Gap E.2 BYOK)"
    )
