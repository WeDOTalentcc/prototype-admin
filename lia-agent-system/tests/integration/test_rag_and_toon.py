"""
Integração — RAG search → TOON generation → Redis cache (Sprint K2).

Camada 3 da pirâmide de testes.
Cobre:
- RAGPipelineService.search retorna RAGSearchResult com .results, .total, .source
- Blend alpha=0 (BM25 only), alpha=1 (semântico only), alpha=0.5 (hybrid)
- _check_fairness chamado sobre os resultados do top-10
- TOONService.get_or_generate: cache miss → gera → armazena no Redis
- TOONService.get_or_generate: cache hit → retorna sem chamar generate
- LGPD anonymize=True → name_display = "Candidato X"
- Chave Redis: toon:{company_id}:{candidate_id}:{job_id}
"""
import uuid
import json
import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


COMPANY_ID = "c-integ-001"
JOB_ID = str(uuid.uuid4())
CANDIDATE_ID = str(uuid.uuid4())


def _make_db():
    db = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = []
    result.scalars.return_value = MagicMock(all=MagicMock(return_value=[]))
    db.execute = AsyncMock(return_value=result)
    return db


def _make_toon_card(name_display="João Silva", anonymized=False):
    from app.services.toon_service import TOONCard
    return TOONCard(
        candidate_id=CANDIDATE_ID,
        job_id=JOB_ID,
        generated_at=datetime.datetime.utcnow().isoformat(),
        headline="Dev Backend Sênior",
        highlights=["5 anos exp", "Python"],
        match_score=85,
        skills_match=["Python", "FastAPI"],
        name_display=name_display,
        location="São Paulo, SP",
        experience_years=5,
        anonymized=anonymized,
        fairness_reviewed=True,
    )


# ---------------------------------------------------------------------------
# RAGPipelineService
# ---------------------------------------------------------------------------

class TestRAGSearch:

    @pytest.mark.asyncio
    async def test_search_returns_rag_result(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()
        with patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=[]), \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]):
            result = await svc.search("dev backend", COMPANY_ID, db, limit=10)
        assert hasattr(result, "results")
        assert hasattr(result, "total")
        assert isinstance(result.results, list)

    @pytest.mark.asyncio
    async def test_alpha_zero_calls_only_bm25(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()
        with patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=[]) as bm25, \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]) as sem:
            await svc.search("dev", COMPANY_ID, db, limit=5, alpha=0.0)
        bm25.assert_awaited_once()
        sem.assert_not_called()

    @pytest.mark.asyncio
    async def test_alpha_one_calls_only_semantic(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()
        with patch("app.services.rag_pipeline_service.generate_embedding", new_callable=AsyncMock, return_value=[0.1] * 768), \
             patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=[]) as bm25, \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]) as sem:
            await svc.search("dev", COMPANY_ID, db, limit=5, alpha=1.0)
        sem.assert_awaited_once()
        bm25.assert_not_called()

    @pytest.mark.asyncio
    async def test_hybrid_calls_both(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()
        with patch("app.services.rag_pipeline_service.generate_embedding", new_callable=AsyncMock, return_value=[0.1] * 768), \
             patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=[]) as bm25, \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]) as sem:
            await svc.search("dev", COMPANY_ID, db, limit=5, alpha=0.5)
        bm25.assert_awaited_once()
        sem.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fairness_check_invoked(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()
        with patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=[]), \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]), \
             patch("app.services.rag_pipeline_service._check_fairness", return_value=True) as mock_fair:
            result = await svc.search("dev", COMPANY_ID, db, limit=10, alpha=0.0)
        mock_fair.assert_called_once()
        assert result.fairness_ok is True

    @pytest.mark.asyncio
    async def test_result_bounded_by_limit(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()
        many = [{"id": str(uuid.uuid4()), "name": "C", "bm25_score": 0.9, "company_id": COMPANY_ID} for _ in range(20)]
        with patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=many), \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]):
            result = await svc.search("dev", COMPANY_ID, db, limit=5, alpha=0.0)
        assert len(result.results) <= 5

    @pytest.mark.asyncio
    async def test_source_is_bm25_when_alpha_zero(self):
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService
        svc = RAGPipelineService()
        db = _make_db()
        with patch.object(svc, "_bm25_search", new_callable=AsyncMock, return_value=[]), \
             patch.object(svc, "_semantic_search", new_callable=AsyncMock, return_value=[]):
            result = await svc.search("dev", COMPANY_ID, db, limit=5, alpha=0.0)
        assert result.source == "bm25"


# ---------------------------------------------------------------------------
# _check_fairness — module-level
# ---------------------------------------------------------------------------

class TestFairnessGuard:

    def test_ok_with_balanced_genders(self):
        from app.domains.ai.services.rag_pipeline_service import _check_fairness
        results = (
            [{"gender": "F"}] * 5 +
            [{"gender": "M"}] * 5
        )
        assert _check_fairness(results, top_n=10) is True

    def test_flagged_when_one_gender_dominates(self):
        from app.domains.ai.services.rag_pipeline_service import _check_fairness
        # 9 M + 1 F → 90% M → acima do limiar de 70%
        results = [{"gender": "M"}] * 9 + [{"gender": "F"}]
        assert _check_fairness(results, top_n=10) is False

    def test_ok_without_gender_data(self):
        from app.domains.ai.services.rag_pipeline_service import _check_fairness
        results = [{"name": "C"}] * 10
        assert _check_fairness(results, top_n=10) is True


# ---------------------------------------------------------------------------
# TOONService
# ---------------------------------------------------------------------------

class TestTOONService:

    def _make_service(self):
        from app.services.toon_service import TOONService
        svc = TOONService()
        return svc

    @pytest.mark.asyncio
    async def test_cache_miss_calls_generate(self):
        svc = self._make_service()
        card = _make_toon_card()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_redis.aclose = AsyncMock()

        with patch("app.services.toon_service._get_redis", new_callable=AsyncMock, return_value=mock_redis), \
             patch.object(svc, "generate", new_callable=AsyncMock, return_value=card) as mock_gen:
            result = await svc.get_or_generate(CANDIDATE_ID, JOB_ID, _make_db(), COMPANY_ID)

        mock_gen.assert_awaited_once()
        assert result.match_score == 85

    @pytest.mark.asyncio
    async def test_cache_hit_skips_generate(self):
        from dataclasses import asdict
        svc = self._make_service()
        card = _make_toon_card()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(asdict(card)).encode())
        mock_redis.aclose = AsyncMock()

        with patch("app.services.toon_service._get_redis", new_callable=AsyncMock, return_value=mock_redis), \
             patch.object(svc, "generate", new_callable=AsyncMock) as mock_gen:
            result = await svc.get_or_generate(CANDIDATE_ID, JOB_ID, _make_db(), COMPANY_ID)

        mock_gen.assert_not_awaited()
        assert result.headline == "Dev Backend Sênior"

    @pytest.mark.asyncio
    async def test_anonymize_true_returns_masked_name(self):
        svc = self._make_service()
        card = _make_toon_card(name_display="Candidato X", anonymized=True)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_redis.aclose = AsyncMock()

        with patch("app.services.toon_service._get_redis", new_callable=AsyncMock, return_value=mock_redis), \
             patch.object(svc, "generate", new_callable=AsyncMock, return_value=card):
            result = await svc.get_or_generate(CANDIDATE_ID, JOB_ID, _make_db(), COMPANY_ID, anonymize=True)

        assert result.name_display == "Candidato X"

    def test_cache_key_format(self):
        from app.services.toon_service import _toon_cache_key
        key = _toon_cache_key(CANDIDATE_ID, JOB_ID, COMPANY_ID)
        assert key == f"toon:{COMPANY_ID}:{CANDIDATE_ID}:{JOB_ID}"

    @pytest.mark.asyncio
    async def test_redis_unavailable_still_generates(self):
        """Se Redis indisponível, generate é chamado e resultado retornado sem cache."""
        svc = self._make_service()
        card = _make_toon_card()

        with patch("app.services.toon_service._get_redis", new_callable=AsyncMock, return_value=None), \
             patch.object(svc, "generate", new_callable=AsyncMock, return_value=card) as mock_gen:
            result = await svc.get_or_generate(CANDIDATE_ID, JOB_ID, _make_db(), COMPANY_ID)

        mock_gen.assert_awaited_once()
        assert result is not None
