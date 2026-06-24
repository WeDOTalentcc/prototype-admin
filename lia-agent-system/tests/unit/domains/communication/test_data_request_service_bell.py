"""Tests for data_request_service bell notifications (G5)"""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.domains.communication.services.data_request_service import DataRequestService
from lia_models.data_request import DataRequest, DataRequestStatus, TriggerType


@pytest.mark.asyncio
async def test_send_notification_emits_bell_on_email_success():
    """send_notification emits bell notification after successful email send"""
    company_id = uuid4()
    candidate_id = uuid4()
    vacancy_id = uuid4()
    data_request_id = uuid4()
    
    # Mock database
    mock_db = AsyncMock()
    
    # Mock data_request
    data_request = MagicMock(spec=DataRequest)
    data_request.id = data_request_id
    data_request.candidate_id = candidate_id
    data_request.vacancy_id = vacancy_id
    data_request.company_id = company_id
    data_request.is_blocking = False
    data_request.token = "test-token-123"
    data_request.sent_via_email = False
    data_request.sent_via_whatsapp = False
    data_request.sent_via_voice = False
    
    # Mock candidate
    candidate = MagicMock()
    candidate.email = "candidate@test.com"
    candidate.name = "Test Candidate"
    
    mock_db.get = AsyncMock(side_effect=lambda model, id_: 
        data_request if id_ == data_request_id else candidate if id_ == candidate_id else None
    )
    mock_db.commit = AsyncMock()
    
    # Patch dependencies
    with patch("app.domains.communication.services.data_request_service.communication_dispatcher") as mock_dispatcher:
        with patch("app.domains.communication.services.data_request_service.notification_service") as mock_notif_svc:
            mock_dispatcher.send_email = MagicMock(return_value={"success": True})
            mock_notif_svc.create_notification = AsyncMock()
            
            service = DataRequestService()
            result = await service.send_notification(mock_db, data_request_id, channels=["email"])
    
    # Assertions
    assert result["email"]["success"]
    # Verify bell notification was created
    mock_notif_svc.create_notification.assert_called_once()
    call_kwargs = mock_notif_svc.create_notification.call_args.kwargs
    assert call_kwargs["channels"] == ["bell"]
    assert call_kwargs["category"] == "data_request"
    assert call_kwargs["user_id"] == str(candidate_id)


@pytest.mark.asyncio
async def test_send_notification_no_bell_on_failure():
    """send_notification does not emit bell if all channels fail"""
    data_request_id = uuid4()
    candidate_id = uuid4()
    
    mock_db = AsyncMock()
    
    data_request = MagicMock(spec=DataRequest)
    data_request.id = data_request_id
    data_request.candidate_id = candidate_id
    data_request.vacancy_id = None
    data_request.is_blocking = False
    
    candidate = MagicMock()
    candidate.email = None  # No email - will fail
    
    mock_db.get = AsyncMock(side_effect=lambda model, id_: 
        data_request if id_ == data_request_id else candidate if id_ == candidate_id else None
    )
    mock_db.commit = AsyncMock()
    
    with patch("app.domains.communication.services.data_request_service.communication_dispatcher"):
        with patch("app.domains.communication.services.data_request_service.notification_service") as mock_notif_svc:
            mock_notif_svc.create_notification = AsyncMock()
            
            service = DataRequestService()
            result = await service.send_notification(mock_db, data_request_id, channels=["email"])
    
    # All channels failed, no bell should be emitted
    assert not result["email"]["success"]
    mock_notif_svc.create_notification.assert_not_called()


@pytest.mark.asyncio
async def test_resend_notification_emits_bell():
    """resend_notification (reminder) emits bell notification"""
    company_id = uuid4()
    candidate_id = uuid4()
    vacancy_id = uuid4()
    data_request_id = uuid4()
    
    mock_db = AsyncMock()
    
    data_request = MagicMock(spec=DataRequest)
    data_request.id = data_request_id
    data_request.candidate_id = candidate_id
    data_request.vacancy_id = vacancy_id
    data_request.company_id = company_id
    data_request.status = DataRequestStatus.PENDING
    data_request.is_blocking = False
    data_request.token = "test-token"
    data_request.reminder_count = 0
    data_request.sent_via_email = False
    data_request.sent_via_whatsapp = False
    data_request.sent_via_voice = False
    
    candidate = MagicMock()
    candidate.email = "candidate@test.com"
    candidate.name = "Test"
    
    mock_db.get = AsyncMock(side_effect=lambda model, id_: 
        data_request if id_ == data_request_id else candidate if id_ == candidate_id else None
    )
    mock_db.commit = AsyncMock()
    
    with patch("app.domains.communication.services.data_request_service.communication_dispatcher") as mock_dispatcher:
        with patch("app.domains.communication.services.data_request_service.notification_service") as mock_notif_svc:
            mock_dispatcher.send_email = MagicMock(return_value={"success": True})
            mock_notif_svc.create_notification = AsyncMock()
            
            service = DataRequestService()
            result = await service.resend_notification(mock_db, data_request_id, channels=["email"])
    
    assert result["reminder_count"] == 1
    mock_notif_svc.create_notification.assert_called_once()
    call_kwargs = mock_notif_svc.create_notification.call_args.kwargs
    assert call_kwargs["channels"] == ["bell"]
