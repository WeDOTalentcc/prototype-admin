"""
4.1: Pipeline de embeddings de candidatos.

Garante que:
1. CandidateEmbedding model SQLAlchemy existe com vector(768)
2. CandidateEmbeddingRepository tem upsert_embedding + search_similar
3. CandidateEmbeddingService gera texto + chama EmbeddingService + persiste
4. Multi-tenancy: company_id obrigatorio em toda operacao
"""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestCandidateEmbeddingModel:
    """4.1a: Model existe com vector column."""

    def test_model_exists(self):
        from app.models.candidate_embedding import CandidateEmbedding
        assert hasattr(CandidateEmbedding, "embedding")
        assert hasattr(CandidateEmbedding, "company_id")
        assert hasattr(CandidateEmbedding, "candidate_id")

    def test_model_has_embedding_text(self):
        from app.models.candidate_embedding import CandidateEmbedding
        assert hasattr(CandidateEmbedding, "embedding_text")


class TestCandidateEmbeddingRepository:
    """4.1b: Repository com upsert + search."""

    def test_repo_exists(self):
        from app.domains.ai.repositories.candidate_embedding_repository import (
            CandidateEmbeddingRepository,
        )
        assert hasattr(CandidateEmbeddingRepository, "upsert_embedding")
        assert hasattr(CandidateEmbeddingRepository, "search_similar")

    @pytest.mark.asyncio
    async def test_upsert_calls_db(self):
        from app.domains.ai.repositories.candidate_embedding_repository import (
            CandidateEmbeddingRepository,
        )
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(rowcount=1))
        repo = CandidateEmbeddingRepository(db)
        rows = await repo.upsert_embedding(
            candidate_id="cand-1",
            company_id="comp-1",
            embedding=[0.1] * 768,
            embedding_text="Python developer with 5 years exp",
        )
        assert rows == 1
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_similar_requires_company_id(self):
        from app.domains.ai.repositories.candidate_embedding_repository import (
            CandidateEmbeddingRepository,
        )
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
        repo = CandidateEmbeddingRepository(db)
        with pytest.raises((ValueError, TypeError)):
            await repo.search_similar(
                embedding=[0.1] * 768,
                company_id=None,
                limit=10,
            )


class TestCandidateEmbeddingService:
    """4.1c: Service gera embedding text + chama provider."""

    def test_service_exists(self):
        from app.domains.ai.services.candidate_embedding_service import (
            CandidateEmbeddingService,
        )
        assert hasattr(CandidateEmbeddingService, "embed_candidate")

    def test_build_embedding_text(self):
        from app.domains.ai.services.candidate_embedding_service import (
            CandidateEmbeddingService,
        )
        svc = CandidateEmbeddingService()
        text = svc.build_embedding_text({
            "name": "Ana Silva",
            "summary": "Backend developer with Python expertise",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience": [{"title": "Sr Dev", "company": "Acme"}],
        })
        assert "Python" in text
        assert "Backend" in text
        assert len(text) > 20
