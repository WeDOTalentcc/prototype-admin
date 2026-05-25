"""
Testes unitários para HybridSearchService (Sprint C — Item C1).

Cobertura:
  - search_jobs retorna lista vazia se sem resultados
  - score híbrido é alpha*vector + (1-alpha)*text
  - alpha=0 usa apenas text_score
  - alpha=1 usa apenas vector_score
  - benchmark retorna dict com chaves text_only, vector_only, hybrid
  - resultados têm campos id, hybrid_score, source
  - isolamento multi-tenant (company_id sempre filtrado)
  - sem embedding → usa apenas tsvector
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.ai.services.hybrid_search_service import (
    HybridSearchService,
    _normalize_scores,
    _merge_results,
    hybrid_search_service,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(text_rows=None, vector_rows=None):
    """Cria mock de AsyncSession que retorna rows configurados."""
    db = MagicMock()
    # Controla retorno sequencial para múltiplas chamadas a execute()
    call_count = [0]
    text_rows = text_rows or []
    vector_rows = vector_rows or []

    async def _execute(sql, params=None):
        call_count[0] += 1
        result = MagicMock()
        if call_count[0] == 1:
            result.fetchall.return_value = text_rows
        else:
            result.fetchall.return_value = vector_rows
        return result

    db.execute = _execute
    return db


# ---------------------------------------------------------------------------
# _normalize_scores
# ---------------------------------------------------------------------------

class TestNormalizeScores:

    def test_empty_list(self):
        assert _normalize_scores([], "text_score") == []

    def test_single_item(self):
        results = [{"id": "1", "text_score": 0.5}]
        normalized = _normalize_scores(results, "text_score")
        # Quando apenas um item, range=0 → score = 1.0
        assert normalized[0]["text_score"] == 1.0

    def test_normalizes_to_0_1(self):
        results = [
            {"id": "1", "text_score": 0.1},
            {"id": "2", "text_score": 0.5},
            {"id": "3", "text_score": 1.0},
        ]
        normalized = _normalize_scores(results, "text_score")
        scores = [r["text_score"] for r in normalized]
        assert min(scores) == pytest.approx(0.0)
        assert max(scores) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# _merge_results
# ---------------------------------------------------------------------------

class TestMergeResults:

    def test_alpha_half_hybrid_score(self):
        """alpha=0.5 → hybrid = 0.5*vector + 0.5*text."""
        text_results = [{"id": "1", "title": "Dev", "text_score": 1.0}]
        vector_results = [{"id": "1", "title": "Dev", "vector_score": 1.0}]
        merged = _merge_results(text_results, vector_results, alpha=0.5)
        assert merged[0]["hybrid_score"] == pytest.approx(1.0)

    def test_alpha_zero_uses_only_text(self):
        """alpha=0 → hybrid_score = text_score apenas."""
        text_results = [{"id": "1", "title": "Dev", "text_score": 1.0}]
        vector_results = [{"id": "1", "title": "Dev", "vector_score": 0.5}]
        merged = _merge_results(text_results, vector_results, alpha=0.0)
        # alpha=0: hybrid = 0*vector_score + 1*text_score
        item = next(r for r in merged if r["id"] == "1")
        assert item["hybrid_score"] == pytest.approx(item["text_score"])

    def test_alpha_one_uses_only_vector(self):
        """alpha=1 → hybrid_score = vector_score apenas."""
        text_results = [{"id": "1", "title": "Dev", "text_score": 0.5}]
        vector_results = [{"id": "1", "title": "Dev", "vector_score": 1.0}]
        merged = _merge_results(text_results, vector_results, alpha=1.0)
        item = next(r for r in merged if r["id"] == "1")
        assert item["hybrid_score"] == pytest.approx(item["vector_score"])

    def test_source_hybrid_when_in_both(self):
        """item presente em text e vector → source=hybrid."""
        text_results = [{"id": "1", "title": "A", "text_score": 0.8}]
        vector_results = [{"id": "1", "title": "A", "vector_score": 0.6}]
        merged = _merge_results(text_results, vector_results, alpha=0.5)
        assert merged[0]["source"] == "hybrid"

    def test_source_text_when_only_in_text(self):
        """item apenas em text → source=text."""
        text_results = [{"id": "1", "title": "A", "text_score": 0.9}]
        vector_results = []
        merged = _merge_results(text_results, vector_results, alpha=0.5)
        assert merged[0]["source"] == "text"

    def test_source_vector_when_only_in_vector(self):
        """item apenas em vector → source=vector."""
        text_results = []
        vector_results = [{"id": "1", "title": "A", "vector_score": 0.7}]
        merged = _merge_results(text_results, vector_results, alpha=0.5)
        assert merged[0]["source"] == "vector"

    def test_result_has_required_fields(self):
        """Cada resultado deve ter id, hybrid_score, source."""
        text_results = [{"id": "x", "title": "Test", "text_score": 0.5}]
        merged = _merge_results(text_results, [], alpha=0.5)
        item = merged[0]
        assert "id" in item
        assert "hybrid_score" in item
        assert "source" in item


# ---------------------------------------------------------------------------
# HybridSearchService.search_jobs
# ---------------------------------------------------------------------------

class TestSearchJobs:

    @pytest.mark.asyncio
    async def test_returns_empty_if_no_results(self):
        svc = HybridSearchService(alpha=0.5)
        db = _make_db(text_rows=[], vector_rows=[])
        result = await svc.search_jobs("python dev", "company-1", db, limit=10)
        assert result == []

    @pytest.mark.asyncio
    async def test_without_embedding_uses_only_tsvector(self):
        svc = HybridSearchService(alpha=0.5)
        db = _make_db(text_rows=[("id-1", "Dev Python", 0.9)], vector_rows=[])

        with patch.object(svc, "_text_search_jobs", new_callable=AsyncMock) as mock_text, \
             patch.object(svc, "_vector_search_jobs", new_callable=AsyncMock) as mock_vec:
            mock_text.return_value = [{"id": "id-1", "title": "Dev Python", "text_score": 0.9}]
            result = await svc.search_jobs("python", "company-1", db, limit=10, embedding=None)
            mock_text.assert_called_once()
            mock_vec.assert_not_called()

        assert result[0]["source"] == "text"

    @pytest.mark.asyncio
    async def test_with_embedding_calls_both(self):
        svc = HybridSearchService(alpha=0.5)
        db = MagicMock()
        embedding = [0.1] * 10

        with patch.object(svc, "_text_search_jobs", new_callable=AsyncMock) as mock_text, \
             patch.object(svc, "_vector_search_jobs", new_callable=AsyncMock) as mock_vec:
            mock_text.return_value = []
            mock_vec.return_value = []
            await svc.search_jobs("query", "company-1", db, limit=5, embedding=embedding)
            mock_text.assert_called_once()
            mock_vec.assert_called_once()

    @pytest.mark.asyncio
    async def test_multitenant_company_id_filtered(self):
        """company_id deve sempre ser passado para as queries SQL."""
        svc = HybridSearchService(alpha=0.5)
        db = MagicMock()
        company_id = "tenant-abc"
        captured_params = []

        async def _fake_execute(sql, params=None):
            if params:
                captured_params.append(params)
            result = MagicMock()
            result.fetchall.return_value = []
            return result

        db.execute = _fake_execute
        await svc.search_jobs("dev", company_id, db)

        assert any(p.get("company_id") == company_id for p in captured_params)

    @pytest.mark.asyncio
    async def test_text_search_returns_gracefully_on_db_error(self):
        """Erro no DB → retorna lista vazia sem lançar exceção."""
        svc = HybridSearchService()

        async def _bad_execute(sql, params=None):
            raise Exception("DB offline")

        db = MagicMock()
        db.execute = _bad_execute
        result = await svc._text_search_jobs("query", "company-1", db, 10)
        assert result == []

    @pytest.mark.asyncio
    async def test_vector_search_returns_gracefully_on_db_error(self):
        """Erro no pgvector → retorna lista vazia sem lançar exceção."""
        svc = HybridSearchService()

        async def _bad_execute(sql, params=None):
            raise Exception("pgvector error")

        db = MagicMock()
        db.execute = _bad_execute
        result = await svc._vector_search_jobs("company-1", db, 10, [0.1] * 10)
        assert result == []


# ---------------------------------------------------------------------------
# HybridSearchService.search_candidates
# ---------------------------------------------------------------------------

class TestSearchCandidates:

    @pytest.mark.asyncio
    async def test_returns_empty_if_no_results(self):
        svc = HybridSearchService(alpha=0.5)
        db = _make_db(text_rows=[], vector_rows=[])
        result = await svc.search_candidates("developer", "company-1", db, limit=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_without_embedding_uses_only_tsvector(self):
        svc = HybridSearchService(alpha=0.5)
        db = MagicMock()

        with patch.object(svc, "_text_search_candidates", new_callable=AsyncMock) as mock_text, \
             patch.object(svc, "_vector_search_candidates", new_callable=AsyncMock) as mock_vec:
            mock_text.return_value = [{"id": "c-1", "name": "João", "text_score": 0.8}]
            result = await svc.search_candidates("João", "company-1", db, embedding=None)
            mock_text.assert_called_once()
            mock_vec.assert_not_called()

        assert result[0]["source"] == "text"


# ---------------------------------------------------------------------------
# HybridSearchService.benchmark
# ---------------------------------------------------------------------------

class TestBenchmark:

    @pytest.mark.asyncio
    async def test_benchmark_returns_required_keys(self):
        svc = HybridSearchService(alpha=0.5)
        db = MagicMock()

        with patch.object(svc, "_text_search_jobs", new_callable=AsyncMock) as mock_text, \
             patch.object(svc, "_vector_search_jobs", new_callable=AsyncMock) as mock_vec:
            mock_text.return_value = []
            mock_vec.return_value = []
            result = await svc.benchmark("query", "company-1", db, embedding=[0.1] * 5)

        assert "text_only" in result
        assert "vector_only" in result
        assert "hybrid" in result

    @pytest.mark.asyncio
    async def test_benchmark_has_count_and_latency(self):
        svc = HybridSearchService(alpha=0.5)
        db = MagicMock()

        with patch.object(svc, "_text_search_jobs", new_callable=AsyncMock) as mock_text, \
             patch.object(svc, "_vector_search_jobs", new_callable=AsyncMock) as mock_vec:
            mock_text.return_value = [{"id": "1", "title": "A", "text_score": 0.5}]
            mock_vec.return_value = []
            result = await svc.benchmark("query", "company-1", db, embedding=[0.1] * 5)

        assert "count" in result["text_only"]
        assert "latency_ms" in result["text_only"]
        assert result["text_only"]["count"] == 1

    @pytest.mark.asyncio
    async def test_benchmark_without_embedding_skips_vector(self):
        svc = HybridSearchService(alpha=0.5)
        db = MagicMock()

        with patch.object(svc, "_text_search_jobs", new_callable=AsyncMock) as mock_text, \
             patch.object(svc, "_vector_search_jobs", new_callable=AsyncMock) as mock_vec:
            mock_text.return_value = []
            result = await svc.benchmark("query", "company-1", db, embedding=None)
            mock_vec.assert_not_called()

        assert result["vector_only"]["count"] == 0


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

def test_singleton_exists():
    """hybrid_search_service deve ser instância de HybridSearchService."""
    assert isinstance(hybrid_search_service, HybridSearchService)


def test_singleton_default_alpha():
    assert hybrid_search_service.alpha == 0.5
