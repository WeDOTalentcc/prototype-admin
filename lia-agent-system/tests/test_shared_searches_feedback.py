"""
Testes — Public Shared Searches: submit_feedback (H.3c)

Cobre:
- Feedback gravado corretamente (create + update)
- Notificação Bell disparada ao created_by_user_id quando feedback enviado
- Falha de notificação não propaga exceção (plataforma não quebra)
- Candidato não encontrado retorna 404
- Sessão inválida retorna 403
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

SHARED_SEARCH_ID = uuid4()
COMPANY_ID = uuid4()
CREATOR_USER_ID = uuid4()
CANDIDATE_ID = uuid4()
ACCESS_TOKEN = "tok_test_abc"
REVIEWER_EMAIL = "gestor@empresa.com"


def _make_search(title="Shortlist Dev Sênior"):
    s = MagicMock()
    s.id = SHARED_SEARCH_ID
    s.company_id = COMPANY_ID
    s.created_by_user_id = CREATOR_USER_ID
    s.title = title
    s.snapshot_payload = {"candidates": [{"id": str(CANDIDATE_ID)}]}
    return s


def _make_access():
    a = MagicMock()
    a.shared_search_id = SHARED_SEARCH_ID
    a.email = REVIEWER_EMAIL
    return a


def _make_session():
    return {
        "shared_search_id": str(SHARED_SEARCH_ID),
        "email": REVIEWER_EMAIL,
    }


class TestSubmitFeedbackNotification:
    """Testa notificação pós-feedback (H.3c)."""

    @pytest.mark.asyncio
    async def test_notificacao_bell_disparada_apos_feedback(self):
        """Após salvar feedback, notification_service.create_notification é chamado."""
        from app.api.public.shared_searches import submit_feedback
        from app.schemas.shared_search import SubmitFeedbackRequest, FeedbackDecision

        db = AsyncMock()
        # simulate scalar_one_or_none → None (novo feedback)
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.add = MagicMock()
        db.commit = AsyncMock()

        mock_feedback = MagicMock()
        mock_feedback.id = uuid4()
        mock_feedback.candidate_id = CANDIDATE_ID
        mock_feedback.reviewer_email = REVIEWER_EMAIL
        mock_feedback.decision = MagicMock(value="approved")
        mock_feedback.rating = 5
        mock_feedback.comment = "Excelente perfil"
        mock_feedback.created_at = datetime.utcnow()

        db.refresh = AsyncMock(side_effect=lambda obj: None)

        request_data = MagicMock()
        request_data.candidate_id = CANDIDATE_ID
        request_data.decision = MagicMock(value="approved")
        request_data.rating = 5
        request_data.comment = "Excelente perfil"

        # Mockar select() para evitar validação de coluna SQLAlchemy
        mock_select_result = MagicMock()
        mock_select_result.where = MagicMock(return_value=mock_select_result)
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", mock_feedback.id) or None)

        with patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(_make_search(), _make_access())),
        ), patch(
            "app.api.public.shared_searches.notification_service"
        ) as mock_notif, patch(
            "app.api.public.shared_searches.select",
            return_value=mock_select_result,
        ):
            mock_notif.create_notification = AsyncMock()

            await submit_feedback(
                token=ACCESS_TOKEN,
                request_data=request_data,
                db=db,
                session=_make_session(),
            )

        mock_notif.create_notification.assert_called_once()
        call_kwargs = mock_notif.create_notification.call_args.kwargs
        assert str(CREATOR_USER_ID) == call_kwargs["user_id"]
        assert REVIEWER_EMAIL in call_kwargs["message"]
        assert "shortlist_feedback" == call_kwargs["category"]
        assert call_kwargs["channels"] == ["bell"]

    @pytest.mark.asyncio
    async def test_falha_notificacao_nao_propaga(self):
        """Se notification_service lançar exceção, o feedback ainda é retornado."""
        from app.api.public.shared_searches import submit_feedback

        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.add = MagicMock()
        db.commit = AsyncMock()

        mock_feedback = MagicMock()
        mock_feedback.id = uuid4()
        mock_feedback.candidate_id = CANDIDATE_ID
        mock_feedback.reviewer_email = REVIEWER_EMAIL
        mock_feedback.decision = MagicMock(value="maybe")
        mock_feedback.rating = None
        mock_feedback.comment = None
        mock_feedback.created_at = datetime.utcnow()
        db.refresh = AsyncMock()

        request_data = MagicMock()
        request_data.candidate_id = CANDIDATE_ID
        request_data.decision = MagicMock(value="maybe")
        request_data.rating = None
        request_data.comment = None

        mock_select_result = MagicMock()
        mock_select_result.where = MagicMock(return_value=mock_select_result)
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        with patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(_make_search(), _make_access())),
        ), patch(
            "app.api.public.shared_searches.notification_service"
        ) as mock_notif, patch(
            "app.api.public.shared_searches.select",
            return_value=mock_select_result,
        ):
            mock_notif.create_notification = AsyncMock(side_effect=RuntimeError("SMTP down"))

            # Não deve lançar exceção
            result = await submit_feedback(
                token=ACCESS_TOKEN,
                request_data=request_data,
                db=db,
                session=_make_session(),
            )

        assert result is not None

    @pytest.mark.asyncio
    async def test_sem_created_by_notificacao_nao_chamada(self):
        """Se created_by_user_id for None, notificação não é chamada."""
        from app.api.public.shared_searches import submit_feedback

        search_sem_criador = _make_search()
        search_sem_criador.created_by_user_id = None

        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.add = MagicMock()
        db.commit = AsyncMock()

        mock_feedback = MagicMock()
        mock_feedback.id = uuid4()
        mock_feedback.candidate_id = CANDIDATE_ID
        mock_feedback.reviewer_email = REVIEWER_EMAIL
        mock_feedback.decision = MagicMock(value="rejected")
        mock_feedback.rating = None
        mock_feedback.comment = None
        mock_feedback.created_at = datetime.utcnow()
        db.refresh = AsyncMock()

        request_data = MagicMock()
        request_data.candidate_id = CANDIDATE_ID
        request_data.decision = MagicMock(value="rejected")
        request_data.rating = None
        request_data.comment = None

        mock_select_result = MagicMock()
        mock_select_result.where = MagicMock(return_value=mock_select_result)
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        with patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(search_sem_criador, _make_access())),
        ), patch(
            "app.api.public.shared_searches.notification_service"
        ) as mock_notif, patch(
            "app.api.public.shared_searches.select",
            return_value=mock_select_result,
        ):
            mock_notif.create_notification = AsyncMock()

            await submit_feedback(
                token=ACCESS_TOKEN,
                request_data=request_data,
                db=db,
                session=_make_session(),
            )

        mock_notif.create_notification.assert_not_called()


class TestSubmitFeedbackValidation:
    """Testa validação de sessão e candidato."""

    @pytest.mark.asyncio
    async def test_sessao_invalida_retorna_403(self):
        """Sessão com shared_search_id diferente deve retornar 403."""
        from app.api.public.shared_searches import submit_feedback
        from fastapi import HTTPException

        db = AsyncMock()
        request_data = MagicMock()
        request_data.candidate_id = CANDIDATE_ID

        sessao_errada = {
            "shared_search_id": str(uuid4()),  # ID diferente
            "email": REVIEWER_EMAIL,
        }

        with patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(_make_search(), _make_access())),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await submit_feedback(
                    token=ACCESS_TOKEN,
                    request_data=request_data,
                    db=db,
                    session=sessao_errada,
                )
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_candidato_nao_encontrado_retorna_404(self):
        """Candidato fora do snapshot retorna 404."""
        from app.api.public.shared_searches import submit_feedback
        from fastapi import HTTPException

        db = AsyncMock()
        request_data = MagicMock()
        request_data.candidate_id = uuid4()  # ID que não está no snapshot

        with patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(_make_search(), _make_access())),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await submit_feedback(
                    token=ACCESS_TOKEN,
                    request_data=request_data,
                    db=db,
                    session=_make_session(),
                )
            assert exc_info.value.status_code == 404
