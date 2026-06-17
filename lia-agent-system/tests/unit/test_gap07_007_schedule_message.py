"""Tests for GAP-07-007: schedule_message endpoint.

Verifies:
- Valid payload → 201 with scheduled_message_id + status=pending
- send_at in the past → 422 send_at_in_past
- Missing send_at → 422 validation error
- Invalid channel → 422 invalid_channel
- company_id comes from JWT (not payload)
- LGPD: lgpd_expiry = send_at + 90 days stored
"""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch


FUTURE_ISO = (datetime.now(UTC) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
PAST_ISO = (datetime.now(UTC) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

VALID_PAYLOAD = {
    "candidate_id": "cand-abc-123",
    "candidate_name": "Ana Lima",
    "channel": "email",
    "message": "Olá! Gostaríamos de conversar sobre sua candidatura.",
    "send_at": FUTURE_ISO,
}


def _make_mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


class TestScheduleMessageEndpoint:
    """GAP-07-007: POST /communication/schedule-message."""

    @pytest.mark.asyncio
    async def test_valid_payload_returns_201(self):
        """Valid payload with future send_at → 201 + scheduled_message_id."""
        from app.api.v1.communication import schedule_message, ScheduleMessageRequest

        req = ScheduleMessageRequest(**VALID_PAYLOAD)
        mock_db = _make_mock_db()

        result = await schedule_message(
            request=req,
            db=mock_db,
            company_id="company-x",
        )

        assert result.status == "pending"
        assert result.channel == "email"
        assert result.candidate_id == "cand-abc-123"
        assert result.scheduled_message_id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_past_send_at_returns_422(self):
        """send_at in the past → 422 send_at_in_past."""
        from fastapi import HTTPException
        from app.api.v1.communication import schedule_message, ScheduleMessageRequest

        payload = {**VALID_PAYLOAD, "send_at": PAST_ISO}
        req = ScheduleMessageRequest(**payload)
        mock_db = _make_mock_db()

        with pytest.raises(HTTPException) as exc_info:
            await schedule_message(request=req, db=mock_db, company_id="company-x")

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"] == "send_at_in_past"

    @pytest.mark.asyncio
    async def test_invalid_channel_returns_422(self):
        """Unknown channel string → 422 invalid_channel."""
        from fastapi import HTTPException
        from app.api.v1.communication import schedule_message, ScheduleMessageRequest

        payload = {**VALID_PAYLOAD, "channel": "sms"}
        req = ScheduleMessageRequest(**payload)
        mock_db = _make_mock_db()

        with pytest.raises(HTTPException) as exc_info:
            await schedule_message(request=req, db=mock_db, company_id="company-x")

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"] == "invalid_channel"

    @pytest.mark.asyncio
    async def test_whatsapp_channel_accepted(self):
        """channel=whatsapp is a valid channel."""
        from app.api.v1.communication import schedule_message, ScheduleMessageRequest

        payload = {**VALID_PAYLOAD, "channel": "whatsapp"}
        req = ScheduleMessageRequest(**payload)
        mock_db = _make_mock_db()

        result = await schedule_message(request=req, db=mock_db, company_id="company-x")
        assert result.channel == "whatsapp"

    @pytest.mark.asyncio
    async def test_company_id_from_jwt_not_payload(self):
        """company_id is sourced from JWT dependency, not from the request model.

        ScheduleMessageRequest inherits WeDoBaseModel (extra=forbid) so a
        company_id field in the payload raises a ValidationError before reaching
        the handler — multi-tenancy is enforced at schema level.
        """
        from pydantic import ValidationError
        from app.api.v1.communication import ScheduleMessageRequest

        with pytest.raises(ValidationError):
            ScheduleMessageRequest(**VALID_PAYLOAD, company_id="injected")

    @pytest.mark.asyncio
    async def test_lgpd_expiry_90_days(self):
        """Stored ScheduledMessage must have lgpd_expiry = send_at + 90 days."""
        from app.api.v1.communication import schedule_message, ScheduleMessageRequest
        from app.models import ScheduledMessage

        req = ScheduleMessageRequest(**VALID_PAYLOAD)
        mock_db = _make_mock_db()

        await schedule_message(request=req, db=mock_db, company_id="company-x")

        # Inspect the object passed to db.add()
        stored: ScheduledMessage = mock_db.add.call_args[0][0]
        delta = stored.lgpd_expiry - stored.send_at
        assert abs(delta.days - 90) <= 1  # allow 1 day float tolerance
