"""
P0-2: VacancyCandidate ORM deve ter campos cv_score, cv_fit_score,
sub_status, screening_completed_at, ai_analysis.
TDD Red → Green — testes de contrato do modelo.
"""
import pytest
from sqlalchemy import inspect as sa_inspect


class TestP02VacancyCandidateOrmFields:
    """P0-2: campos de score pós-triagem no ORM VacancyCandidate."""

    def _get_column_names(self):
        from app.models.candidate import VacancyCandidate
        mapper = sa_inspect(VacancyCandidate)
        return {col.key for col in mapper.column_attrs}

    def test_cv_score_column_exists(self):
        """cv_score Float nullable deve existir no ORM."""
        cols = self._get_column_names()
        assert "cv_score" in cols, (
            "ORM VacancyCandidate não tem cv_score — P0-2 não implementado"
        )

    def test_cv_fit_score_column_exists(self):
        """cv_fit_score Float nullable deve existir no ORM."""
        cols = self._get_column_names()
        assert "cv_fit_score" in cols, (
            "ORM VacancyCandidate não tem cv_fit_score — P0-2 não implementado"
        )

    def test_sub_status_column_exists(self):
        """sub_status String nullable deve existir no ORM."""
        cols = self._get_column_names()
        assert "sub_status" in cols, (
            "ORM VacancyCandidate não tem sub_status — P0-2 não implementado"
        )

    def test_screening_completed_at_column_exists(self):
        """screening_completed_at DateTime nullable deve existir no ORM."""
        cols = self._get_column_names()
        assert "screening_completed_at" in cols, (
            "ORM VacancyCandidate não tem screening_completed_at — P0-2 não implementado"
        )

    def test_ai_analysis_column_exists(self):
        """ai_analysis JSON nullable deve existir no ORM."""
        cols = self._get_column_names()
        assert "ai_analysis" in cols, (
            "ORM VacancyCandidate não tem ai_analysis — P0-2 não implementado"
        )

    def test_column_types_are_correct(self):
        """Valida tipos SQLAlchemy dos novos campos."""
        from app.models.candidate import VacancyCandidate
        from sqlalchemy import Float, String, DateTime, JSON
        mapper = sa_inspect(VacancyCandidate)
        col_map = {col.key: col for col in mapper.column_attrs}

        float_cols = ["cv_score", "cv_fit_score"]
        for name in float_cols:
            if name in col_map:
                col = col_map[name].columns[0]
                assert isinstance(col.type, Float), (
                    f"{name} deve ser Float, é {type(col.type).__name__}"
                )

        if "sub_status" in col_map:
            col = col_map["sub_status"].columns[0]
            assert isinstance(col.type, String), (
                f"sub_status deve ser String, é {type(col.type).__name__}"
            )

        if "screening_completed_at" in col_map:
            col = col_map["screening_completed_at"].columns[0]
            assert isinstance(col.type, DateTime), (
                f"screening_completed_at deve ser DateTime, é {type(col.type).__name__}"
            )

        if "ai_analysis" in col_map:
            col = col_map["ai_analysis"].columns[0]
            assert isinstance(col.type, JSON), (
                f"ai_analysis deve ser JSON, é {type(col.type).__name__}"
            )

    def test_migration_263_exists(self):
        """Migration 263 deve existir em alembic/versions/."""
        import os
        versions_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "alembic", "versions"
        )
        versions_dir = os.path.abspath(versions_dir)
        files = os.listdir(versions_dir)
        migration_263 = [f for f in files if f.startswith("263_")]
        assert migration_263, (
            "Migration 263_*.py não encontrada em alembic/versions/ — P0-2 não implementado"
        )
