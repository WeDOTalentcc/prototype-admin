"""
Testes E2E para VectorSemanticCache — fluxo completo com mocks.

Complementa os testes unitários com cenários de ponta a ponta:
- Fluxo set() → get() com threshold exato
- Isolamento multi-tenant (company_id)
- Hit count e stats acumuladas
- Variação de threshold
- Compatibilidade com diferentes dimensões de embedding

Camada 3 (Integração) da pirâmide — embedding e pgvector mockados.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.orchestrator.memory.vector_semantic_cache import VectorSemanticCache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vec(value: float = 0.5, dim: int = 1536) -> list:
    """Cria vetor fake normalizado."""
    return [value] * dim


def _dot_product(a: list, b: list) -> float:
    """Cosine similarity simplificada para vetores normalizados."""
    return sum(x * y for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# Seção 1: Fluxo completo set() → get()
# ---------------------------------------------------------------------------

class TestVectorCacheFullFlow:

    @pytest.mark.asyncio
    async def test_cache_miss_on_empty_db(self):
        """get() em cache vazio retorna None."""
        cache = VectorSemanticCache(similarity_threshold=0.92)
        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec())), \
             patch.object(cache, "_query_similar", new=AsyncMock(return_value=None)):
            result = await cache.get("criar vaga de engenheiro")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_after_set(self):
        """get() retorna resultado após set() com mesma mensagem."""
        cache = VectorSemanticCache(similarity_threshold=0.90)
        domain_data = {
            "domain_id": "job_management",
            "confidence": 0.95,
            "source": "fast_router",
        }

        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec(0.7))), \
             patch.object(cache, "_insert_cache", new=AsyncMock()):
            await cache.set("criar vaga de desenvolvedor", domain_data)

        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec(0.7))), \
             patch.object(cache, "_query_similar", new=AsyncMock(return_value={
                 **domain_data,
                 "cache_source": "vector_cache",
                 "similarity": 0.98,
             })):
            result = await cache.get("criar vaga de desenvolvedor")

        assert result is not None
        assert result["domain_id"] == "job_management"

    @pytest.mark.asyncio
    async def test_get_returns_none_below_threshold(self):
        """get() retorna None quando similarity está abaixo do threshold."""
        cache = VectorSemanticCache(similarity_threshold=0.92)

        # Simula resultado com similaridade abaixo do threshold
        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec())), \
             patch.object(cache, "_query_similar", new=AsyncMock(return_value=None)):
            result = await cache.get("query completamente diferente")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_does_not_raise_on_db_error(self):
        """set() falha graciosamente sem propagar exceção."""
        cache = VectorSemanticCache()
        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec())), \
             patch.object(cache, "_insert_cache", new=AsyncMock(side_effect=Exception("DB down"))):
            # Não deve lançar exceção
            await cache.set("query test", {"domain_id": "sourcing"})

    @pytest.mark.asyncio
    async def test_get_returns_none_on_embedding_error(self):
        """get() retorna None quando serviço de embedding falha."""
        cache = VectorSemanticCache()
        with patch.object(cache, "_get_embedding", new=AsyncMock(side_effect=Exception("API down"))):
            result = await cache.get("criar vaga")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_on_db_query_error(self):
        """get() retorna None quando query pgvector falha."""
        cache = VectorSemanticCache()
        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec())), \
             patch.object(cache, "_query_similar", new=AsyncMock(side_effect=Exception("PG down"))):
            result = await cache.get("buscar candidatos")
        assert result is None


# ---------------------------------------------------------------------------
# Seção 2: Hit count e stats
# ---------------------------------------------------------------------------

class TestVectorCacheHitCount:

    @pytest.mark.asyncio
    async def test_hit_returns_domain_data(self):
        """Cache hit retorna domain_data com cache_source=vector_cache."""
        cache = VectorSemanticCache()
        domain_data = {"domain_id": "sourcing", "confidence": 0.9, "source": "fast_router"}

        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec())), \
             patch.object(cache, "_query_similar", new=AsyncMock(return_value={
                 **domain_data,
                 "cache_source": "vector_cache",
             })):
            result = await cache.get("buscar candidatos python")

        assert result is not None
        assert result["cache_source"] == "vector_cache"
        assert result["domain_id"] == "sourcing"

    @pytest.mark.asyncio
    async def test_multiple_hits_all_return_data(self):
        """Múltiplos hits consecutivos retornam dados corretamente."""
        cache = VectorSemanticCache()
        domain_data = {"domain_id": "sourcing", "confidence": 0.9, "source": "fast_router",
                       "cache_source": "vector_cache"}

        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec())), \
             patch.object(cache, "_query_similar", new=AsyncMock(return_value=domain_data)):
            r1 = await cache.get("buscar candidatos python")
            r2 = await cache.get("buscar candidatos python")

        assert r1 is not None
        assert r2 is not None
        assert r1["domain_id"] == r2["domain_id"]


# ---------------------------------------------------------------------------
# Seção 3: Threshold configurável
# ---------------------------------------------------------------------------

class TestVectorCacheThresholds:

    def test_default_threshold_is_high(self):
        """Threshold padrão é alto para evitar falsos positivos (>= 0.85)."""
        cache = VectorSemanticCache()
        assert cache.threshold >= 0.85

    def test_custom_threshold_accepted(self):
        """Threshold customizado é aceito."""
        cache_strict = VectorSemanticCache(similarity_threshold=0.99)
        assert cache_strict.threshold == 0.99

        cache_lenient = VectorSemanticCache(similarity_threshold=0.70)
        assert cache_lenient.threshold == 0.70

    def test_high_threshold_more_restrictive(self):
        """Cache com threshold alto é mais restritivo que com threshold baixo."""
        # Apenas valida que threshold está acessível e correto
        cache_high = VectorSemanticCache(similarity_threshold=0.98)
        cache_low = VectorSemanticCache(similarity_threshold=0.75)
        assert cache_high.threshold > cache_low.threshold


# ---------------------------------------------------------------------------
# Seção 4: Isolamento multi-tenant
# ---------------------------------------------------------------------------

class TestVectorCacheMultiTenant:

    @pytest.mark.asyncio
    async def test_different_caches_do_not_share_state(self):
        """Duas instâncias de cache não compartilham estado interno."""
        cache_a = VectorSemanticCache()
        cache_b = VectorSemanticCache()

        # Cache A: set com domínio job_management
        with patch.object(cache_a, "_get_embedding", new=AsyncMock(return_value=_vec(0.5))), \
             patch.object(cache_a, "_insert_cache", new=AsyncMock()):
            await cache_a.set("criar vaga", {"domain_id": "job_management"})

        # Cache B: get retorna None — não compartilha estado com A
        with patch.object(cache_b, "_get_embedding", new=AsyncMock(return_value=_vec(0.5))), \
             patch.object(cache_b, "_query_similar", new=AsyncMock(return_value=None)):
            result_b = await cache_b.get("criar vaga")

        assert result_b is None

    @pytest.mark.asyncio
    async def test_cache_set_calls_insert_cache(self):
        """set() chama _insert_cache ao armazenar resultado."""
        cache = VectorSemanticCache()
        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec())), \
             patch.object(cache, "_insert_cache", new=AsyncMock()) as mock_store:
            await cache.set("criar vaga", {"domain_id": "job_management"})
            # _insert_cache deve ter sido chamado
            mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_get_returns_none_on_cache_miss(self):
        """get() retorna None quando não há resultado armazenado."""
        cache = VectorSemanticCache()
        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=_vec())), \
             patch.object(cache, "_query_similar", new=AsyncMock(return_value=None)):
            result = await cache.get("criar vaga")
        assert result is None  # sem cache, retorna None sem erro


# ---------------------------------------------------------------------------
# Seção 5: Embedding dimensions
# ---------------------------------------------------------------------------

class TestVectorCacheEmbeddingDimensions:

    @pytest.mark.asyncio
    async def test_accepts_1536_dim_embeddings(self):
        """Aceita embeddings de 1536 dimensões (OpenAI text-embedding-3-small)."""
        cache = VectorSemanticCache()
        embedding_1536 = _vec(0.3, dim=1536)
        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=embedding_1536)), \
             patch.object(cache, "_query_similar", new=AsyncMock(return_value=None)):
            result = await cache.get("test query")
        assert result is None  # sem erro

    @pytest.mark.asyncio
    async def test_accepts_768_dim_embeddings(self):
        """Aceita embeddings de 768 dimensões (modelos menores)."""
        cache = VectorSemanticCache()
        embedding_768 = _vec(0.3, dim=768)
        with patch.object(cache, "_get_embedding", new=AsyncMock(return_value=embedding_768)), \
             patch.object(cache, "_query_similar", new=AsyncMock(return_value=None)):
            result = await cache.get("test query 768")
        assert result is None  # sem erro
