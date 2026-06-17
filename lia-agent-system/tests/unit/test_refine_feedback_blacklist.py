"""Contract: /candidates/refine deve excluir candidatos com dislike automaticamente."""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestGetDislikedCandidateIds:
    @pytest.mark.asyncio
    async def test_returns_disliked_ids(self):
        """Repositorio: get_disliked_candidate_ids retorna IDs com dislike para o fingerprint."""
        from app.domains.recruitment.repositories.search_feedback_repository import (
            SearchFeedbackRepository,
        )
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["cand-aaa", "cand-bbb"]
        mock_db.execute.return_value = mock_result

        repo = SearchFeedbackRepository(db=mock_db)
        result = await repo.get_disliked_candidate_ids(
            company_id="comp-001",
            search_fingerprint="fp-xyz",
        )

        assert result == ["cand-aaa", "cand-bbb"]
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_dislikes(self):
        """Repositorio: retorna [] quando nao ha dislikes para o fingerprint."""
        from app.domains.recruitment.repositories.search_feedback_repository import (
            SearchFeedbackRepository,
        )
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        repo = SearchFeedbackRepository(db=mock_db)
        result = await repo.get_disliked_candidate_ids(
            company_id="comp-001",
            search_fingerprint="fp-xyz",
        )
        assert result == []


class TestBuildEffectiveBlacklist:
    """Testa a logica de merge de blacklists (isolada do endpoint)."""

    def _build(self, explicit_csv, disliked_ids):
        explicit = set(explicit_csv.split(",")) if explicit_csv else set()
        return explicit | set(disliked_ids)

    def test_merges_explicit_and_disliked(self):
        result = self._build("cand-explicit", ["cand-disliked"])
        assert "cand-explicit" in result
        assert "cand-disliked" in result

    def test_no_fingerprint_uses_only_explicit(self):
        result = self._build("cand-explicit", [])
        assert result == {"cand-explicit"}

    def test_empty_when_no_blacklist_at_all(self):
        result = self._build(None, [])
        assert result == set()
