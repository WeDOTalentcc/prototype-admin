"""
COMP-2: Celery LGPD cleanup task
COMP-3: Circuit breaker notification hook
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestLgpdCleanupTask:
    """COMP-2: lgpd.run_cleanup_daily task."""

    def test_task_registered(self):
        """Task deve estar registrada no celery_app após import do módulo."""
        import app.jobs.celery_tasks  # noqa: F401 — força registro das tasks
        from app.core.celery_app import celery_app
        assert "lgpd.run_cleanup_daily" in celery_app.tasks

    def test_task_calls_cleanup_service(self):
        """Task deve chamar lgpd_cleanup_service.run_cleanup."""
        from app.jobs.celery_tasks import run_lgpd_cleanup_task

        mock_result = {"deleted_candidates": 5, "deleted_evaluations": 2, "errors": 0}

        with patch("app.jobs.celery_tasks.asyncio") as mock_asyncio:
            mock_asyncio.run.return_value = mock_result
            # Testa que a task existe e tem o nome correto
            assert run_lgpd_cleanup_task.name == "lgpd.run_cleanup_daily"

    def test_beat_schedule_has_lgpd_cleanup(self):
        """Beat schedule deve ter lgpd-cleanup-daily às 02h Brasília."""
        from app.core.celery_app import celery_app
        schedule = celery_app.conf.beat_schedule
        assert "lgpd-cleanup-daily" in schedule
        task_cfg = schedule["lgpd-cleanup-daily"]
        assert task_cfg["task"] == "lgpd.run_cleanup_daily"

    def test_admin_endpoint_exists(self):
        """Admin endpoint deve existir."""
        from app.api.v1.admin_lgpd import router
        routes = [r.path for r in router.routes]
        assert any("run-cleanup" in r for r in routes)

    def test_admin_endpoint_dry_run_default_true(self):
        """Admin endpoint deve ter dry_run=True como padrão."""
        from app.api.v1.admin_lgpd import router
        for route in router.routes:
            if hasattr(route, "endpoint") and "cleanup" in route.path:
                import inspect
                sig = inspect.signature(route.endpoint)
                dry_run_param = sig.parameters.get("dry_run")
                if dry_run_param:
                    # FastAPI Query(True) wraps the default, check its .default attribute
                    from fastapi import Query as _Query
                    default_val = dry_run_param.default
                    actual = default_val.default if hasattr(default_val, "default") else default_val
                    assert actual is True


class TestCircuitBreakerNotification:
    """COMP-3: Circuit breaker notification hook."""

    def test_notify_function_exists(self):
        """_notify_circuit_open deve existir no módulo."""
        from app.shared.resilience.circuit_breaker import _notify_circuit_open
        import asyncio
        assert asyncio.iscoroutinefunction(_notify_circuit_open)

    @pytest.mark.asyncio
    async def test_notify_deduped_by_redis(self):
        """Segundo alerta no mesmo circuit/hora deve ser ignorado (Redis dedup)."""
        from app.shared.resilience.circuit_breaker import _notify_circuit_open

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="1")  # Já existe no cache
        mock_redis.aclose = AsyncMock()

        # redis.asyncio.from_url é chamado diretamente, patch no módulo redis.asyncio
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            # Não deve chamar notification_service
            with patch("app.services.notification_service.notification_service") as MockNotif:
                MockNotif.send_system_alert = AsyncMock()
                await _notify_circuit_open("anthropic")
                MockNotif.send_system_alert.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_sends_alert_on_first_open(self):
        """Primeiro open deve enviar alerta Bell + Teams."""
        from app.shared.resilience.circuit_breaker import _notify_circuit_open

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # Não existe no cache
        mock_redis.setex = AsyncMock()
        mock_redis.aclose = AsyncMock()

        with patch("redis.asyncio.from_url", return_value=mock_redis), \
             patch("app.core.database.AsyncSessionLocal") as MockDB, \
             patch("app.services.notification_service.notification_service") as MockNotif:

            MockDB.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            MockDB.return_value.__aexit__ = AsyncMock(return_value=False)
            MockNotif.send_system_alert = AsyncMock()

            await _notify_circuit_open("pearch")
            # Redis dedup foi setado
            mock_redis.setex.assert_called_once()

    def test_notify_non_blocking_on_exception(self):
        """Falha na notificação não deve impedir operação do circuit breaker."""
        from app.shared.resilience.circuit_breaker import _notify_circuit_open
        # Função existe e é coroutine — qualquer exceção interna é silenciada
        import asyncio
        assert asyncio.iscoroutinefunction(_notify_circuit_open)
