"""
Tests — WSI Abandoned Service (Gap B / Passo 7A Alpha 1)

Cobre:
- check_abandoned_sessions: batch vazio
- 1º lembrete após 48h
- 2º lembrete após 96h + notificação recruiter
- Sem ação quando reminder_count >= 2
- Erro por sessão não interrompe batch
- Erro na query inicial retorna errors=1
- Task Celery registrada
- Beat schedule correto (a cada 4h)
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_session_row(
    session_id="sess-001",
    candidate_id="cand-001",
    job_vacancy_id="job-001",
    age_hours=50,
    reminder_count=0,
):
    row = MagicMock()
    row.session_id = session_id
    row.candidate_id = candidate_id
    row.job_vacancy_id = job_vacancy_id
    row.created_at = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    row.last_activity = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    row.reminder_count = reminder_count
    return row


# ── Tests ──────────────────────────────────────────────────────────────────

class TestWsiAbandonedService:
    @pytest.mark.asyncio
    async def test_batch_vazio_retorna_zeros(self):
        """Sem sessões abandonadas → result zerado."""
        from app.jobs.wsi_abandoned_service import check_abandoned_sessions

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        result = await check_abandoned_sessions(mock_db)

        assert result["first_reminders"] == 0
        assert result["second_reminders"] == 0
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_primeiro_lembrete_apos_48h(self):
        """Sessão com 50h sem atividade e reminder_count=0 → 1º lembrete."""
        from app.jobs.wsi_abandoned_service import check_abandoned_sessions

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            _make_session_row(age_hours=50, reminder_count=0)
        ]
        mock_db.execute.return_value = mock_result

        with patch("app.jobs.wsi_abandoned_service._send_candidate_reminder", new=AsyncMock()) as mock_send, \
             patch("app.jobs.wsi_abandoned_service._increment_reminder_count", new=AsyncMock()):
            result = await check_abandoned_sessions(mock_db)

        assert result["first_reminders"] == 1
        assert result["second_reminders"] == 0
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["reminder_num"] == 1

    @pytest.mark.asyncio
    async def test_segundo_lembrete_apos_96h_com_recruiter(self):
        """Sessão com 100h e reminder_count=1 → 2º lembrete + notificação recruiter."""
        from app.jobs.wsi_abandoned_service import check_abandoned_sessions

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            _make_session_row(age_hours=100, reminder_count=1)
        ]
        mock_db.execute.return_value = mock_result

        with patch("app.jobs.wsi_abandoned_service._send_candidate_reminder", new=AsyncMock()) as mock_send, \
             patch("app.jobs.wsi_abandoned_service._notify_recruiter_abandoned", new=AsyncMock()) as mock_notify, \
             patch("app.jobs.wsi_abandoned_service._increment_reminder_count", new=AsyncMock()):
            result = await check_abandoned_sessions(mock_db)

        assert result["second_reminders"] == 1
        mock_send.assert_called_once()
        mock_notify.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["reminder_num"] == 2

    @pytest.mark.asyncio
    async def test_sem_acao_quando_reminder_count_2(self):
        """reminder_count >= 2 → nenhuma ação."""
        from app.jobs.wsi_abandoned_service import check_abandoned_sessions

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            _make_session_row(age_hours=120, reminder_count=2)
        ]
        mock_db.execute.return_value = mock_result

        with patch("app.jobs.wsi_abandoned_service._send_candidate_reminder", new=AsyncMock()) as mock_send:
            result = await check_abandoned_sessions(mock_db)

        assert result["first_reminders"] == 0
        assert result["second_reminders"] == 0
        mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_erro_por_sessao_nao_interrompe_batch(self):
        """Exceção em uma sessão não interrompe o batch."""
        from app.jobs.wsi_abandoned_service import check_abandoned_sessions

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            _make_session_row(session_id="sess-001", age_hours=50, reminder_count=0),
            _make_session_row(session_id="sess-002", age_hours=50, reminder_count=0),
        ]
        mock_db.execute.return_value = mock_result

        call_count = [0]

        async def mock_send(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("erro simulado")

        with patch("app.jobs.wsi_abandoned_service._send_candidate_reminder", side_effect=mock_send), \
             patch("app.jobs.wsi_abandoned_service._increment_reminder_count", new=AsyncMock()):
            result = await check_abandoned_sessions(mock_db)

        assert result["errors"] >= 1

    @pytest.mark.asyncio
    async def test_erro_na_query_inicial_retorna_errors_1(self):
        """Erro na query principal retorna errors=1."""
        from app.jobs.wsi_abandoned_service import check_abandoned_sessions

        mock_db = AsyncMock()
        mock_db.execute.side_effect = RuntimeError("conexão perdida")

        result = await check_abandoned_sessions(mock_db)

        assert result["errors"] == 1
        assert result["first_reminders"] == 0


class TestWsiAbandonedCeleryTask:
    def test_task_registrada_no_celery(self):
        """wsi.check_abandoned deve estar registrado."""
        import app.jobs.celery_tasks  # noqa: F401 — registra tasks no Celery
        from app.core.celery_app import celery_app
        assert "wsi.check_abandoned" in celery_app.tasks

    def test_beat_schedule_wsi_abandoned(self):
        """wsi-abandoned-check deve estar no beat_schedule."""
        from lia_config.celery_app import celery_app
        assert "wsi-abandoned-check" in celery_app.conf.beat_schedule
        entry = celery_app.conf.beat_schedule["wsi-abandoned-check"]
        assert entry["task"] == "wsi.check_abandoned"
        assert entry["options"]["expires"] == 14000
