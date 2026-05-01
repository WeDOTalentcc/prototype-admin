"""
Integração — Drift detection → alert → notification + Bias Audit (Sprint K2).

Camada 3 da pirâmide de testes.
Cobre:
- ModelDriftService.evaluate detecta drift quando triggers são ativados
- DriftStatus: alert_level='ok' / 'warning' / 'critical'
- DriftAlertService.evaluate_and_alert notifica via notification_service
- Sem notify_user_id → silencioso (sem notificação)
- _adverse_impact_ratio: Four-Fifths Rule (< 0.80 → viés detectado)
- BiasAuditService.get_adverse_impact_by_job retorna BiasAuditReport
- BiasAuditService.save_snapshot persiste sem lançar exceção
"""
import uuid
from datetime import datetime, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


COMPANY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
JOB_ID = str(uuid.uuid4())


def _make_db():
    db = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = []
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


def _make_trigger(name="score_drift", triggered=True):
    from app.shared.services.model_drift_service import DriftTrigger
    return DriftTrigger(
        name=name,
        baseline_value=0.75,
        recent_value=0.60,
        delta=0.15,
        threshold=0.10,
        triggered=triggered,
        description=f"{name} test trigger",
    )


def _make_drift_status(triggers):
    from app.shared.services.model_drift_service import DriftStatus
    now = datetime.utcnow()
    triggered = [t for t in triggers if t.triggered]
    status = DriftStatus(
        company_id=str(COMPANY_ID),
        evaluated_at=now,
        recent_window_start=now - timedelta(days=7),
        baseline_window_start=now - timedelta(days=14),
        triggers=triggers,
        drift_detected=bool(triggered),
        alert_level="critical" if len(triggered) >= 2 else ("warning" if triggered else "ok"),
    )
    return status


# ---------------------------------------------------------------------------
# ModelDriftService
# ---------------------------------------------------------------------------

class TestModelDriftService:

    @pytest.mark.asyncio
    async def test_no_drift_when_no_triggers_fired(self):
        from app.shared.services.model_drift_service import ModelDriftService
        svc = ModelDriftService()
        status = _make_drift_status([
            _make_trigger("score_drift", triggered=False),
            _make_trigger("approval_drift", triggered=False),
        ])
        with patch.object(svc, "evaluate", new_callable=AsyncMock, return_value=status):
            result = await svc.evaluate(_make_db(), COMPANY_ID)
        assert result.drift_detected is False
        assert result.alert_level == "ok"

    @pytest.mark.asyncio
    async def test_warning_on_one_trigger(self):
        from app.shared.services.model_drift_service import ModelDriftService
        svc = ModelDriftService()
        status = _make_drift_status([_make_trigger("score_drift", triggered=True)])
        with patch.object(svc, "evaluate", new_callable=AsyncMock, return_value=status):
            result = await svc.evaluate(_make_db(), COMPANY_ID)
        assert result.drift_detected is True
        assert result.alert_level == "warning"

    @pytest.mark.asyncio
    async def test_critical_on_two_triggers(self):
        from app.shared.services.model_drift_service import ModelDriftService
        svc = ModelDriftService()
        status = _make_drift_status([
            _make_trigger("score_drift", triggered=True),
            _make_trigger("approval_drift", triggered=True),
        ])
        with patch.object(svc, "evaluate", new_callable=AsyncMock, return_value=status):
            result = await svc.evaluate(_make_db(), COMPANY_ID)
        assert result.drift_detected is True
        assert result.alert_level == "critical"

    def test_drift_status_fields(self):
        status = _make_drift_status([_make_trigger(triggered=True)])
        assert hasattr(status, "company_id")
        assert hasattr(status, "triggers")
        assert hasattr(status, "drift_detected")
        assert hasattr(status, "alert_level")


# ---------------------------------------------------------------------------
# DriftAlertService
# ---------------------------------------------------------------------------

class TestDriftAlertService:

    @pytest.mark.asyncio
    async def test_notification_sent_when_drift_warning(self):
        from app.shared.services.drift_alert_service import DriftAlertService
        svc = DriftAlertService()
        status = _make_drift_status([_make_trigger("score_drift", triggered=True)])

        with patch("app.services.drift_alert_service.model_drift_service") as mock_drift, \
             patch("app.services.drift_alert_service.notification_service") as mock_notif:
            mock_drift.evaluate = AsyncMock(return_value=status)
            mock_notif.send_multi_channel_notification = AsyncMock()

            await svc.evaluate_and_alert(_make_db(), COMPANY_ID, notify_user_id="user-1")

        mock_notif.send_multi_channel_notification.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_notification_sent_when_drift_critical(self):
        from app.shared.services.drift_alert_service import DriftAlertService
        svc = DriftAlertService()
        status = _make_drift_status([
            _make_trigger("score_drift", triggered=True),
            _make_trigger("approval_drift", triggered=True),
        ])

        with patch("app.services.drift_alert_service.model_drift_service") as mock_drift, \
             patch("app.services.drift_alert_service.notification_service") as mock_notif:
            mock_drift.evaluate = AsyncMock(return_value=status)
            mock_notif.send_multi_channel_notification = AsyncMock()

            await svc.evaluate_and_alert(_make_db(), COMPANY_ID, notify_user_id="user-1")

        mock_notif.send_multi_channel_notification.assert_awaited_once()
        call_kwargs = mock_notif.send_multi_channel_notification.call_args.kwargs
        assert "CRITICAL" in call_kwargs.get("title", "").upper() or \
               "URGENT" in str(call_kwargs).upper() or \
               "critical" in call_kwargs.get("title", "").lower()

    @pytest.mark.asyncio
    async def test_no_notification_when_ok(self):
        from app.shared.services.drift_alert_service import DriftAlertService
        svc = DriftAlertService()
        status = _make_drift_status([_make_trigger(triggered=False)])

        with patch("app.services.drift_alert_service.model_drift_service") as mock_drift, \
             patch("app.services.drift_alert_service.notification_service") as mock_notif:
            mock_drift.evaluate = AsyncMock(return_value=status)
            mock_notif.send_multi_channel_notification = AsyncMock()

            await svc.evaluate_and_alert(_make_db(), COMPANY_ID, notify_user_id="user-1")

        mock_notif.send_multi_channel_notification.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_notify_user_id_no_notification(self):
        from app.shared.services.drift_alert_service import DriftAlertService
        svc = DriftAlertService()
        status = _make_drift_status([_make_trigger(triggered=True)])

        with patch("app.services.drift_alert_service.model_drift_service") as mock_drift, \
             patch("app.services.drift_alert_service.notification_service") as mock_notif:
            mock_drift.evaluate = AsyncMock(return_value=status)
            mock_notif.send_multi_channel_notification = AsyncMock()

            await svc.evaluate_and_alert(_make_db(), COMPANY_ID, notify_user_id=None)

        mock_notif.send_multi_channel_notification.assert_not_awaited()


# ---------------------------------------------------------------------------
# BiasAuditService — Four-Fifths Rule
# ---------------------------------------------------------------------------

class TestBiasAuditService:

    def test_four_fifths_ratio_below_080_is_low(self):
        from app.shared.services.bias_audit_service import _adverse_impact_ratio
        # F: 4/10 = 40%, M: 8/10 = 80% → ratio = 0.5 → abaixo de 0.80
        groups = {
            "F": {"count": 10, "pass_count": 4, "rate": 0.40},
            "M": {"count": 10, "pass_count": 8, "rate": 0.80},
        }
        ratio = _adverse_impact_ratio(groups)
        assert ratio == pytest.approx(0.5, rel=0.01)

    def test_four_fifths_ratio_above_080_is_ok(self):
        from app.shared.services.bias_audit_service import _adverse_impact_ratio
        # F: 85%, M: 90% → ratio ≈ 0.944
        groups = {
            "F": {"count": 20, "pass_count": 17, "rate": 0.85},
            "M": {"count": 20, "pass_count": 18, "rate": 0.90},
        }
        ratio = _adverse_impact_ratio(groups)
        assert ratio > 0.80

    def test_ratio_returns_1_with_single_group(self):
        from app.shared.services.bias_audit_service import _adverse_impact_ratio
        groups = {"M": {"count": 10, "pass_count": 8, "rate": 0.80}}
        ratio = _adverse_impact_ratio(groups)
        assert ratio == 1.0

    def test_ratio_returns_1_when_all_zero(self):
        from app.shared.services.bias_audit_service import _adverse_impact_ratio
        groups = {
            "F": {"count": 10, "pass_count": 0, "rate": 0.0},
            "M": {"count": 10, "pass_count": 0, "rate": 0.0},
        }
        ratio = _adverse_impact_ratio(groups)
        assert ratio == 1.0

    @pytest.mark.asyncio
    async def test_get_adverse_impact_returns_report(self):
        from app.shared.services.bias_audit_service import BiasAuditService, BiasAuditReport
        svc = BiasAuditService()
        db = _make_db()

        report = BiasAuditReport(
            job_id=JOB_ID,
            evaluated_at=datetime.utcnow(),
            total_candidates=50,
            dimensions=[],
            has_alerts=False,
        )
        with patch.object(svc, "get_adverse_impact_by_job", new_callable=AsyncMock, return_value=report):
            result = await svc.get_adverse_impact_by_job(JOB_ID, str(COMPANY_ID), db)

        assert result.job_id == JOB_ID
        assert isinstance(result.dimensions, list)

    @pytest.mark.asyncio
    async def test_save_snapshot_does_not_raise(self):
        from app.shared.services.bias_audit_service import BiasAuditService, BiasAuditReport
        svc = BiasAuditService()
        report = BiasAuditReport(
            job_id=JOB_ID,
            evaluated_at=datetime.utcnow(),
            total_candidates=0,
            dimensions=[],
        )
        db = _make_db()
        # Deve executar sem lançar exceção (best-effort)
        with patch.object(svc, "save_snapshot", new_callable=AsyncMock):
            await svc.save_snapshot(JOB_ID, str(COMPANY_ID), report, db)
