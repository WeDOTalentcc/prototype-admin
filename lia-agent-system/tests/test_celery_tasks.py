"""
Testes unitários para celery_tasks.py (G.1).

Cobrem:
- Nome da task registrada
- Retorno do resultado do job
- Repasse do notify_user_id
- Retry automático em caso de exceção
- max_retries configurado

Estratégia: mockar run_drift_check_all_companies e AsyncSessionLocal
para evitar conexão real com DB e Celery broker.
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.jobs.celery_tasks import run_drift_batch_task


class TestRunDriftBatchTask:
    """Testes unitários para a Celery task drift.run_batch."""

    def test_task_name_is_drift_run_batch(self):
        """Task deve ser registrada com nome 'drift.run_batch'."""
        assert run_drift_batch_task.name == "drift.run_batch"

    def test_max_retries_is_3(self):
        """max_retries deve ser 3."""
        assert run_drift_batch_task.max_retries == 3

    def _make_session_mock(self):
        """Cria mock de sessão assíncrona reutilizável."""
        mock_session = AsyncMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        return mock_cm

    def test_run_returns_dict_from_job(self):
        """Task deve retornar o dict retornado por run_drift_check_all_companies."""
        expected = {"checked": 5, "drifted": 1, "errors": 0}

        async def _mock_run_drift(db, notify_user_id):
            return expected

        # bind=True: self é injetado pelo Celery — chamar sem mock_ctx
        with patch(
            "app.jobs.drift_job.run_drift_check_all_companies",
            new=_mock_run_drift,
        ), patch(
            "app.core.database.AsyncSessionLocal",
            return_value=self._make_session_mock(),
        ):
            result = run_drift_batch_task()

        assert result == expected

    def test_run_passes_notify_user_id(self):
        """notify_user_id deve ser repassado ao run_drift_check_all_companies."""
        captured = {}

        async def _mock_run_drift(db, notify_user_id):
            captured["notify_user_id"] = notify_user_id
            return {"checked": 1, "drifted": 0, "errors": 0}

        with patch(
            "app.jobs.drift_job.run_drift_check_all_companies",
            new=_mock_run_drift,
        ), patch(
            "app.core.database.AsyncSessionLocal",
            return_value=self._make_session_mock(),
        ):
            run_drift_batch_task(notify_user_id="user-42")

        assert captured["notify_user_id"] == "user-42"

    def test_retries_on_exception(self):
        """Em caso de exceção, self.retry() deve ser chamado com countdown=60."""
        async def _failing_run_drift(db, notify_user_id):
            raise RuntimeError("DB indisponível")

        # Monkeypatchar retry diretamente na task object (self é a task)
        with patch.object(
            run_drift_batch_task, "retry", side_effect=Exception("retry chamado")
        ) as mock_retry, patch(
            "app.jobs.drift_job.run_drift_check_all_companies",
            new=_failing_run_drift,
        ), patch(
            "app.core.database.AsyncSessionLocal",
            return_value=self._make_session_mock(),
        ):
            with pytest.raises(Exception, match="retry chamado"):
                run_drift_batch_task()

        mock_retry.assert_called_once()
        call_kwargs = mock_retry.call_args
        assert call_kwargs.kwargs.get("countdown") == 60
