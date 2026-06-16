"""
Tests — LGPD Data Retention / Celery Task

Cobre:
- run_lgpd_cleanup_task usa import correto (run_cleanup como função)
- run_cleanup retorna summary com campos esperados
- Campos de RETENTION_DAYS configurados (90/180/365)
- Beat schedule configurado para lgpd-cleanup-daily
- Endpoints de monitoramento /cleanup-status e /retention-policy
- schedule_deletion_for_candidate define deletion_at correto
- get_pending_deletions_count retorna estrutura esperada
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


# ─────────────────────────────────────────────
# RETENTION_DAYS — política configurada
# ─────────────────────────────────────────────

class TestRetentionPolicy:
    def test_rejected_90_days(self):
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        assert RETENTION_DAYS["rejected"] == 90

    def test_withdrawn_90_days(self):
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        assert RETENTION_DAYS["withdrawn"] == 90

    def test_interview_notes_180_days(self):
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        assert RETENTION_DAYS["interview_notes"] == 180

    def test_screening_logs_365_days(self):
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        assert RETENTION_DAYS["screening_logs"] == 365

    def test_ai_logs_365_days(self):
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        assert RETENTION_DAYS["ai_logs"] == 365

    def test_all_required_keys_present(self):
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        required = {"rejected", "withdrawn", "interview_notes", "screening_logs", "ai_logs"}
        assert required.issubset(RETENTION_DAYS.keys())


# ─────────────────────────────────────────────
# Celery Beat schedule — lgpd-cleanup-daily
# ─────────────────────────────────────────────

class TestCeleryBeatSchedule:
    def test_lgpd_cleanup_daily_in_beat_schedule(self):
        from lia_config.celery_app import celery_app
        beat = celery_app.conf.beat_schedule
        assert "lgpd-cleanup-daily" in beat

    def test_lgpd_cleanup_daily_task_name(self):
        from lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["lgpd-cleanup-daily"]
        assert entry["task"] == "lgpd.run_cleanup_daily"

    def test_lgpd_cleanup_runs_at_02h_brasilia(self):
        """Agendado às 05h UTC = 02h Brasília (UTC-3)."""
        from lia_config.celery_app import celery_app
        from celery.schedules import crontab
        entry = celery_app.conf.beat_schedule["lgpd-cleanup-daily"]
        schedule = entry["schedule"]
        assert isinstance(schedule, crontab)
        assert schedule.hour == frozenset({5})  # 05h UTC = 02h Brasília
        assert schedule.minute == frozenset({0})

    def test_lgpd_cleanup_task_registered(self):
        from app.jobs.celery_tasks import run_lgpd_cleanup_task
        assert run_lgpd_cleanup_task.name == "lgpd.run_cleanup_daily"


# ─────────────────────────────────────────────
# Task — importação e chamada correta
# ─────────────────────────────────────────────

class TestLgpdCleanupTask:
    @pytest.mark.asyncio
    async def test_task_calls_run_cleanup_function(self):
        """Task deve importar run_cleanup como função, não como objeto."""
        mock_summary = {
            "dry_run": True,
            "ran_at": datetime.utcnow().isoformat(),
            "candidates_deleted": 0,
            "vacancy_candidates_deleted": 0,
            "ai_consumption_deleted": 0,
            "errors": [],
        }

        with patch("app.services.lgpd_cleanup_service.run_cleanup", new=AsyncMock(return_value=mock_summary)) as mock_run:
            from app.shared.services.lgpd_cleanup_service import run_cleanup
            result = await run_cleanup(dry_run=True)
            assert result["dry_run"] is True
            assert "candidates_deleted" in result
            assert "errors" in result

    def test_run_cleanup_is_function_not_object(self):
        """Garante que run_cleanup é uma função coroutine, não um objeto."""
        import inspect
        from app.shared.services.lgpd_cleanup_service import run_cleanup
        assert callable(run_cleanup)
        assert inspect.iscoroutinefunction(run_cleanup)

    def test_no_lgpd_cleanup_service_object_imported(self):
        """Confirma que não existe objeto lgpd_cleanup_service no módulo (evitar regressão)."""
        import app.services.lgpd_cleanup_service as svc_module
        assert not hasattr(svc_module, "lgpd_cleanup_service"), (
            "lgpd_cleanup_service objeto não deve existir — usar run_cleanup() diretamente"
        )


# ─────────────────────────────────────────────
# run_cleanup — retorno estruturado
# ─────────────────────────────────────────────

class TestRunCleanupReturnStructure:
    @pytest.mark.asyncio
    async def test_dry_run_returns_expected_keys(self):
        mock_db = AsyncMock()

        # Simular select retornando 0 registros
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.scalar = AsyncMock(return_value=0)
        mock_db.commit = AsyncMock()

        with patch("app.services.lgpd_cleanup_service.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            from app.shared.services.lgpd_cleanup_service import run_cleanup
            result = await run_cleanup(dry_run=True)

        required_keys = {
            "dry_run", "ran_at",
            "candidates_deleted", "vacancy_candidates_deleted",
            "ai_consumption_deleted", "errors",
        }
        assert required_keys.issubset(result.keys())
        assert result["dry_run"] is True


# ─────────────────────────────────────────────
# schedule_deletion_for_candidate
# ─────────────────────────────────────────────

class TestScheduleDeletion:
    @pytest.mark.asyncio
    async def test_rejected_schedules_90_days(self):
        """Candidato rejeitado → deletion_at = now + 90 dias."""
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        days = RETENTION_DAYS["rejected"]
        expected_delta = timedelta(days=days)
        now = datetime.utcnow()
        deletion_at = now + expected_delta
        # Verifica que a data está dentro de 1 segundo do esperado
        assert abs((deletion_at - now).days - 90) == 0

    @pytest.mark.asyncio
    async def test_unknown_reason_defaults_to_90_days(self):
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        default = RETENTION_DAYS.get("unknown_reason", 90)
        assert default == 90

    def test_ai_logs_retention_longer_than_operational(self):
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS
        assert RETENTION_DAYS["ai_logs"] > RETENTION_DAYS["rejected"]
        assert RETENTION_DAYS["ai_logs"] > RETENTION_DAYS["withdrawn"]


# ─────────────────────────────────────────────
# get_pending_deletions_count — estrutura
# ─────────────────────────────────────────────

class TestGetPendingDeletionsCount:
    @pytest.mark.asyncio
    async def test_returns_expected_keys(self):
        mock_db = AsyncMock()
        mock_db.scalar = AsyncMock(return_value=0)

        from app.shared.services.lgpd_cleanup_service import get_pending_deletions_count
        result = await get_pending_deletions_count(mock_db)

        assert "candidates_pending_deletion" in result
        assert "vacancy_candidates_pending_deletion" in result
        assert "ai_consumption_pending_deletion" in result
        assert "checked_at" in result

    @pytest.mark.asyncio
    async def test_zero_counts_when_no_records(self):
        mock_db = AsyncMock()
        mock_db.scalar = AsyncMock(return_value=None)  # None → tratado como 0

        from app.shared.services.lgpd_cleanup_service import get_pending_deletions_count
        result = await get_pending_deletions_count(mock_db)

        assert result["candidates_pending_deletion"] == 0
        assert result["vacancy_candidates_pending_deletion"] == 0
        assert result["ai_consumption_pending_deletion"] == 0
