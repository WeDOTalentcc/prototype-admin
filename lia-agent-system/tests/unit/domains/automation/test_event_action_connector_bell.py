"""Tests for EventActionConnector bell notifications (G5)"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from enum import Enum


class EventType(str, Enum):
    APPROVAL_PENDING = "approval_pending"
    CANDIDATE_REJECTED = "candidate_rejected"


@pytest.mark.asyncio
async def test_send_notification_for_event_includes_bell():
    """_send_notification_for_event includes bell channel"""
    from app.domains.automation.services.event_action_connector import EventActionConnector
    
    connector = EventActionConnector()
    
    # Mock event
    mock_event = MagicMock()
    mock_event.event_type = EventType.APPROVAL_PENDING
    mock_event.company_id = str(uuid4())
    mock_event.severity = "warning"
    mock_event.title = "Test Event"
    mock_event.message = "Test message"
    mock_event.suggested_action = "test_action"
    mock_event.action_label = "Test Action"
    mock_event.data = {}
    mock_event.candidate_id = str(uuid4())
    mock_event.vacancy_id = str(uuid4())
    
    with patch.object(connector, "_get_notification_service") as mock_get_notif:
        with patch("app.domains.automation.services.event_action_connector.NotificationType"):
            mock_notif_service = AsyncMock()
            mock_get_notif.return_value = mock_notif_service
            
            result = await connector._send_notification_for_event(mock_event)
    
    # Verify success and bell channel
    assert result is True
    mock_notif_service.create_notification.assert_called_once()
    call_kwargs = mock_notif_service.create_notification.call_args.kwargs
    assert call_kwargs["channels"] == ["bell"]
    assert call_kwargs["category"] == "pipeline_monitor"


@pytest.mark.asyncio
async def test_process_events_sends_bell_notifications():
    """process_events emits bell notifications for each event"""
    from app.domains.automation.services.event_action_connector import EventActionConnector
    
    connector = EventActionConnector()
    
    # Mock events
    mock_events = []
    for i in range(2):
        mock_event = MagicMock()
        mock_event.event_type = EventType.APPROVAL_PENDING
        mock_event.company_id = str(uuid4())
        mock_event.severity = "info"
        mock_event.title = f"Event {i}"
        mock_event.message = f"Message {i}"
        mock_event.suggested_action = "test"
        mock_event.action_label = "Test"
        mock_event.data = {}
        mock_event.candidate_id = str(uuid4())
        mock_event.vacancy_id = str(uuid4())
        mock_events.append(mock_event)
    
    with patch.object(connector, "_create_action_from_event", return_value=True):
        with patch.object(connector, "_send_notification_for_event", return_value=True):
            result = await connector.process_events(mock_events)
    
    # Verify both events were processed
    assert result["actions_created"] == 2
    assert result["notifications_sent"] == 2
    assert result["errors"] == 0

