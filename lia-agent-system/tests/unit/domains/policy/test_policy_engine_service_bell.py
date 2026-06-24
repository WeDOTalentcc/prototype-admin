"""Tests for PolicyEngineService bell notifications (G5)"""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.domains.policy.services.policy_engine_service import PolicyEngineService
from lia_models.policy import EscalationRule, EscalationAction, EscalationLog


@pytest.mark.asyncio
async def test_send_notifications_bell_channel():
    """_send_notifications includes bell channel"""
    recipient_id = str(uuid4())
    
    service = PolicyEngineService()
    
    with patch("app.domains.policy.services.policy_engine_service.notification_service") as mock_notif:
        mock_notif.create_notification = AsyncMock()
        
        result = await service._send_notifications(
            recipients=[recipient_id],
            template="Test notification",
            context={}
        )
    
    # Verify notification was created with bell channel
    mock_notif.create_notification.assert_called_once()
    call_kwargs = mock_notif.create_notification.call_args.kwargs
    assert call_kwargs["channels"] == ["bell"]
    assert call_kwargs["user_id"] == recipient_id
    assert len(result) == 1


@pytest.mark.asyncio
async def test_send_notifications_multiple_recipients():
    """_send_notifications sends bell to all recipients"""
    recipient_ids = [str(uuid4()) for _ in range(3)]
    
    service = PolicyEngineService()
    
    with patch("app.domains.policy.services.policy_engine_service.notification_service") as mock_notif:
        mock_notif.create_notification = AsyncMock()
        
        result = await service._send_notifications(
            recipients=recipient_ids,
            template="Test notification",
            context={}
        )
    
    # Verify notification was created for each recipient
    assert mock_notif.create_notification.call_count == 3
    assert len(result) == 3
    # Verify all calls include bell channel
    for call in mock_notif.create_notification.call_args_list:
        assert call.kwargs["channels"] == ["bell"]
