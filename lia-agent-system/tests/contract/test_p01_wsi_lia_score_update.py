"""
P0-1: WSI triagem completion deve atualizar vacancy_candidates.lia_score.
TDD Red → Green — 5 testes de contrato.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


def _make_session(
    candidate_id="cand-111",
    job_id="job-222",
    company_id="comp-333",
    wsi_final_score=8.5,
    recommendation="aprovado",
):
    s = MagicMock()
    s.candidate_id = candidate_id
    s.job_id = job_id
    s.company_id = company_id
    s.wsi_final_score = wsi_final_score
    s.recommendation = recommendation
    s.candidate_name = "Fulano Teste"
    s.metadata_json = {}
    s.token = "tok-abc"
    return s


def _base_patches(mock_repo_instance):
    """Patches comuns a todos os testes."""
    return [
        patch(
            "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
            new_callable=AsyncMock,
            return_value="wsi-session-abc",
        ),
        patch(
            "app.domains.recruitment.services.triagem_session_service.completion._get_event_dispatcher",
            return_value=MagicMock(on_screening_completed=AsyncMock()),
        ),
        # publish_platform_event é importado inline no try/except — mock no módulo real
        patch(
            "app.shared.messaging.platform_events.publish_platform_event",
            new_callable=AsyncMock,
        ),
        patch(
            "app.domains.candidates.repositories.vacancy_candidate_repository.VacancyCandidateRepository",
            return_value=mock_repo_instance,
        ),
    ]


class TestP01WsiUpdatesLiaScore:
    """P0-1: wsi_final_score (0-10) → vacancy_candidates.lia_score (0-100)."""

    @pytest.mark.asyncio
    async def test_completion_calls_update_wsi_lia_score(self):
        """Após persistir WSI results, deve chamar update_wsi_lia_score no repository."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )
        session = _make_session(wsi_final_score=8.5)
        db = AsyncMock(spec=AsyncSession)
        mock_repo = AsyncMock()
        mock_repo.update_wsi_lia_score = AsyncMock(return_value=1)

        patches = _base_patches(mock_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            await _trigger_post_completion(db, session, response_scores=[])

        mock_repo.update_wsi_lia_score.assert_called_once(), (
            "update_wsi_lia_score nunca chamado — P0-1 não implementado"
        )

    @pytest.mark.asyncio
    async def test_lia_score_conversion_scale(self):
        """wsi_final_score × 10 = lia_score (escala 0-100)."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )
        session = _make_session(wsi_final_score=7.5)
        db = AsyncMock(spec=AsyncSession)
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return 1

        mock_repo = AsyncMock()
        mock_repo.update_wsi_lia_score = AsyncMock(side_effect=capture)

        patches = _base_patches(mock_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            await _trigger_post_completion(db, session, response_scores=[])

        assert captured.get("lia_score") == 75.0, (
            f"Escala errada: esperado 75.0, recebido {captured.get('lia_score')}"
        )

    @pytest.mark.asyncio
    async def test_skip_update_when_wsi_persistence_fails(self):
        """Se _persist_wsi_results retorna None, não chama update_wsi_lia_score."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )
        session = _make_session(wsi_final_score=9.0)
        db = AsyncMock(spec=AsyncSession)
        mock_repo = AsyncMock()
        mock_repo.update_wsi_lia_score = AsyncMock(return_value=0)

        with (
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.domains.candidates.repositories.vacancy_candidate_repository.VacancyCandidateRepository",
                return_value=mock_repo,
            ),
        ):
            await _trigger_post_completion(db, session, response_scores=[])

        mock_repo.update_wsi_lia_score.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_uses_correct_ids(self):
        """O update usa candidate_id, vacancy_id e company_id corretos da sessão."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )
        session = _make_session(
            candidate_id="CAND-XYZ",
            job_id="JOB-ABC",
            company_id="COMP-DEF",
            wsi_final_score=6.0,
        )
        db = AsyncMock(spec=AsyncSession)
        captured = {}

        async def capture(**kwargs):
            captured.update(kwargs)
            return 1

        mock_repo = AsyncMock()
        mock_repo.update_wsi_lia_score = AsyncMock(side_effect=capture)

        patches = _base_patches(mock_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            await _trigger_post_completion(db, session, response_scores=[])

        assert captured.get("candidate_id") == "CAND-XYZ"
        assert captured.get("vacancy_id") == "JOB-ABC"
        assert captured.get("company_id") == "COMP-DEF"
        assert captured.get("lia_score") == 60.0

    @pytest.mark.asyncio
    async def test_update_fails_soft_does_not_raise(self):
        """Se update_wsi_lia_score lança exceção, não propaga (fail-soft)."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )
        session = _make_session(wsi_final_score=8.0)
        db = AsyncMock(spec=AsyncSession)
        mock_repo = AsyncMock()
        mock_repo.update_wsi_lia_score = AsyncMock(
            side_effect=Exception("DB timeout simulado")
        )

        patches = _base_patches(mock_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            result = await _trigger_post_completion(db, session, response_scores=[])

        assert result is not None
