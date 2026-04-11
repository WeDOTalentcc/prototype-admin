"""
Tests for Sprint Y5 — E6: RAG por Domínio — Embeddings Separados.

10 test cases covering:
  - DOMAIN_ALIASES coverage
  - normalize_domain helper
  - DomainEmbeddingService.detect_domain
  - DomainEmbeddingService.embed_document (fail-open)
  - DomainEmbeddingService.rebuild_domain_index (fail-open)
  - RAGPipelineService.search() accepts domain param
  - Celery task registration
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 1. DOMAIN_ALIASES covers the main source types
# ---------------------------------------------------------------------------

def test_domain_aliases_cover_main_sources():
    from app.domains.ai.services.rag_pipeline_service import DOMAIN_ALIASES
    required_keys = {"candidates", "job_vacancies", "policy_blocks", "company_docs"}
    assert required_keys.issubset(set(DOMAIN_ALIASES.keys())), (
        f"DOMAIN_ALIASES missing keys: {required_keys - set(DOMAIN_ALIASES.keys())}"
    )


# ---------------------------------------------------------------------------
# 2. normalize_domain — known alias
# ---------------------------------------------------------------------------

def test_normalize_domain_known():
    from app.domains.ai.services.rag_pipeline_service import normalize_domain
    assert normalize_domain("candidates") == "talent"
    assert normalize_domain("job_vacancies") == "jobs"
    assert normalize_domain("policy_blocks") == "policy"
    assert normalize_domain("company_docs") == "company"
    assert normalize_domain("talent") == "talent"
    assert normalize_domain("jobs") == "jobs"


# ---------------------------------------------------------------------------
# 3. normalize_domain — unknown falls back to "general"
# ---------------------------------------------------------------------------

def test_normalize_domain_unknown_fallback():
    from app.domains.ai.services.rag_pipeline_service import normalize_domain
    assert normalize_domain("unknown_type") == "general"
    assert normalize_domain("foobar") == "general"
    assert normalize_domain("") == "general"


# ---------------------------------------------------------------------------
# 4. DomainEmbeddingService.detect_domain — candidates
# ---------------------------------------------------------------------------

def test_detect_domain_candidates():
    from app.shared.services.domain_embedding_service import DomainEmbeddingService
    svc = DomainEmbeddingService()
    assert svc.detect_domain("candidates") == "talent"


# ---------------------------------------------------------------------------
# 5. DomainEmbeddingService.detect_domain — policy_blocks
# ---------------------------------------------------------------------------

def test_detect_domain_policy():
    from app.shared.services.domain_embedding_service import DomainEmbeddingService
    svc = DomainEmbeddingService()
    assert svc.detect_domain("policy_blocks") == "policy"


# ---------------------------------------------------------------------------
# 6. DomainEmbeddingService.detect_domain — unknown returns "general"
# ---------------------------------------------------------------------------

def test_detect_domain_unknown():
    from app.shared.services.domain_embedding_service import DomainEmbeddingService
    svc = DomainEmbeddingService()
    assert svc.detect_domain("other") == "general"
    assert svc.detect_domain("xyz_source") == "general"


# ---------------------------------------------------------------------------
# 7. embed_document fails silently (fail-open) when EmbeddingService fails
# ---------------------------------------------------------------------------

def test_embed_document_fail_open():
    from app.shared.services.domain_embedding_service import DomainEmbeddingService
    svc = DomainEmbeddingService()

    mock_db = MagicMock()

    # Patch the EmbeddingService import to raise an exception
    with patch.dict("sys.modules", {
        "app.shared.intelligence.embedding_service": MagicMock(
            EmbeddingService=MagicMock(side_effect=RuntimeError("embedding unavailable"))
        )
    }):
        result = asyncio.run(
            svc.embed_document(
                content="test content",
                source_type="candidates",
                source_id="cand-001",
                company_id="comp-001",
                db=mock_db,
            )
        )
    # Must return False (fail-open) — no exception raised
    assert result is False


# ---------------------------------------------------------------------------
# 8. rebuild_domain_index returns 0 on DB error (fail-open)
# ---------------------------------------------------------------------------

def test_rebuild_domain_index_fail_open():
    from app.shared.services.domain_embedding_service import DomainEmbeddingService
    svc = DomainEmbeddingService()

    # DB that raises on execute
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(side_effect=RuntimeError("DB connection error"))

    result = asyncio.run(
        svc.rebuild_domain_index(domain="talent", company_id="comp-001", db=mock_db)
    )
    assert result == 0


# ---------------------------------------------------------------------------
# 9. RAGPipelineService.search() accepts domain param (mock db)
# ---------------------------------------------------------------------------

def test_rag_search_accepts_domain_param():
    """search() must accept domain kwarg and route it without raising."""
    from app.domains.ai.services.rag_pipeline_service import RAGPipelineService

    svc = RAGPipelineService()

    mock_db = MagicMock()
    # _bm25_search and _semantic_search will call db.execute — mock them out
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Patch generate_embedding to return None (degraded to BM25)
    with patch(
        "app.services.rag_pipeline_service.generate_embedding",
        new=AsyncMock(return_value=None),
    ):
        result = asyncio.run(
            svc.search(
                query="python developer",
                company_id="comp-001",
                db=mock_db,
                limit=10,
                alpha=0.0,
                domain="candidates",
            )
        )

    # domain should be normalized to "talent" in metadata
    assert result.metadata["domain"] == "talent"
    assert result.query == "python developer"


# ---------------------------------------------------------------------------
# 10. Celery task "rag.rebuild_domain_index" is registered
# ---------------------------------------------------------------------------

def test_celery_task_registered():
    from app.core.celery_app import celery_app
    # Importing celery_tasks registers all tasks
    import app.jobs.celery_tasks  # noqa: F401
    assert "rag.rebuild_domain_index" in celery_app.tasks, (
        "Task 'rag.rebuild_domain_index' not registered in celery_app.tasks"
    )
