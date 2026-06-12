"""
2.2: Wire WSI → lia_opinions (parecer) após triagem completa.

Garante que ao finalizar triagem com score WSI, um registro LiaOpinion
do tipo 'wsi' é criado com wsi_score na escala 0-100.

Fail-soft: falha no insert não aborta o fluxo de triagem.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_session(
    wsi_final_score: float = 7.5,
    recommendation: str = "aprovado",
    candidate_id: str | None = None,
    job_id: str | None = None,
    company_id: str | None = None,
):
    s = MagicMock()
    s.wsi_final_score = wsi_final_score
    s.recommendation = recommendation
    s.candidate_id = candidate_id or str(uuid.uuid4())
    s.job_id = job_id or str(uuid.uuid4())
    s.company_id = company_id or str(uuid.uuid4())
    s.metadata_json = {}
    s.session_metadata = {}
    s.total_score = wsi_final_score * 10
    s.approved = recommendation == "aprovado"
    s.wsi_session_id = None
    return s


WSI_SESSION_ID = "system:wsi-test-" + str(uuid.uuid4())


def _base_patches(mock_lio_instance: MagicMock):
    """Patches mínimos para _trigger_post_completion passar sem erros de infra."""
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
            return_value=MagicMock(
                update_wsi_lia_score=AsyncMock(return_value=1),
            ),
        ),
        patch(
            "app.domains.pipeline.repositories.lia_opinion_repository.LiaOpinionRepository",
            return_value=mock_lio_instance,
        ),
    ]


class TestWsiLiaOpinion:
    """2.2: create_wsi_opinion chamado após triagem WSI com score correto."""

    @pytest.mark.asyncio
    async def test_lia_opinion_created_after_triagem(self):
        """Após triagem WSI, LiaOpinionRepository.create_wsi_opinion é chamado."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        mock_lio = MagicMock()
        mock_lio.create_wsi_opinion = AsyncMock(return_value=str(uuid.uuid4()))

        session = _make_session(wsi_final_score=7.5)
        db = AsyncMock()
        db.flush = AsyncMock()

        patches = _base_patches(mock_lio)
        with (
            patches[0] as _p1,
            patches[1] as _p2,
            patches[2] as _p3,
            patches[3] as _p4,
            patches[4] as _p5,
        ):
            await _trigger_post_completion(db=db, session=session, response_scores=[])

        mock_lio.create_wsi_opinion.assert_called_once()

    @pytest.mark.asyncio
    async def test_lia_opinion_wsi_score_is_scaled_to_100(self):
        """wsi_score salvo em lia_opinions é na escala 0-100 (wsi_final_score × 10)."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        mock_lio = MagicMock()
        mock_lio.create_wsi_opinion = AsyncMock(return_value=str(uuid.uuid4()))

        session = _make_session(wsi_final_score=7.5)
        db = AsyncMock()
        db.flush = AsyncMock()

        patches = _base_patches(mock_lio)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            await _trigger_post_completion(db=db, session=session, response_scores=[])

        call_kwargs = mock_lio.create_wsi_opinion.call_args[1]
        assert call_kwargs["wsi_score"] == 75.0, (
            f"Esperado wsi_score=75.0 (7.5×10), recebido {call_kwargs['wsi_score']}"
        )

    @pytest.mark.asyncio
    async def test_lia_opinion_correct_candidate_and_vacancy(self):
        """create_wsi_opinion recebe candidate_id e job_vacancy_id corretos."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        mock_lio = MagicMock()
        capture = {}

        async def cap_create(**kwargs):
            capture.update(kwargs)
            return str(uuid.uuid4())

        mock_lio.create_wsi_opinion = cap_create

        cand_id = str(uuid.uuid4())
        vac_id = str(uuid.uuid4())
        session = _make_session(wsi_final_score=6.0, candidate_id=cand_id, job_id=vac_id)
        db = AsyncMock()
        db.flush = AsyncMock()

        patches = _base_patches(mock_lio)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            await _trigger_post_completion(db=db, session=session, response_scores=[])

        assert capture.get("candidate_id") == cand_id, f"candidate_id incorreto: {capture}"
        assert capture.get("job_vacancy_id") == vac_id, f"job_vacancy_id incorreto: {capture}"
        assert capture.get("wsi_score") == 60.0, f"wsi_score incorreto: {capture}"

    @pytest.mark.asyncio
    async def test_lia_opinion_fail_soft(self):
        """Se create_wsi_opinion lançar exception, _trigger_post_completion NÃO propaga."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        mock_lio = MagicMock()
        mock_lio.create_wsi_opinion = AsyncMock(side_effect=RuntimeError("DB explodiu"))

        session = _make_session(wsi_final_score=5.0)
        db = AsyncMock()
        db.flush = AsyncMock()

        patches = _base_patches(mock_lio)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            # Não deve levantar exceção
            result = await _trigger_post_completion(db=db, session=session, response_scores=[])

        # Fluxo continua — result é dict com actions
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_lia_opinion_not_called_when_no_candidate(self):
        """Se session não tem candidate_id, create_wsi_opinion não é chamado."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        mock_lio = MagicMock()
        mock_lio.create_wsi_opinion = AsyncMock(return_value=str(uuid.uuid4()))

        session = _make_session()
        session.candidate_id = None  # sem candidato

        db = AsyncMock()
        db.flush = AsyncMock()

        patches = _base_patches(mock_lio)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            await _trigger_post_completion(db=db, session=session, response_scores=[])

        mock_lio.create_wsi_opinion.assert_not_called()

    def test_create_wsi_opinion_method_exists_in_repo(self):
        """LiaOpinionRepository deve ter método create_wsi_opinion."""
        from app.domains.pipeline.repositories.lia_opinion_repository import LiaOpinionRepository
        assert hasattr(LiaOpinionRepository, "create_wsi_opinion"), (
            "LiaOpinionRepository precisa de método create_wsi_opinion (2.2)"
        )
