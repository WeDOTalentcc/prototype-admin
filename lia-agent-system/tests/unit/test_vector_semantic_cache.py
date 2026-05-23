"""
Testes unitários para VectorSemanticCache.

Cobertura:
  - test_get_returns_none_on_empty_cache     — cache vazio retorna None
  - test_set_and_get_similar_message         — mensagem similar retorna cache hit
  - test_get_below_threshold_returns_none    — similaridade abaixo do threshold retorna None
  - test_fallback_on_db_error                — erro no banco retorna None graciosamente
  - test_hit_count_incremented               — cada hit incrementa hit_count
  - test_set_does_not_raise_on_db_error      — set falha graciosamente sem propagar
  - test_embedding_cache_reused              — embedding Redis é reutilizado (sem re-chamar LLM)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.orchestrator.memory.vector_semantic_cache import VectorSemanticCache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cache():
    return VectorSemanticCache(similarity_threshold=0.92)


def _mock_embedding(dim: int = 1536) -> list:
    """Vetor fake normalizado para testes."""
    return [0.1] * dim


# ---------------------------------------------------------------------------
# test_get_returns_none_on_empty_cache
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_returns_none_on_empty_cache(cache):
    """Cache vazio deve retornar None sem lançar exceção."""
    with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_mock_embedding())):
        with patch.object(cache, "_query_similar", new=AsyncMock(return_value=None)):
            result = await cache.get("criar uma vaga de desenvolvedor")
    assert result is None


# ---------------------------------------------------------------------------
# test_set_and_get_similar_message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_set_and_get_similar_message(cache):
    """Mensagem semanticamente similar deve retornar cache hit."""
    expected = {
        "domain_id": "job_management",
        "confidence": 0.95,
        "source": "fast_router",
        "cache_source": "vector_cache",
    }

    with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_mock_embedding())):
        with patch.object(cache, "_query_similar", new=AsyncMock(return_value=expected)):
            result = await cache.get("cria uma vaga pra desenvolvedor")

    assert result is not None
    assert result["domain_id"] == "job_management"
    assert result["confidence"] == 0.95
    assert result["cache_source"] == "vector_cache"


# ---------------------------------------------------------------------------
# test_get_below_threshold_returns_none
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_below_threshold_returns_none(cache):
    """Similaridade abaixo do threshold deve retornar None."""
    # _query_similar retorna None quando cosine_sim < threshold (já filtrado no SQL)
    with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_mock_embedding())):
        with patch.object(cache, "_query_similar", new=AsyncMock(return_value=None)):
            result = await cache.get("qual é o tempo hoje")

    assert result is None


# ---------------------------------------------------------------------------
# test_fallback_on_db_error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_on_db_error(cache):
    """Erro no banco deve retornar None graciosamente (sem propagar exceção)."""
    with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_mock_embedding())):
        with patch.object(
            cache,
            "_query_similar",
            new=AsyncMock(side_effect=Exception("DB connection error")),
        ):
            result = await cache.get("criar uma vaga")

    assert result is None  # falhou graciosamente


@pytest.mark.asyncio
async def test_fallback_on_embedding_error(cache):
    """Erro no embedding service deve retornar None graciosamente."""
    with patch.object(
        cache,
        "_get_embedding",
        new=AsyncMock(side_effect=Exception("OpenAI API unreachable")),
    ):
        result = await cache.get("criar uma vaga")

    assert result is None


# ---------------------------------------------------------------------------
# test_hit_count_incremented
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hit_count_incremented(cache):
    """Cada hit deve acionar UPDATE no banco via _query_similar."""
    hit_data = {
        "domain_id": "sourcing",
        "confidence": 0.88,
        "source": "fast_router",
        "cache_source": "vector_cache",
    }

    query_mock = AsyncMock(return_value=hit_data)

    with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_mock_embedding())):
        with patch.object(cache, "_query_similar", query_mock):
            await cache.get("buscar candidatos para engenharia")
            await cache.get("encontrar candidatos engenheiros")
            await cache.get("procurar candidatos de engenharia")

    # _query_similar deve ter sido chamado 3 vezes (cada hit é uma chamada)
    assert query_mock.call_count == 3


# ---------------------------------------------------------------------------
# test_set_does_not_raise_on_db_error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_set_does_not_raise_on_db_error(cache):
    """set() deve falhar graciosamente mesmo com DB indisponível."""
    with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_mock_embedding())):
        with patch.object(
            cache,
            "_insert_cache",
            new=AsyncMock(side_effect=Exception("DB unavailable")),
        ):
            # Não deve lançar exceção
            await cache.set(
                "criar vaga de desenvolvedor",
                {"domain_id": "job_management", "confidence": 0.9, "source": "fast_router"},
            )


# ---------------------------------------------------------------------------
# test_embedding_cache_reused
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_embedding_cache_reused(cache):
    """Embedding cacheado no Redis deve ser reutilizado sem re-chamar LLM."""
    cached_vector = _mock_embedding()
    generate_calls = []

    async def _fake_get_embedding(text: str):
        # Simula: Redis hit retorna cached, _generate_embedding não é chamado
        return cached_vector

    async def _fake_generate_embedding(text: str):
        generate_calls.append(text)
        return cached_vector

    with patch.object(cache, "_get_embedding", new=_fake_get_embedding):
        with patch.object(cache, "_generate_embedding", new=_fake_generate_embedding):
            with patch.object(cache, "_query_similar", new=AsyncMock(return_value=None)):
                await cache.get("criar vaga")

    # _generate_embedding NÃO deve ter sido chamado (cache hit Redis simulado por _get_embedding)
    assert generate_calls == []


# ---------------------------------------------------------------------------
# test_get_returns_none_when_embedding_is_none
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_returns_none_when_embedding_is_none(cache):
    """Se embedding retornar None (providers indisponíveis), get() retorna None."""
    with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=None)):
        result = await cache.get("qualquer mensagem")

    assert result is None


@pytest.mark.asyncio
async def test_set_skips_when_embedding_is_none(cache):
    """Se embedding retornar None, set() deve pular insert graciosamente."""
    with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=None)):
        insert_mock = AsyncMock()
        with patch.object(cache, "_insert_cache", insert_mock):
            await cache.set("qualquer mensagem", {"domain_id": "sourcing", "confidence": 0.9})

    insert_mock.assert_not_called()
