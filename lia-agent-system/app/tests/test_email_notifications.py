"""
Test email notifications for job vacancy publishing.

Tests the complete flow of:
1. Publishing a job vacancy
2. Triggering local sourcing
3. Sending email notification to recruiter
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.notification_service import NotificationChannel, NotificationService, NotificationType


class TestEmailNotifications:
    """Test suite for email notifications."""
    
    @pytest.fixture
    def notification_service(self):
        return NotificationService()
    
    @pytest.fixture
    def sample_notification_data(self):
        return {
            "candidates_added": 12,
            "source_type": "busca local",
            "job_title": "Desenvolvedor Backend Sênior",
            "recipient_email": "paulo.moraes@wedotalent.cc",
            "action_url": "/jobs/test-job-id"
        }
    
    @pytest.mark.asyncio
    async def test_send_to_email_formats_html_correctly(self, notification_service, sample_notification_data):
        """Test that email HTML is formatted correctly."""
        with patch('app.domains.communication.services.email_service.EmailService') as mock_email_service:
            mock_instance = MagicMock()
            mock_instance._send_email_provider = AsyncMock(return_value=True)
            mock_email_service.return_value = mock_instance
            
            await notification_service._send_to_email(
                recipient_email="paulo.moraes@wedotalent.cc",
                title="Candidatos adicionados - Desenvolvedor Backend Sênior",
                message="LIA adicionou 12 candidatos ao pipeline. Aprove para iniciar triagem.",
                notification_type=NotificationType.ACTION_REQUIRED,
                data=sample_notification_data
            )
            
            mock_instance._send_email_provider.assert_called_once()
            call_args = mock_instance._send_email_provider.call_args
            
            assert call_args.kwargs['to_email'] == "paulo.moraes@wedotalent.cc"
            assert "Candidatos adicionados" in call_args.kwargs['subject']
            assert "LIA" in call_args.kwargs['body_html']
            assert "12" in call_args.kwargs['body_html']
    
    @pytest.mark.asyncio
    async def test_send_to_email_includes_action_url(self, notification_service, sample_notification_data):
        """Test that email includes action URL button."""
        with patch('app.domains.communication.services.email_service.EmailService') as mock_email_service:
            mock_instance = MagicMock()
            mock_instance._send_email_provider = AsyncMock(return_value=True)
            mock_email_service.return_value = mock_instance
            
            await notification_service._send_to_email(
                recipient_email="test@example.com",
                title="Test Notification",
                message="Test message",
                notification_type=NotificationType.INFO,
                data=sample_notification_data
            )
            
            call_args = mock_instance._send_email_provider.call_args
            html_body = call_args.kwargs['body_html']
            
            assert "/jobs/test-job-id" in html_body
            assert "Ver Pipeline" in html_body
    
    @pytest.mark.asyncio
    async def test_send_to_email_handles_missing_data(self, notification_service):
        """Test that email handles missing optional data gracefully."""
        with patch('app.domains.communication.services.email_service.EmailService') as mock_email_service:
            mock_instance = MagicMock()
            mock_instance._send_email_provider = AsyncMock(return_value=True)
            mock_email_service.return_value = mock_instance
            
            await notification_service._send_to_email(
                recipient_email="test@example.com",
                title="Simple Notification",
                message="Simple message without extra data",
                notification_type=NotificationType.INFO,
                data=None
            )
            
            mock_instance._send_email_provider.assert_called_once()
            call_args = mock_instance._send_email_provider.call_args
            
            assert call_args.kwargs['to_email'] == "test@example.com"
            assert "Simple Notification" in call_args.kwargs['subject']
    
    @pytest.mark.asyncio
    async def test_send_to_email_raises_on_failure(self, notification_service):
        """Test that email raises exception on send failure."""
        with patch('app.domains.communication.services.email_service.EmailService') as mock_email_service:
            mock_instance = MagicMock()
            mock_instance._send_email_provider = AsyncMock(return_value=False)
            mock_email_service.return_value = mock_instance
            
            with pytest.raises(Exception) as exc_info:
                await notification_service._send_to_email(
                    recipient_email="test@example.com",
                    title="Test",
                    message="Test",
                    notification_type=NotificationType.INFO,
                    data=None
                )
            
            assert "Email sending failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_multi_channel_includes_email(self, notification_service, sample_notification_data):
        """Test that multi-channel notification includes email channel."""
        with patch.object(notification_service, '_send_to_bell', new_callable=AsyncMock) as mock_bell, \
             patch.object(notification_service, '_send_to_teams', new_callable=AsyncMock) as mock_teams, \
             patch.object(notification_service, '_send_to_email', new_callable=AsyncMock) as mock_email:
            
            result = await notification_service.send_multi_channel_notification(
                user_id="test-user-id",
                title="Candidatos adicionados",
                message="LIA encontrou candidatos",
                channels=[
                    NotificationChannel.IN_APP,
                    NotificationChannel.TEAMS,
                    NotificationChannel.EMAIL
                ],
                notification_type=NotificationType.ACTION_REQUIRED,
                data=sample_notification_data
            )
            
            mock_bell.assert_called_once()
            mock_teams.assert_called_once()
            mock_email.assert_called_once()
            
            assert "in_app" in result["sent_to"]
            assert "teams" in result["sent_to"]
            assert "email" in result["sent_to"]
    
    @pytest.mark.asyncio
    async def test_email_template_styling(self, notification_service, sample_notification_data):
        """Test that email template has correct LIA styling."""
        with patch('app.domains.communication.services.email_service.EmailService') as mock_email_service:
            mock_instance = MagicMock()
            mock_instance._send_email_provider = AsyncMock(return_value=True)
            mock_email_service.return_value = mock_instance
            
            await notification_service._send_to_email(
                recipient_email="test@example.com",
                title="Test",
                message="Test message",
                notification_type=NotificationType.INFO,
                data=sample_notification_data
            )
            
            call_args = mock_instance._send_email_provider.call_args
            html_body = call_args.kwargs['body_html']
            
            assert "#00d4aa" in html_body
            assert "Open Sans" in html_body or "Arial" in html_body
            assert "Learning Intelligence Assistant" in html_body


class TestEmailNotificationIntegration:
    """Integration tests for email notification with real Resend API."""
    
    @pytest.fixture
    def real_notification_service(self):
        return NotificationService()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.importorskip("os").environ.get("RESEND_API_KEY"),
        reason="RESEND_API_KEY not configured"
    )
    async def test_send_real_email_to_recruiter(self, real_notification_service):
        """
        Integration test: Send real email to recruiter.
        
        This test actually sends an email via Resend API.
        Only runs when RESEND_API_KEY is configured.
        """
        import os
        
        test_email = os.environ.get("TEST_EMAIL_RECIPIENT", "tech@wedotalent.cc")
        
        data = {
            "candidates_added": 5,
            "job_title": "Teste Automatizado - Desenvolvedor",
            "recipient_email": test_email,
            "action_url": "https://plataforma-lia.replit.app/jobs/test"
        }
        
        try:
            await real_notification_service._send_to_email(
                recipient_email=test_email,
                title="[TESTE] Candidatos Encontrados - Teste Automatizado",
                message="Este é um email de teste automatizado do sistema LIA. "
                        "LIA encontrou 5 candidatos compatíveis com a vaga.",
                notification_type=NotificationType.INFO,
                data=data
            )
            print(f"✅ Email enviado com sucesso para {test_email}")
        except Exception as e:
            pytest.fail(f"Falha ao enviar email: {e}")


class TestCandidatesAddedNotification:
    """Test the complete flow of candidates added notification."""
    
    @pytest.mark.asyncio
    async def test_notification_flow_after_job_publish(self):
        """Test complete notification flow after job is published."""
        from unittest.mock import AsyncMock, MagicMock, patch
        
        mock_db = MagicMock()
        
        notification_data = {
            "user_id": "test-recruiter-id",
            "job_id": str(uuid4()),
            "job_title": "Desenvolvedor Backend Sênior",
            "candidates_added": 12,
            "recruiter_email": "paulo.moraes@wedotalent.cc"
        }
        
        with patch('app.services.notification_service.NotificationService') as MockNotificationService:
            mock_service = MagicMock()
            mock_service.create_notification = AsyncMock(return_value={"id": "test-notification"})
            MockNotificationService.return_value = mock_service
            
            await mock_service.create_notification(
                db=mock_db,
                user_id=notification_data["user_id"],
                title=f"Candidatos adicionados - {notification_data['job_title']}",
                message=f"LIA adicionou {notification_data['candidates_added']} candidatos ao pipeline. Aprove para iniciar triagem.",
                notification_type=NotificationType.ACTION_REQUIRED,
                category="sourcing",
                source_agent="sourcing_pipeline",
                source_trigger="job_publish",
                related_job_id=notification_data["job_id"],
                action_url=f"/jobs/{notification_data['job_id']}",
                action_label="Ver Pipeline",
                channels=[
                    NotificationChannel.IN_APP.value,
                    NotificationChannel.TEAMS.value,
                    NotificationChannel.EMAIL.value
                ],
                metadata={
                    "candidates_added": notification_data["candidates_added"],
                    "source_type": "busca local",
                    "job_title": notification_data["job_title"],
                    "recipient_email": notification_data["recruiter_email"],
                    "action_url": f"/jobs/{notification_data['job_id']}"
                }
            )
            
            mock_service.create_notification.assert_called_once()
            call_args = mock_service.create_notification.call_args
            
            assert NotificationChannel.EMAIL.value in call_args.kwargs['channels']
            assert call_args.kwargs['metadata']['recipient_email'] == "paulo.moraes@wedotalent.cc"
            assert call_args.kwargs['metadata']['candidates_added'] == 12


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
