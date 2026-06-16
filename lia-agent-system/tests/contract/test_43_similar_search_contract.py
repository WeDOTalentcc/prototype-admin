"""
4.3: Busca semantica de candidatos similares via pgvector.
"""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSimilarSearchContract:

    def test_search_similar_returns_list(self):
        from app.domains.ai.repositories.candidate_embedding_repository import (
            CandidateEmbeddingRepository,
        )
        import inspect
        sig = inspect.signature(CandidateEmbeddingRepository.search_similar)
        assert "company_id" in sig.parameters
        assert "embedding" in sig.parameters

    @pytest.mark.asyncio
    async def test_search_similar_filters_by_company(self):
        from app.domains.ai.repositories.candidate_embedding_repository import (
            CandidateEmbeddingRepository,
        )
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
        repo = CandidateEmbeddingRepository(db)
        results = await repo.search_similar(
            embedding=[0.1] * 768, company_id="comp-1", limit=5,
        )
        assert isinstance(results, list)
        sql = str(db.execute.call_args[0][0])
        assert "company_id" in sql

    def test_service_has_find_similar(self):
        from app.domains.ai.services.candidate_embedding_service import (
            CandidateEmbeddingService,
        )
        assert hasattr(CandidateEmbeddingService, "find_similar_candidates")

    @pytest.mark.asyncio
    async def test_find_similar_uses_embedding_repo(self):
        from app.domains.ai.services.candidate_embedding_service import (
            CandidateEmbeddingService,
        )
        svc = CandidateEmbeddingService()
        db = AsyncMock()
        with (
            patch("app.shared.intelligence.embedding_service.EmbeddingService") as mock_embed_cls,
            patch(
                "app.domains.ai.repositories.candidate_embedding_repository.CandidateEmbeddingRepository"
            ) as mock_repo_cls,
        ):
            mock_embed = AsyncMock()
            mock_embed.generate_embedding = AsyncMock(return_value=[0.1] * 768)
            mock_embed_cls.return_value = mock_embed

            mock_repo = AsyncMock()
            mock_repo.search_similar = AsyncMock(return_value=[
                {"candidate_id": "cand-2", "similarity": 0.95, "name": "Ana"},
            ])
            mock_repo_cls.return_value = mock_repo

            results = await svc.find_similar_candidates(
                candidate={"id": "cand-1", "summary": "Backend dev Python com 5 anos experiencia"},
                company_id="comp-1",
                db=db,
                limit=5,
            )
            assert len(results) == 1
            assert results[0]["candidate_id"] == "cand-2"
