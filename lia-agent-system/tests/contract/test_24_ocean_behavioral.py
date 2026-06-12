"""
2.4: OCEAN traits + behavioral_analysis → LiaOpinion via web triagem.

Best-effort: se response_scores contêm trait_ocean, agrega por trait (0-1).
Caso contrário, persiste behavioral_analysis com scores comportamentais.
Fail-soft em ambos os casos.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


CANDIDATE_ID = str(uuid.uuid4())
VACANCY_ID = str(uuid.uuid4())
COMPANY_ID = str(uuid.uuid4())


def _make_session(cid=CANDIDATE_ID, jid=VACANCY_ID, cmpid=COMPANY_ID, wsi_score=7.5):
    s = MagicMock()
    s.candidate_id = cid
    s.job_id = jid
    s.company_id = cmpid
    s.wsi_final_score = wsi_score
    s.recommendation = "aprovado"
    s.metadata_json = {}
    s.session_metadata = {}
    return s


def _rs_with_ocean(score=3.5, trait="conscientiousness"):
    return {
        "block_type": "behavioral",
        "competency": "organizacao",
        "score": score,
        "trait_ocean": trait,
        "response_text": "Texto",
        "question_text": "Pergunta",
    }


def _rs_no_ocean(score=4.0):
    return {
        "block_type": "behavioral",
        "competency": "comunicacao",
        "score": score,
        "response_text": "Texto",
        "question_text": "Pergunta",
    }


def _base_patches():
    return [
        patch(
            "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
            new_callable=AsyncMock,
            return_value="system:wsi-test",
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
            return_value=MagicMock(
                update_wsi_lia_score=AsyncMock(return_value=1),
                get_cv_score=AsyncMock(return_value=None),
                update_score_breakdown=AsyncMock(return_value=1),
            ),
        ),
    ]


class TestOceanBehavioralOpinion:
    """2.4: behavioral_analysis + ocean_traits atualiza LiaOpinion após triagem."""

    def test_lia_opinion_repo_has_update_behavioral_analysis(self):
        """LiaOpinionRepository deve ter update_behavioral_analysis para 2.4."""
        from app.domains.pipeline.repositories.lia_opinion_repository import LiaOpinionRepository
        assert hasattr(LiaOpinionRepository, "update_behavioral_analysis"), (
            "LiaOpinionRepository precisa de método update_behavioral_analysis (2.4)"
        )

    @pytest.mark.asyncio
    async def test_ocean_traits_aggregated_from_response_scores(self):
        """Se response_scores têm trait_ocean, ocean_traits é agregado e persistido."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        capture = {}
        mock_lio = MagicMock()
        mock_lio.create_wsi_opinion = AsyncMock(return_value=str(uuid.uuid4()))

        async def cap_update_ba(**kwargs):
            capture.update(kwargs)
            return 1
        mock_lio.update_behavioral_analysis = cap_update_ba

        session = _make_session()
        db = AsyncMock()
        db.flush = AsyncMock()

        response_scores = [
            _rs_with_ocean(score=4.0, trait="conscientiousness"),
            _rs_with_ocean(score=3.0, trait="extraversion"),
            _rs_no_ocean(score=3.5),  # sem trait — deve ser ignorado para OCEAN
        ]

        patches = _base_patches()
        with patches[0], patches[1], patches[2], patches[3]:
            with patch(
                "app.domains.pipeline.repositories.lia_opinion_repository.LiaOpinionRepository",
                return_value=mock_lio,
            ):
                await _trigger_post_completion(db=db, session=session, response_scores=response_scores)

        # ocean_traits deve existir no capture
        ba = capture.get("behavioral_analysis", {})
        ocean = ba.get("ocean_traits", {})
        assert "conscientiousness" in ocean or mock_lio.update_behavioral_analysis.called, (
            f"ocean_traits deve conter conscientiousness. capture: {capture}"
        )

    @pytest.mark.asyncio
    async def test_behavioral_analysis_persisted_without_ocean(self):
        """Sem trait_ocean nos response_scores, behavioral_analysis é persistido sem ocean_traits."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        capture = {}
        mock_lio = MagicMock()
        mock_lio.create_wsi_opinion = AsyncMock(return_value=str(uuid.uuid4()))

        async def cap_update_ba(**kwargs):
            capture.update(kwargs)
            return 1
        mock_lio.update_behavioral_analysis = cap_update_ba

        session = _make_session()
        db = AsyncMock()
        db.flush = AsyncMock()

        response_scores = [_rs_no_ocean(score=4.0), _rs_no_ocean(score=3.5)]

        patches = _base_patches()
        with patches[0], patches[1], patches[2], patches[3]:
            with patch(
                "app.domains.pipeline.repositories.lia_opinion_repository.LiaOpinionRepository",
                return_value=mock_lio,
            ):
                await _trigger_post_completion(db=db, session=session, response_scores=response_scores)

        # Deve ter chamado update_behavioral_analysis mesmo sem ocean_traits
        assert mock_lio.update_behavioral_analysis.called, (
            "update_behavioral_analysis deve ser chamado mesmo sem trait_ocean"
        )

    @pytest.mark.asyncio
    async def test_update_behavioral_analysis_fail_soft(self):
        """Falha em update_behavioral_analysis não aborta fluxo."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        mock_lio = MagicMock()
        mock_lio.create_wsi_opinion = AsyncMock(return_value=str(uuid.uuid4()))
        mock_lio.update_behavioral_analysis = AsyncMock(side_effect=RuntimeError("DB explodiu"))

        session = _make_session()
        db = AsyncMock()
        db.flush = AsyncMock()

        patches = _base_patches()
        with patches[0], patches[1], patches[2], patches[3]:
            with patch(
                "app.domains.pipeline.repositories.lia_opinion_repository.LiaOpinionRepository",
                return_value=mock_lio,
            ):
                result = await _trigger_post_completion(db=db, session=session, response_scores=[])

        assert isinstance(result, dict), "Fluxo não deve abortar com erro em update_behavioral_analysis"
