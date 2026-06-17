"""
RED tests: verify that update() calls db.add() before db.commit().

Without db.add(), detached objects are silently not persisted (SQLAlchemy dirty
tracking only works for objects loaded in the same session).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, call


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()  # add() is sync in SQLAlchemy async
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestVacancyCandidateRepositoryUpdate:
    async def test_update_calls_db_add_before_commit(self, mock_db):
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        from app.models.candidate import VacancyCandidate

        repo = VacancyCandidateRepository(db=mock_db)
        vc = MagicMock(spec=VacancyCandidate)

        await repo.update(vc)

        mock_db.add.assert_called_once_with(vc)
        # add must be called BEFORE commit
        assert mock_db.add.call_args_list[0] == call(vc)
        mock_db.commit.assert_called_once()


class TestCandidateRepositoryUpdate:
    async def test_update_calls_db_add_before_commit(self, mock_db):
        from app.domains.candidates.repositories.candidate_repository import (
            CandidateRepository,
        )
        from app.models.candidate import Candidate

        repo = CandidateRepository(db=mock_db)
        candidate = MagicMock(spec=Candidate)

        await repo.update(candidate)

        mock_db.add.assert_called_once_with(candidate)
        mock_db.commit.assert_called_once()


class TestCandidateFavoritesRepositoryUpdate:
    async def test_update_calls_db_add_before_commit(self, mock_db):
        from app.domains.candidates.repositories.candidate_favorites_repository import (
            CandidateFavoritesRepository,
        )
        from app.models.candidate import CandidateFavorite

        repo = CandidateFavoritesRepository(db=mock_db)
        favorite = MagicMock(spec=CandidateFavorite)

        await repo.update(favorite)

        mock_db.add.assert_called_once_with(favorite)
        mock_db.commit.assert_called_once()
