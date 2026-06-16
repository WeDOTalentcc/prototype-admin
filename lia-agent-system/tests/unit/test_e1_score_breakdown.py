"""
E1 — Score Clicável Kanban

Testa o endpoint GET /{job_id}/candidates/{candidate_id}/breakdown:
- Retorna detalhamento quando avaliação existe
- Retorna 404 quando não existe
- Campos obrigatórios presentes
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime


class TestScoreBreakdownEndpoint:

    def _make_fake_evaluation(self, score=82.0):
        ev = MagicMock()
        ev.id = uuid4()
        ev.score = score
        ev.candidate_id = uuid4()
        ev.job_vacancy_id = uuid4()
        ev.evaluated_at = datetime.utcnow()
        ev.model_version = "claude-sonnet-4-6"
        ev.strengths = ["Forte experiência em Python", "Liderança técnica"]
        ev.concerns = ["Sem experiência em cloud"]
        ev.reasoning = "Candidato apresenta sólida base técnica."
        ev.recommendation = "Aprovado"
        ev.evaluations = [
            {
                "requirement": "Python 3.x",
                "priority": "essential",
                "level": "exceeds",
                "points": 100,
                "multiplier": 3,
                "weighted_points": 300,
                "evidence": "7 anos Python",
                "confidence": 0.95,
            }
        ]
        ev.auto_excluded = False
        return ev

    @pytest.mark.asyncio
    async def test_breakdown_returns_score_and_fields(self):
        """Endpoint retorna score e campos obrigatórios quando avaliação existe."""
        from app.api.v1.rubric_evaluation import get_score_breakdown

        fake_ev = self._make_fake_evaluation(score=85.0)
        job_id = fake_ev.job_vacancy_id
        candidate_id = fake_ev.candidate_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_ev

        db = MagicMock()
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_score_breakdown(job_id=job_id, candidate_id=candidate_id, db=db)

        assert result["score"] == 85.0
        assert "strengths" in result
        assert "concerns" in result
        assert "reasoning" in result
        assert "evaluations" in result
        assert result["candidate_id"] == str(candidate_id)
        assert result["job_vacancy_id"] == str(job_id)

    @pytest.mark.asyncio
    async def test_breakdown_404_when_no_evaluation(self):
        """Retorna 404 quando não há avaliação para o par candidato+vaga."""
        from app.api.v1.rubric_evaluation import get_score_breakdown
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = MagicMock()
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_score_breakdown(
                job_id=uuid4(), candidate_id=uuid4(), db=db
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_breakdown_includes_strengths_list(self):
        """strengths é uma lista (pode ser vazia)."""
        from app.api.v1.rubric_evaluation import get_score_breakdown

        fake_ev = self._make_fake_evaluation()
        fake_ev.strengths = []
        fake_ev.concerns = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_ev

        db = MagicMock()
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_score_breakdown(
            job_id=fake_ev.job_vacancy_id,
            candidate_id=fake_ev.candidate_id,
            db=db,
        )
        assert isinstance(result["strengths"], list)
        assert isinstance(result["concerns"], list)

    @pytest.mark.asyncio
    async def test_breakdown_evaluated_at_isoformat(self):
        """evaluated_at retornado como ISO string."""
        from app.api.v1.rubric_evaluation import get_score_breakdown

        fake_ev = self._make_fake_evaluation()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_ev

        db = MagicMock()
        db.execute = AsyncMock(return_value=mock_result)

        result = await get_score_breakdown(
            job_id=fake_ev.job_vacancy_id,
            candidate_id=fake_ev.candidate_id,
            db=db,
        )
        # evaluated_at deve ser string ISO ou None
        assert result["evaluated_at"] is None or isinstance(result["evaluated_at"], str)
