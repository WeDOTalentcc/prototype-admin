"""
Tests — Follow-up Service (Gap A / Passo 6B Alpha 1)

Cobre:
- process_email_followups: batch vazio
- Reenvio de notificação não aberta
- Skip de opt-out
- Skip quando followup_count >= MAX_FOLLOWUPS
- Marcar sem_resposta após MAX_FOLLOWUPS
- Erro por candidato não interrompe batch
- Task Celery registrada
- Beat schedule correto
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_row(
    notification_id="notif-001",
    user_id="user-001",
    candidate_id="cand-001",
    job_id="job-001",
    extra_data=None,
    created_at=None,
):
    from datetime import datetime, timezone, timedelta
    row = MagicMock()
    row.notification_id = notification_id
    row.user_id = user_id
    row.candidate_id = candidate_id
    row.job_id = job_id
    row.extra_data = extra_data or {}
    row.sent_at = created_at or (datetime.now(timezone.utc) - timedelta(hours=25))
    return row


# ── Tests ──────────────────────────────────────────────────────────────────

class TestFollowupService:
    @pytest.mark.asyncio
    async def test_batch_vazio_retorna_zeros(self):
        """Sem notificações pendentes → result zerado."""
        from app.jobs.followup_service import process_email_followups

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        result = await process_email_followups(mock_db)

        assert result["sent"] == 0
        assert result["skipped"] == 0
        assert result["errors"] == 0
        assert result["marked_no_response"] == 0

    @pytest.mark.asyncio
    async def test_reenvia_notificacao_nao_aberta(self):
        """Notificação não aberta → reenvio + incremento followup_count."""
        from app.jobs.followup_service import process_email_followups

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [_make_row(extra_data={"followup_count": 0})]
        mock_db.execute.return_value = mock_result

        with patch("app.services.notification_service.notification_service") as mock_ns:
            mock_ns.create_notification = AsyncMock()
            result = await process_email_followups(mock_db)

        assert result["sent"] == 1
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_skip_opted_out(self):
        """Candidato com opted_out=True é ignorado."""
        from app.jobs.followup_service import process_email_followups

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            _make_row(extra_data={"followup_count": 1, "opted_out": True})
        ]
        mock_db.execute.return_value = mock_result

        result = await process_email_followups(mock_db)

        assert result["sent"] == 0
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_skip_quando_max_followups_atingido(self):
        """followup_count >= MAX_FOLLOWUPS → marca sem_resposta, não reenvia."""
        from app.jobs.followup_service import process_email_followups, MAX_FOLLOWUPS

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            _make_row(extra_data={"followup_count": MAX_FOLLOWUPS})
        ]
        mock_db.execute.return_value = mock_result

        with patch("app.jobs.followup_service._mark_no_response", new=AsyncMock()) as mock_mark:
            result = await process_email_followups(mock_db)

        assert result["marked_no_response"] == 1
        assert result["skipped"] == 1
        assert result["sent"] == 0
        mock_mark.assert_called_once()

    @pytest.mark.asyncio
    async def test_erro_por_candidato_nao_interrompe_batch(self):
        """Exceção em um candidato não interrompe o batch."""
        from app.jobs.followup_service import process_email_followups

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            _make_row(notification_id="notif-001", extra_data={"followup_count": 0}),
            _make_row(notification_id="notif-002", extra_data={"followup_count": 0}),
        ]
        # Segundo execute (UPDATE) lança exceção no primeiro candidato
        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise RuntimeError("DB error simulado")
            return mock_result

        mock_db.execute.side_effect = side_effect

        result = await process_email_followups(mock_db)

        assert result["errors"] >= 1

    @pytest.mark.asyncio
    async def test_erro_na_query_inicial_retorna_errors_1(self):
        """Erro na query principal retorna errors=1."""
        from app.jobs.followup_service import process_email_followups

        mock_db = AsyncMock()
        mock_db.execute.side_effect = RuntimeError("conexão perdida")

        result = await process_email_followups(mock_db)

        assert result["errors"] == 1
        assert result["sent"] == 0


class TestFollowupCeleryTask:
    def test_task_registrada_no_celery(self):
        """followup.process_pending deve estar registrado."""
        import app.jobs.celery_tasks  # noqa: F401 — registra tasks no Celery
        from app.core.celery_app import celery_app
        assert "followup.process_pending" in celery_app.tasks

    def test_beat_schedule_followup_check(self):
        """followup-check-hourly deve estar no beat_schedule."""
        from lia_config.celery_app import celery_app
        assert "followup-check-hourly" in celery_app.conf.beat_schedule
        entry = celery_app.conf.beat_schedule["followup-check-hourly"]
        assert entry["task"] == "followup.process_pending"
        assert entry["options"]["expires"] == 3500

    def test_beat_schedule_followup_executa_todo_hora(self):
        """followup-check-hourly deve rodar a cada hora (minute=0)."""
        from lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["followup-check-hourly"]
        assert 0 in entry["schedule"].minute
