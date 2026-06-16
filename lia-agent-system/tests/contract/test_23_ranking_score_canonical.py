"""
2.3: calculate_ranking_score como fórmula canônica para lia_score pós-triagem.

Garante que:
- LiaScoreService.calculate_ranking_score é usado (não magic wsi × 10 inline)
- cv_score existente na VacancyCandidate row é lido e passado para a fórmula
- ai_analysis é persistido com o score_breakdown JSON
- fail-soft: erros no ranking service não abortam o fluxo
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


CANDIDATE_ID = str(uuid.uuid4())
VACANCY_ID = str(uuid.uuid4())
COMPANY_ID = str(uuid.uuid4())
WSI_SESSION_ID = "system:wsi-" + str(uuid.uuid4())

WSI_FINAL_SCORE = 7.5   # 0-10
WSI_LIA_SCORE = 75.0    # 0-100


def _make_session(
    wsi_final_score: float = WSI_FINAL_SCORE,
    candidate_id: str = CANDIDATE_ID,
    job_id: str = VACANCY_ID,
    company_id: str = COMPANY_ID,
):
    s = MagicMock()
    s.wsi_final_score = wsi_final_score
    s.recommendation = "aprovado"
    s.candidate_id = candidate_id
    s.job_id = job_id
    s.company_id = company_id
    s.metadata_json = {}
    s.session_metadata = {}
    s.total_score = wsi_final_score * 10
    s.approved = True
    return s


def _make_ranking_result(score: float = 72.5):
    """Cria um RankingScoreResult mock."""
    result = MagicMock()
    result.ranking_score = score
    result.breakdown = MagicMock()
    result.breakdown.to_dict.return_value = {
        "wsi_score": WSI_LIA_SCORE,
        "rubricas_score": 65.0,
        "weighted_wsi": 22.5,
        "weighted_rubricas": 26.0,
        "formula": "ranking_v1",
    }
    return result


def _base_patches(mock_vc_repo, mock_lio_repo=None):
    """Patches mínimos para _trigger_post_completion não explodir."""
    mock_lio = mock_lio_repo or MagicMock(
        create_wsi_opinion=AsyncMock(return_value=str(uuid.uuid4()))
    )
    return [
        patch(
            "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
            new_callable=AsyncMock,
            return_value=WSI_SESSION_ID,
        ),
        patch(
            "app.domains.recruitment.services.triagem_session_service.completion._get_event_dispatcher",
            return_value=MagicMock(on_screening_completed=AsyncMock()),
        ),
        patch(
            "app.shared.messaging.platform_events.publish_platform_event",
            new_callable=AsyncMock,
        ),
        patch(
            "app.domains.candidates.repositories.vacancy_candidate_repository.VacancyCandidateRepository",
            return_value=mock_vc_repo,
        ),
        patch(
            "app.domains.pipeline.repositories.lia_opinion_repository.LiaOpinionRepository",
            return_value=mock_lio,
        ),
    ]


class TestRankingScoreCanonical:
    """2.3: calculate_ranking_score é a fórmula canônica para lia_score pós-WSI."""

    def test_vc_repo_has_get_cv_score_method(self):
        """VacancyCandidateRepository deve ter get_cv_score() para ler score existente."""
        from app.domains.candidates.repositories.vacancy_candidate_repository import VacancyCandidateRepository
        assert hasattr(VacancyCandidateRepository, "get_cv_score"), (
            "VacancyCandidateRepository precisa de método get_cv_score (2.3)"
        )

    def test_vc_repo_has_update_score_breakdown_method(self):
        """VacancyCandidateRepository deve ter update_score_breakdown() para persistir ai_analysis."""
        from app.domains.candidates.repositories.vacancy_candidate_repository import VacancyCandidateRepository
        assert hasattr(VacancyCandidateRepository, "update_score_breakdown"), (
            "VacancyCandidateRepository precisa de método update_score_breakdown (2.3)"
        )

    @pytest.mark.asyncio
    async def test_ranking_score_updates_ai_analysis(self):
        """Após triagem, ai_analysis é atualizado com score_breakdown."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        capture = {}
        ranking_result = _make_ranking_result(score=72.5)

        mock_vc = MagicMock()
        mock_vc.update_wsi_lia_score = AsyncMock(return_value=1)
        mock_vc.get_cv_score = AsyncMock(return_value=65.0)

        async def cap_update_breakdown(**kwargs):
            capture.update(kwargs)
            return 1
        mock_vc.update_score_breakdown = cap_update_breakdown

        session = _make_session()
        db = AsyncMock()
        db.flush = AsyncMock()

        with (
            patch("app.domains.cv_screening.services.lia_score_service.LIAScoreService.calculate_ranking_score",
                  return_value=ranking_result) as mock_ranking,
        ):
            patches = _base_patches(mock_vc)
            with patches[0], patches[1], patches[2], patches[3], patches[4]:
                await _trigger_post_completion(db=db, session=session, response_scores=[])

        # update_score_breakdown foi chamado com ai_analysis
        assert "ai_analysis" in capture or mock_vc.update_score_breakdown.called, (
            "update_score_breakdown deve ser chamado com ai_analysis"
        )

    @pytest.mark.asyncio
    async def test_ranking_score_uses_existing_cv_score(self):
        """get_cv_score é chamado para obter cv_score existente da VC row."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        mock_vc = MagicMock()
        mock_vc.update_wsi_lia_score = AsyncMock(return_value=1)
        mock_vc.get_cv_score = AsyncMock(return_value=80.0)
        mock_vc.update_score_breakdown = AsyncMock(return_value=1)

        session = _make_session()
        db = AsyncMock()
        db.flush = AsyncMock()

        patches = _base_patches(mock_vc)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            await _trigger_post_completion(db=db, session=session, response_scores=[])

        mock_vc.get_cv_score.assert_called_once()

    @pytest.mark.asyncio
    async def test_ranking_score_fail_soft(self):
        """Se update_score_breakdown falhar, fluxo principal não é abortado."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        mock_vc = MagicMock()
        mock_vc.update_wsi_lia_score = AsyncMock(return_value=1)
        mock_vc.get_cv_score = AsyncMock(side_effect=RuntimeError("DB error"))
        mock_vc.update_score_breakdown = AsyncMock(return_value=1)

        session = _make_session()
        db = AsyncMock()
        db.flush = AsyncMock()

        patches = _base_patches(mock_vc)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            result = await _trigger_post_completion(db=db, session=session, response_scores=[])

        assert isinstance(result, dict), "Fluxo não deve abortar mesmo com erro em get_cv_score"

    def test_completion_references_ranking_score_or_score_breakdown(self):
        """completion.py deve referenciar score_breakdown ou calculate_ranking_score (2.3)."""
        import os
        path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..",
            "app", "domains", "recruitment", "services",
            "triagem_session_service", "completion.py",
        ))
        with open(path) as f:
            source = f.read()
        has_breakdown = "score_breakdown" in source or "calculate_ranking_score" in source or "update_score_breakdown" in source
        assert has_breakdown, (
            "completion.py deve chamar update_score_breakdown ou calculate_ranking_score (2.3)"
        )
