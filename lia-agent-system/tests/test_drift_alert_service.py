"""
Testes — Drift Alert Service (E.1)

Verifica integração entre ModelDriftService e NotificationService:
- Sem drift → sem notificação
- 1 trigger → WARNING
- 2+ triggers (critical) → URGENT
- notify_user_id=None → sem notificação
- Retorna DriftStatus corretamente
- Mensagem contém nomes dos triggers disparados
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.shared.services.drift_alert_service import DriftAlertService, ALERT_CHANNELS
from app.shared.services.model_drift_service import DriftStatus, DriftTrigger
from app.services.notification_service import NotificationType, NotificationChannel

COMPANY_ID = uuid4()
USER_ID = "user-test-123"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trigger(name: str, triggered: bool) -> DriftTrigger:
    return DriftTrigger(
        name=name,
        baseline_value=50.0,
        recent_value=60.0,
        delta=0.6,
        threshold=0.5,
        triggered=triggered,
        description=f"Trigger {name}",
    )


def _make_status(triggers: list[DriftTrigger]) -> DriftStatus:
    triggered = [t for t in triggers if t.triggered]
    drift_detected = bool(triggered)
    if len(triggered) >= 2:
        alert_level = "critical"
    elif len(triggered) == 1:
        alert_level = "warning"
    else:
        alert_level = "ok"

    return DriftStatus(
        company_id=str(COMPANY_ID),
        evaluated_at=datetime.utcnow(),
        recent_window_start=datetime.utcnow() - timedelta(days=7),
        baseline_window_start=datetime.utcnow() - timedelta(days=14),
        triggers=triggers,
        drift_detected=drift_detected,
        alert_level=alert_level,
    )


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

class TestDriftAlertService:

    @pytest.mark.asyncio
    async def test_no_alert_when_no_drift(self):
        """Sem drift → send_multi_channel_notification NÃO deve ser chamado."""
        status = _make_status([_make_trigger("score_drift", triggered=False)])

        with patch(
            "app.services.drift_alert_service.model_drift_service.evaluate",
            new=AsyncMock(return_value=status),
        ), patch(
            "app.services.drift_alert_service.notification_service.send_multi_channel_notification",
            new=AsyncMock(),
        ) as mock_notify:
            svc = DriftAlertService()
            result = await svc.evaluate_and_alert(MagicMock(), COMPANY_ID, USER_ID)

        mock_notify.assert_not_called()
        assert result.drift_detected is False

    @pytest.mark.asyncio
    async def test_warning_alert_on_single_trigger(self):
        """1 trigger disparado → notificação WARNING."""
        status = _make_status([_make_trigger("score_drift", triggered=True)])

        with patch(
            "app.services.drift_alert_service.model_drift_service.evaluate",
            new=AsyncMock(return_value=status),
        ), patch(
            "app.services.drift_alert_service.notification_service.send_multi_channel_notification",
            new=AsyncMock(),
        ) as mock_notify:
            svc = DriftAlertService()
            await svc.evaluate_and_alert(MagicMock(), COMPANY_ID, USER_ID)

        mock_notify.assert_awaited_once()
        call_kwargs = mock_notify.call_args.kwargs
        assert call_kwargs["notification_type"] == NotificationType.WARNING

    @pytest.mark.asyncio
    async def test_urgent_alert_on_critical(self):
        """2+ triggers disparados (critical) → notificação URGENT."""
        status = _make_status([
            _make_trigger("score_drift", triggered=True),
            _make_trigger("approval_drift", triggered=True),
        ])

        with patch(
            "app.services.drift_alert_service.model_drift_service.evaluate",
            new=AsyncMock(return_value=status),
        ), patch(
            "app.services.drift_alert_service.notification_service.send_multi_channel_notification",
            new=AsyncMock(),
        ) as mock_notify:
            svc = DriftAlertService()
            await svc.evaluate_and_alert(MagicMock(), COMPANY_ID, USER_ID)

        call_kwargs = mock_notify.call_args.kwargs
        assert call_kwargs["notification_type"] == NotificationType.URGENT
        assert status.alert_level == "critical"

    @pytest.mark.asyncio
    async def test_no_alert_when_notify_user_id_none(self):
        """Drift detectado mas notify_user_id=None → sem notificação."""
        status = _make_status([_make_trigger("cost_drift", triggered=True)])

        with patch(
            "app.services.drift_alert_service.model_drift_service.evaluate",
            new=AsyncMock(return_value=status),
        ), patch(
            "app.services.drift_alert_service.notification_service.send_multi_channel_notification",
            new=AsyncMock(),
        ) as mock_notify:
            svc = DriftAlertService()
            result = await svc.evaluate_and_alert(MagicMock(), COMPANY_ID, notify_user_id=None)

        mock_notify.assert_not_called()
        assert result.drift_detected is True

    @pytest.mark.asyncio
    async def test_returns_drift_status(self):
        """Método deve retornar o DriftStatus recebido do model_drift_service."""
        status = _make_status([_make_trigger("latency_drift", triggered=True)])

        with patch(
            "app.services.drift_alert_service.model_drift_service.evaluate",
            new=AsyncMock(return_value=status),
        ), patch(
            "app.services.drift_alert_service.notification_service.send_multi_channel_notification",
            new=AsyncMock(),
        ):
            svc = DriftAlertService()
            result = await svc.evaluate_and_alert(MagicMock(), COMPANY_ID, USER_ID)

        assert result is status
        assert result.company_id == str(COMPANY_ID)

    @pytest.mark.asyncio
    async def test_alert_includes_trigger_names(self):
        """Mensagem da notificação deve conter o nome do trigger disparado."""
        status = _make_status([_make_trigger("cost_drift", triggered=True)])

        with patch(
            "app.services.drift_alert_service.model_drift_service.evaluate",
            new=AsyncMock(return_value=status),
        ), patch(
            "app.services.drift_alert_service.notification_service.send_multi_channel_notification",
            new=AsyncMock(),
        ) as mock_notify:
            svc = DriftAlertService()
            await svc.evaluate_and_alert(MagicMock(), COMPANY_ID, USER_ID)

        call_kwargs = mock_notify.call_args.kwargs
        assert "cost_drift" in call_kwargs["message"]
        assert call_kwargs["channels"] == ALERT_CHANNELS
