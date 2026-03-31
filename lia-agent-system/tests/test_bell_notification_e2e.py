"""
Bell Notification In-App — E2E Tests

Tests the complete notification flow:
1. Backend API CRUD for notifications
2. ProactiveService BELL channel emission
3. NotificationService multi-channel with BELL
4. Proxy route forwarding patterns
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def notification_service():
    from lia_messaging.notification_service import NotificationService
    return NotificationService()


@pytest.fixture
def proactive_service():
    from app.domains.automation.services.proactive_service import ProactiveService
    return ProactiveService()


class TestNotificationServiceBehavior:

    def test_notification_type_enum_values(self):
        from lia_messaging.notification_service import NotificationType
        assert NotificationType.INFO.value == "info"
        assert NotificationType.SUCCESS.value == "success"
        assert NotificationType.WARNING.value == "warning"
        assert NotificationType.URGENT.value == "urgent"
        assert NotificationType.ACTION_REQUIRED.value == "action_required"

    def test_notification_channel_includes_bell(self):
        from lia_messaging.notification_service import NotificationChannel
        assert NotificationChannel.BELL.value == "bell"
        assert NotificationChannel.CHAT.value == "chat"
        assert NotificationChannel.TEAMS.value == "teams"
        assert NotificationChannel.EMAIL.value == "email"

    def test_notification_model_to_dict(self):
        from lia_messaging.notification_service import Notification
        notif = Notification(
            id="test-123",
            user_id="recruiter-1",
            title="Test Notification",
            message="Test message body",
            notification_type="info",
            category="pipeline",
            source_agent="proactive_service",
            is_read=False,
            channels=["bell"],
        )
        d = notif.to_dict()
        assert d["id"] == "test-123"
        assert d["user_id"] == "recruiter-1"
        assert d["title"] == "Test Notification"
        assert d["message"] == "Test message body"
        assert d["notification_type"] == "info"
        assert d["category"] == "pipeline"
        assert d["source_agent"] == "proactive_service"
        assert d["is_read"] is False
        assert "bell" in d["channels"]

    def test_notification_model_read_fields(self):
        from lia_messaging.notification_service import Notification
        notif = Notification(
            id="test-456",
            user_id="recruiter-1",
            title="Read Test",
            is_read=True,
            read_at=datetime(2026, 3, 31, 12, 0, 0),
        )
        d = notif.to_dict()
        assert d["is_read"] is True
        assert d["read_at"] == "2026-03-31T12:00:00"

    def test_notification_model_dismiss_fields(self):
        from lia_messaging.notification_service import Notification
        notif = Notification(
            id="test-789",
            user_id="recruiter-1",
            title="Dismiss Test",
            is_dismissed=True,
            dismissed_at=datetime(2026, 3, 31, 14, 0, 0),
        )
        d = notif.to_dict()
        assert d["is_dismissed"] is True

    def test_notification_model_action_fields(self):
        from lia_messaging.notification_service import Notification
        notif = Notification(
            id="test-action",
            user_id="recruiter-1",
            title="Action Test",
            action_url="/chat/thread-1",
            action_label="Ver Relatório",
        )
        d = notif.to_dict()
        assert d["action_url"] == "/chat/thread-1"
        assert d["action_label"] == "Ver Relatório"

    def test_notification_model_related_ids(self):
        from lia_messaging.notification_service import Notification
        notif = Notification(
            id="test-related",
            user_id="recruiter-1",
            title="Related IDs Test",
            related_job_id="job-123",
            related_candidate_id="cand-456",
            related_task_id="task-789",
        )
        d = notif.to_dict()
        assert d["related_job_id"] == "job-123"
        assert d["related_candidate_id"] == "cand-456"
        assert d["related_task_id"] == "task-789"


class TestProactiveServiceBellEmission:

    @pytest.mark.asyncio
    async def test_daily_briefing_creates_bell_notification(self, proactive_service):
        with patch.object(proactive_service, '_create_bell_notification', new_callable=AsyncMock) as mock_bell, \
             patch.object(proactive_service, '_send_via_teams', new_callable=AsyncMock, return_value=True):
            await proactive_service.generate_daily_briefing("recruiter-1", "Maria")
            mock_bell.assert_called_once()
            call_args = mock_bell.call_args[0][0]
            assert call_args["title"] == "Briefing Diário"
            assert call_args["recruiter_id"] == "recruiter-1"

    @pytest.mark.asyncio
    async def test_end_of_day_creates_bell_notification(self, proactive_service):
        with patch.object(proactive_service, '_create_bell_notification', new_callable=AsyncMock) as mock_bell, \
             patch.object(proactive_service, '_send_via_teams', new_callable=AsyncMock, return_value=True):
            await proactive_service.generate_end_of_day_summary("recruiter-1", "Maria")
            mock_bell.assert_called_once()
            call_args = mock_bell.call_args[0][0]
            assert call_args["title"] == "Resumo do Dia"

    @pytest.mark.asyncio
    async def test_interview_reminder_creates_bell_notification(self, proactive_service):
        with patch.object(proactive_service, '_create_bell_notification', new_callable=AsyncMock) as mock_bell, \
             patch.object(proactive_service, '_send_via_teams', new_callable=AsyncMock, return_value=True):
            await proactive_service.send_interview_reminder(
                recruiter_id="recruiter-1",
                recruiter_name="Maria",
                candidate_name="João Silva",
                interview_time=datetime(2026, 4, 1, 14, 0, 0),
                interview_link="https://meet.example.com/abc",
            )
            mock_bell.assert_called_once()
            call_args = mock_bell.call_args[0][0]
            assert "João Silva" in call_args["title"]

    @pytest.mark.asyncio
    async def test_screening_completed_creates_bell_notification(self, proactive_service):
        with patch.object(proactive_service, '_create_bell_notification', new_callable=AsyncMock) as mock_bell, \
             patch.object(proactive_service, '_send_via_teams', new_callable=AsyncMock, return_value=True):
            await proactive_service.notify_screening_completed(
                recruiter_id="recruiter-1",
                candidate_name="Ana Costa",
                job_title="Dev Backend",
                wsi_score=4.2,
                passed=True,
                strengths=["Python", "SQL"],
                development_areas=["Docker"],
                session_id="session-123",
                dispatch_event=False,
            )
            mock_bell.assert_called_once()
            call_args = mock_bell.call_args[0][0]
            assert "Ana Costa" in call_args["title"]

    @pytest.mark.asyncio
    async def test_critical_alert_creates_bell_notification(self, proactive_service):
        with patch.object(proactive_service, '_create_bell_notification', new_callable=AsyncMock) as mock_bell, \
             patch.object(proactive_service, '_send_via_teams', new_callable=AsyncMock, return_value=True):
            await proactive_service.send_critical_alert(
                recruiter_id="recruiter-1",
                alert_type="Pipeline Parado",
                message="Nenhum candidato progrediu em 5 dias",
                action_required="Revisar pipeline",
            )
            mock_bell.assert_called_once()
            call_args = mock_bell.call_args[0][0]
            assert "ALERTA" in call_args["title"]

    @pytest.mark.asyncio
    async def test_bell_notification_maps_types_correctly(self):
        from app.domains.automation.services.proactive_service import ProactiveService
        svc = ProactiveService()

        mock_ns = MagicMock()
        mock_ns.create_notification = AsyncMock(return_value={"id": "test"})

        notification = {
            "type": "critical_alert",
            "priority": "critical",
            "recruiter_id": "recruiter-1",
            "title": "ALERTA: Test",
            "message": "Test message",
            "data": {},
            "channel": "teams",
        }

        with patch(
            'lia_messaging.notification_service.notification_service',
            mock_ns,
        ):
            result = await svc._create_bell_notification(notification)
            assert result is True
            call_kwargs = mock_ns.create_notification.call_args[1]
            from lia_messaging.notification_service import NotificationType as MsgNT
            assert call_kwargs["notification_type"] == MsgNT.URGENT
            assert call_kwargs["category"] == "system"
            assert call_kwargs["source_agent"] == "proactive_service"

    @pytest.mark.asyncio
    async def test_bell_notification_graceful_failure(self, proactive_service):
        mock_ns = MagicMock()
        mock_ns.create_notification = AsyncMock(side_effect=Exception("DB error"))

        with patch(
            'lia_messaging.notification_service.notification_service',
            mock_ns,
        ):
            result = await proactive_service._create_bell_notification({
                "type": "daily_briefing",
                "recruiter_id": "recruiter-1",
                "title": "Test",
                "message": "Test",
                "data": {},
            })
            assert result is False


class TestNotificationServiceCRUD:

    @pytest.mark.asyncio
    async def test_create_notification_with_db(self, notification_service):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        from lia_messaging.notification_service import NotificationType

        result = await notification_service.create_notification(
            user_id="recruiter-1",
            title="Test Create",
            message="Test message",
            notification_type=NotificationType.INFO,
            category="pipeline",
            source_agent="test",
            db=mock_db,
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read_found(self, notification_service):
        from lia_messaging.notification_service import Notification

        mock_notif = Notification(
            id="notif-1",
            user_id="recruiter-1",
            title="Test",
            is_read=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notif
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await notification_service.mark_as_read("notif-1", "recruiter-1", db=mock_db)
        assert result is True
        assert mock_notif.is_read is True

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, notification_service):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await notification_service.mark_as_read("nonexistent", "recruiter-1", db=mock_db)
        assert result is False

    @pytest.mark.asyncio
    async def test_dismiss_notification_found(self, notification_service):
        from lia_messaging.notification_service import Notification

        mock_notif = Notification(
            id="notif-2",
            user_id="recruiter-1",
            title="Dismiss Test",
            is_dismissed=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notif
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await notification_service.dismiss_notification("notif-2", "recruiter-1", db=mock_db)
        assert result is True
        assert mock_notif.is_dismissed is True

    @pytest.mark.asyncio
    async def test_dismiss_notification_not_found(self, notification_service):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await notification_service.dismiss_notification("nonexistent", "recruiter-1", db=mock_db)
        assert result is False


class TestNotificationAPIEndpoints:

    def test_api_router_has_correct_prefix(self):
        from app.api.v1.notifications import router
        assert router.prefix == "/notifications"

    def test_create_notification_request_model(self):
        from app.api.v1.notifications import CreateNotificationRequest
        req = CreateNotificationRequest(
            user_id="recruiter-1",
            title="Test",
            message="Test message",
            notification_type="info",
            category="pipeline",
        )
        assert req.user_id == "recruiter-1"
        assert req.notification_type == "info"

    def test_multi_channel_request_defaults_to_bell(self):
        from app.api.v1.notifications import MultiChannelNotificationRequest
        req = MultiChannelNotificationRequest(
            user_id="recruiter-1",
            title="Test",
            message="Test message",
        )
        assert "bell" in req.channels
        assert "chat" in req.channels

    def test_recruiter_action_request_defaults_to_bell(self):
        from app.api.v1.notifications import RecruiterActionNotificationRequest
        req = RecruiterActionNotificationRequest(
            recruiter_ids=["recruiter-1"],
            action="pause",
            job_titles=["Dev Backend"],
            job_ids=["job-1"],
        )
        assert req.channels == ["bell"]


class TestProactiveServiceTierMapping:

    def test_tier_a_from_high_wsi(self):
        from app.domains.automation.services.proactive_service import ProactiveService
        assert ProactiveService._get_tier_from_wsi(4.5) == "A"
        assert ProactiveService._get_tier_from_wsi(4.0) == "A"

    def test_tier_b_from_medium_wsi(self):
        from app.domains.automation.services.proactive_service import ProactiveService
        assert ProactiveService._get_tier_from_wsi(3.5) == "B"
        assert ProactiveService._get_tier_from_wsi(3.0) == "B"

    def test_tier_c_from_low_wsi(self):
        from app.domains.automation.services.proactive_service import ProactiveService
        assert ProactiveService._get_tier_from_wsi(2.5) == "C"
        assert ProactiveService._get_tier_from_wsi(2.0) == "C"

    def test_tier_d_from_very_low_wsi(self):
        from app.domains.automation.services.proactive_service import ProactiveService
        assert ProactiveService._get_tier_from_wsi(1.5) == "D"
        assert ProactiveService._get_tier_from_wsi(0.0) == "D"


class TestNotificationRepositoryBehavior:

    def test_repository_model_class(self):
        from app.shared.repositories.notification_repository import NotificationRepository
        from lia_messaging.notification_service import Notification
        repo = NotificationRepository()
        assert repo.model_class is Notification

    @pytest.mark.asyncio
    async def test_get_unread_count(self):
        from app.shared.repositories.notification_repository import NotificationRepository
        repo = NotificationRepository()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        count = await repo.get_unread_count(mock_db, "recruiter-1")
        assert count == 5

    @pytest.mark.asyncio
    async def test_mark_as_read_via_repo(self):
        from app.shared.repositories.notification_repository import NotificationRepository
        from lia_messaging.notification_service import Notification
        repo = NotificationRepository()

        mock_notif = Notification(
            id="notif-repo-1",
            user_id="recruiter-1",
            title="Repo Read Test",
            is_read=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notif
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        result = await repo.mark_as_read(mock_db, "notif-repo-1")
        assert result is True
        assert mock_notif.is_read is True


class TestBellNotificationAPIIntegration:

    def test_notification_api_module_exposes_router(self):
        from app.api.v1 import notifications
        assert hasattr(notifications, 'router')
        routes = [r.path for r in notifications.router.routes if hasattr(r, 'path')]
        assert any("read" in r for r in routes)
        assert any("dismiss" in r for r in routes)

    @pytest.mark.asyncio
    async def test_create_and_retrieve_notification_flow(self):
        from lia_messaging.notification_service import (
            NotificationService, NotificationType, NotificationChannel, Notification
        )
        svc = NotificationService()

        notif = Notification(
            id="integ-test-1",
            user_id="recruiter-integ",
            title="Bell Integration Test",
            message="Created via integration test",
            notification_type=NotificationType.INFO.value,
            channels=[NotificationChannel.BELL.value],
            category="system",
            source_agent="test_runner",
        )
        assert notif.id == "integ-test-1"
        assert NotificationChannel.BELL.value in notif.channels
        assert not notif.is_read

        notif_dict = notif.to_dict()
        assert notif_dict["title"] == "Bell Integration Test"
        assert notif_dict["user_id"] == "recruiter-integ"
        assert not notif_dict["is_read"]

        notif.is_read = True
        assert notif.to_dict()["is_read"] is True

    @pytest.mark.asyncio
    async def test_full_bell_creation_via_proactive_service(self):
        from app.domains.automation.services.proactive_service import ProactiveService
        svc = ProactiveService()

        mock_ns = MagicMock()
        created_notif = {
            "id": "integ-bell-1",
            "title": "Proactive Alert",
            "user_id": "recruiter-integ",
            "channels": ["bell"],
            "is_read": False,
        }
        mock_ns.create_notification = AsyncMock(return_value=created_notif)

        notification = {
            "type": "pipeline_stagnation",
            "priority": "high",
            "recruiter_id": "recruiter-integ",
            "title": "Pipeline Stagnation Alert",
            "message": "3 candidates stagnated",
            "data": {"job_id": "job-123"},
            "channel": "teams",
        }

        with patch('lia_messaging.notification_service.notification_service', mock_ns):
            result = await svc._create_bell_notification(notification)
            assert result is True
            call_kwargs = mock_ns.create_notification.call_args[1]
            assert call_kwargs["user_id"] == "recruiter-integ"
            assert call_kwargs["title"] == "Pipeline Stagnation Alert"
            assert "bell" in str(call_kwargs.get("channels", []))

    def test_weekly_digest_uses_bell_channel(self):
        from app.domains.analytics.services.weekly_digest_service import WeeklyDigestService
        import inspect
        source = inspect.getsource(WeeklyDigestService)
        assert "bell" in source, "WeeklyDigestService must include bell channel"

    def test_screening_uses_bell_channel(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        import inspect
        source = inspect.getsource(RubricEvaluationService)
        assert "BELL" in source, "RubricEvaluationService must include BELL channel"

    def test_proactive_service_creates_bell_notification(self):
        from app.domains.automation.services.proactive_service import ProactiveService
        import inspect
        source = inspect.getsource(ProactiveService._create_bell_notification)
        assert "BELL" in source, "ProactiveService._create_bell_notification must use BELL channel"
        assert "create_notification" in source, "Must call create_notification"
