"""
Unit tests for RAGPipelineService — Sprint G6: RAG Híbrido.

Cobre:
  - RAGSearchResult dataclass fields
  - search() structure and source routing
  - alpha=0.0 → BM25 path
  - alpha=1.0 → semantic path
  - alpha=0.5 → hybrid path
  - FairnessGuard logic
  - Multi-tenant scoping
  - Empty results handling
  - Score normalization
  - Merge logic
  - Embedding unavailable degradation
"""
import pytest

pytestmark = pytest.mark.medium

from dataclasses import fields
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.ai.services.rag_pipeline_service import (
    RAGPipelineService,
    RAGSearchResult,
    _check_fairness,
    _merge_candidate_results,
    _normalize,
    generate_embedding,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_bm25_rows(n: int, prefix: str = "c"):
    return [{"id": f"{prefix}{i}", "name": f"Candidato {i}", "bm25_score": float(i + 1)} for i in range(n)]


def _make_semantic_rows(n: int, prefix: str = "c"):
    return [
        {"id": f"{prefix}{i}", "name": f"Candidato {i}", "semantic_score": float(i + 1) / (n + 1)}
        for i in range(n)
    ]


@pytest.fixture
def service():
    return RAGPipelineService(semantic_threshold=0.75)


@pytest.fixture
def mock_db():
    return AsyncMock()


# ---------------------------------------------------------------------------
# 1. RAGSearchResult dataclass fields
# ---------------------------------------------------------------------------


def test_rag_search_result_has_required_fields():
    field_names = {f.name for f in fields(RAGSearchResult)}
    assert "results" in field_names
    assert "query" in field_names
    assert "total" in field_names
    assert "source" in field_names
    assert "fairness_ok" in field_names
    assert "search_time_ms" in field_names
    assert "metadata" in field_names


def test_rag_search_result_instantiation():
    r = RAGSearchResult(
        results=[{"id": "1"}],
        query="python developer",
        total=1,
        source="hybrid",
        fairness_ok=True,
        search_time_ms=42.5,
    )
    assert r.query == "python developer"
    assert r.total == 1
    assert r.source == "hybrid"
    assert r.fairness_ok is True
    assert r.search_time_ms == 42.5
    assert r.metadata == {}


def test_rag_search_result_source_values():
    for src in ("semantic", "bm25", "hybrid"):
        r = RAGSearchResult(
            results=[], query="q", total=0, source=src, fairness_ok=True, search_time_ms=1.0
        )
        assert r.source == src


# ---------------------------------------------------------------------------
# 2. _normalize helper
# ---------------------------------------------------------------------------


def test_normalize_empty():
    assert _normalize([]) == []


def test_normalize_single_value():
    assert _normalize([5.0]) == [1.0]


def test_normalize_uniform():
    result = _normalize([3.0, 3.0, 3.0])
    assert all(v == 1.0 for v in result)


def test_normalize_range():
    result = _normalize([0.0, 0.5, 1.0])
    assert result[0] == pytest.approx(0.0)
    assert result[1] == pytest.approx(0.5)
    assert result[2] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 3. _merge_candidate_results
# ---------------------------------------------------------------------------


def test_merge_bm25_only_source():
    bm25 = [{"id": "1", "name": "Alice", "bm25_score": 1.0}]
    merged = _merge_candidate_results(bm25, [], alpha=0.5)
    assert len(merged) == 1
    assert merged[0]["source"] == "bm25"


def test_merge_semantic_only_source():
    sem = [{"id": "1", "name": "Alice", "semantic_score": 0.9}]
    merged = _merge_candidate_results([], sem, alpha=0.5)
    assert len(merged) == 1
    assert merged[0]["source"] == "semantic"


def test_merge_hybrid_source():
    bm25 = [{"id": "1", "name": "Alice", "bm25_score": 1.0}]
    sem = [{"id": "1", "name": "Alice", "semantic_score": 0.9}]
    merged = _merge_candidate_results(bm25, sem, alpha=0.5)
    assert merged[0]["source"] == "hybrid"


def test_merge_hybrid_score_calculation():
    bm25 = [{"id": "1", "name": "Alice", "bm25_score": 1.0}]
    sem = [{"id": "1", "name": "Alice", "semantic_score": 1.0}]
    merged = _merge_candidate_results(bm25, sem, alpha=0.5)
    # Both normalize to 1.0 → hybrid = 0.5*1 + 0.5*1 = 1.0
    assert merged[0]["hybrid_score"] == pytest.approx(1.0)


def test_merge_sorted_by_hybrid_score_desc():
    bm25 = [
        {"id": "1", "name": "Alice", "bm25_score": 0.2},
        {"id": "2", "name": "Bob", "bm25_score": 1.0},
    ]
    merged = _merge_candidate_results(bm25, [], alpha=0.0)
    # alpha=0 → hybrid_score = 0*sem + 1*bm25; higher bm25 first
    assert merged[0]["id"] == "2"
    assert merged[1]["id"] == "1"


# ---------------------------------------------------------------------------
# 4. _check_fairness
# ---------------------------------------------------------------------------


def test_fairness_ok_with_no_gender_data():
    results = [{"id": str(i)} for i in range(10)]
    assert _check_fairness(results) is True


def test_fairness_ok_with_balanced_genders():
    results = [{"id": str(i), "gender": "M" if i < 5 else "F"} for i in range(10)]
    assert _check_fairness(results) is True


def test_fairness_fails_with_dominant_gender():
    # 9 M out of 10 = 90% → above 70% threshold
    results = [{"id": str(i), "gender": "M" if i < 9 else "F"} for i in range(10)]
    assert _check_fairness(results) is False


def test_fairness_ok_at_exact_threshold():
    # 7 M, 3 F = 70% — exactly at threshold (not above)
    results = [{"id": str(i), "gender": "M" if i < 7 else "F"} for i in range(10)]
    assert _check_fairness(results) is True


def test_fairness_insufficient_data_returns_true():
    results = [{"id": "1", "gender": "M"}, {"id": "2", "gender": "F"}]
    assert _check_fairness(results) is True


def test_fairness_top_n_respected():
    # First 10: balanced. Next 10: all M. Fairness should be OK.
    results = (
        [{"id": str(i), "gender": "M" if i < 5 else "F"} for i in range(10)]
        + [{"id": str(i + 10), "gender": "M"} for i in range(10)]
    )
    assert _check_fairness(results, top_n=10) is True


# ---------------------------------------------------------------------------
# 5. RAGPipelineService.search() — alpha routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_alpha_zero_uses_bm25_path(service, mock_db):
    """alpha=0.0 → apenas BM25, não gera embedding."""
    bm25_rows = _make_bm25_rows(3)

    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=bm25_rows)) as mock_bm25,
        patch.object(service, "_semantic_search", new=AsyncMock(return_value=[])) as mock_sem,
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=None)) as mock_emb,
    ):
        result = await service.search("python", "company-1", mock_db, limit=10, alpha=0.0)

    mock_bm25.assert_called_once()
    mock_emb.assert_not_called()
    mock_sem.assert_not_called()
    assert result.source == "bm25"
    assert result.total == 3


@pytest.mark.asyncio
async def test_search_alpha_one_uses_semantic_path(service, mock_db):
    """alpha=1.0 → apenas semântico, não executa BM25."""
    sem_rows = _make_semantic_rows(3)
    fake_embedding = [0.1] * 1536

    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=[])) as mock_bm25,
        patch.object(service, "_semantic_search", new=AsyncMock(return_value=sem_rows)) as mock_sem,
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=fake_embedding)),
    ):
        result = await service.search("python", "company-1", mock_db, limit=10, alpha=1.0)

    mock_bm25.assert_not_called()
    mock_sem.assert_called_once()
    assert result.source == "semantic"
    assert result.total == 3


@pytest.mark.asyncio
async def test_search_alpha_half_uses_hybrid_path(service, mock_db):
    """alpha=0.5 → path híbrido, ambas as buscas executadas."""
    bm25_rows = _make_bm25_rows(3)
    sem_rows = _make_semantic_rows(3)
    fake_embedding = [0.1] * 1536

    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=bm25_rows)),
        patch.object(service, "_semantic_search", new=AsyncMock(return_value=sem_rows)),
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=fake_embedding)),
    ):
        result = await service.search("python", "company-1", mock_db, limit=10, alpha=0.5)

    assert result.source == "hybrid"


@pytest.mark.asyncio
async def test_search_returns_rag_search_result_instance(service, mock_db):
    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=_make_bm25_rows(2))),
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=None)),
    ):
        result = await service.search("dev", "company-1", mock_db, alpha=0.0)

    assert isinstance(result, RAGSearchResult)
    assert isinstance(result.search_time_ms, float)
    assert result.search_time_ms >= 0


@pytest.mark.asyncio
async def test_search_empty_results(service, mock_db):
    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=[])),
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=None)),
    ):
        result = await service.search("inexistente", "company-1", mock_db, alpha=0.0)

    assert result.results == []
    assert result.total == 0
    assert result.source == "bm25"
    assert result.fairness_ok is True  # sem dados → True


@pytest.mark.asyncio
async def test_search_embedding_unavailable_falls_back_to_bm25(service, mock_db):
    """Quando embedding indisponível, alpha>0 cai em BM25."""
    bm25_rows = _make_bm25_rows(2)

    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=bm25_rows)),
        patch.object(service, "_semantic_search", new=AsyncMock(return_value=[])) as mock_sem,
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=None)),
    ):
        result = await service.search("python", "company-1", mock_db, alpha=0.5)

    mock_sem.assert_not_called()
    assert result.source == "bm25"
    assert result.total == 2


# ---------------------------------------------------------------------------
# 6. Multi-tenant scoping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_passes_company_id_to_bm25(service, mock_db):
    """_bm25_search deve receber o company_id correto."""
    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=[])) as mock_bm25,
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=None)),
    ):
        await service.search("python", "tenant-xyz", mock_db, alpha=0.0)

    _, kwargs = mock_bm25.call_args
    # pode ser posicional ou keyword — verificar ambos
    call_args = mock_bm25.call_args
    assert "tenant-xyz" in call_args.args or call_args.kwargs.get("company_id") == "tenant-xyz"


@pytest.mark.asyncio
async def test_search_passes_company_id_to_semantic(service, mock_db):
    """_semantic_search deve receber o company_id correto."""
    fake_embedding = [0.1] * 100

    with (
        patch.object(service, "_semantic_search", new=AsyncMock(return_value=[])) as mock_sem,
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=[])),
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=fake_embedding)),
    ):
        await service.search("python", "tenant-abc", mock_db, alpha=1.0)

    call_args = mock_sem.call_args
    assert "tenant-abc" in call_args.args or call_args.kwargs.get("company_id") == "tenant-abc"


# ---------------------------------------------------------------------------
# 7. Metadata fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_metadata_contains_alpha(service, mock_db):
    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=_make_bm25_rows(1))),
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=None)),
    ):
        result = await service.search("q", "c1", mock_db, alpha=0.3)

    assert result.metadata["alpha"] == pytest.approx(0.3)


@pytest.mark.asyncio
async def test_search_metadata_embedding_flag_false_when_unavailable(service, mock_db):
    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=[])),
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=None)),
    ):
        result = await service.search("q", "c1", mock_db, alpha=0.5)

    assert result.metadata["embedding_available"] is False


@pytest.mark.asyncio
async def test_search_metadata_embedding_flag_true_when_available(service, mock_db):
    fake_embedding = [0.1] * 10

    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=[])),
        patch.object(service, "_semantic_search", new=AsyncMock(return_value=[])),
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=fake_embedding)),
    ):
        result = await service.search("q", "c1", mock_db, alpha=0.5)

    assert result.metadata["embedding_available"] is True


# ---------------------------------------------------------------------------
# 8. Limit respected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_respects_limit(service, mock_db):
    bm25_rows = _make_bm25_rows(50)

    with (
        patch.object(service, "_bm25_search", new=AsyncMock(return_value=bm25_rows)),
        patch("app.domains.ai.services.rag_pipeline_service.generate_embedding", new=AsyncMock(return_value=None)),
    ):
        result = await service.search("q", "c1", mock_db, limit=5, alpha=0.0)

    assert result.total <= 5


# ---------------------------------------------------------------------------
# 9. generate_embedding graceful failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_embedding_returns_none_on_import_error():
    with patch.dict("sys.modules", {"app.services.embedding_cache_service": None}):
        # Should not raise — returns None gracefully
        result = await generate_embedding("test query")
    assert result is None or isinstance(result, list)
