"""
P0-1: WSI triagem completion deve atualizar vacancy_candidates.lia_score.

Red test — falha antes do fix (nenhum código propaga wsi_final_score para vacancy_candidates.lia_score).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_session(
    candidate_id="cand-111",
    job_id="job-222",
    company_id="comp-333",
    wsi_final_score=8.5,
    recommendation="aprovado",
):
    session = MagicMock()
    session.candidate_id = candidate_id
    session.job_id = job_id
    session.company_id = company_id
    session.wsi_final_score = wsi_final_score
    session.recommendation = recommendation
    session.candidate_name = "Fulano Teste"
    session.metadata_json = {}
    return session


# ── tests ─────────────────────────────────────────────────────────────────────

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

        with (
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
                new_callable=AsyncMock,
                return_value="wsi-session-abc",
            ),
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._dispatch_screening_completed",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.candidates.repositories.vacancy_candidate_repository.VacancyCandidateRepository"
            ) as MockRepo,
        ):
            mock_repo_instance = AsyncMock()
            mock_repo_instance.update_wsi_lia_score = AsyncMock(return_value=1)
            MockRepo.return_value = mock_repo_instance

            await _trigger_post_completion(db, session, response_scores=[])

        mock_repo_instance.update_wsi_lia_score.assert_called_once()
        call_kwargs = mock_repo_instance.update_wsi_lia_score.call_args
        assert call_kwargs is not None, "update_wsi_lia_score nunca foi chamado (P0-1 não implementado)"

    @pytest.mark.asyncio
    async def test_lia_score_conversion_scale(self):
        """wsi_final_score 0-10 deve ser convertido para lia_score 0-100 (×10)."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        session = _make_session(wsi_final_score=7.5)
        db = AsyncMock(spec=AsyncSession)

        captured_score = {}

        async def capture_update(**kwargs):
            captured_score.update(kwargs)
            return 1

        with (
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
                new_callable=AsyncMock,
                return_value="wsi-session-xyz",
            ),
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._dispatch_screening_completed",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.candidates.repositories.vacancy_candidate_repository.VacancyCandidateRepository"
            ) as MockRepo,
        ):
            mock_repo_instance = AsyncMock()
            mock_repo_instance.update_wsi_lia_score = AsyncMock(side_effect=capture_update)
            MockRepo.return_value = mock_repo_instance

            await _trigger_post_completion(db, session, response_scores=[])

        assert captured_score.get("lia_score") == 75.0, (
            f"Escala errada: esperado 75.0 (7.5×10), recebido {captured_score.get('lia_score')}"
        )

    @pytest.mark.asyncio
    async def test_skip_update_when_wsi_persistence_fails(self):
        """Se _persist_wsi_results falha (retorna None), não deve chamar update_wsi_lia_score."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        session = _make_session(wsi_final_score=9.0)
        db = AsyncMock(spec=AsyncSession)

        with (
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
                new_callable=AsyncMock,
                return_value=None,  # persistência falhou
            ),
            patch(
                "app.domains.candidates.repositories.vacancy_candidate_repository.VacancyCandidateRepository"
            ) as MockRepo,
        ):
            mock_repo_instance = AsyncMock()
            MockRepo.return_value = mock_repo_instance

            await _trigger_post_completion(db, session, response_scores=[])

        mock_repo_instance.update_wsi_lia_score.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_uses_correct_ids(self):
        """O update deve usar candidate_id, job_id e company_id corretos da sessão."""
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

        with (
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
                new_callable=AsyncMock,
                return_value="wsi-ok",
            ),
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._dispatch_screening_completed",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.candidates.repositories.vacancy_candidate_repository.VacancyCandidateRepository"
            ) as MockRepo,
        ):
            mock_repo_instance = AsyncMock()
            mock_repo_instance.update_wsi_lia_score = AsyncMock(side_effect=capture)
            MockRepo.return_value = mock_repo_instance

            await _trigger_post_completion(db, session, response_scores=[])

        assert captured.get("candidate_id") == "CAND-XYZ"
        assert captured.get("vacancy_id") == "JOB-ABC"
        assert captured.get("company_id") == "COMP-DEF"
        assert captured.get("lia_score") == 60.0

    @pytest.mark.asyncio
    async def test_update_fails_soft_does_not_raise(self):
        """Se update_wsi_lia_score lança exceção, _trigger_post_completion não deve propagar (fail-soft)."""
        from app.domains.recruitment.services.triagem_session_service.completion import (
            _trigger_post_completion,
        )

        session = _make_session(wsi_final_score=8.0)
        db = AsyncMock(spec=AsyncSession)

        with (
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._persist_wsi_results",
                new_callable=AsyncMock,
                return_value="wsi-ok",
            ),
            patch(
                "app.domains.recruitment.services.triagem_session_service.completion._dispatch_screening_completed",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.candidates.repositories.vacancy_candidate_repository.VacancyCandidateRepository"
            ) as MockRepo,
        ):
            mock_repo_instance = AsyncMock()
            mock_repo_instance.update_wsi_lia_score = AsyncMock(
                side_effect=Exception("DB timeout simulado")
            )
            MockRepo.return_value = mock_repo_instance

            # Não deve levantar — fail-soft
            result = await _trigger_post_completion(db, session, response_scores=[])

        assert result is not None  # retornou normalmente
