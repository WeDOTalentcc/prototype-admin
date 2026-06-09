"""
Fase 1 — Voice channel for DataRequest.

Tests:
- DataRequestService.send_notification accepts channel="voice" and routes
  to DataRequestVoiceService (mocked).
- Invalid channel "telegram" is still rejected (no permissive allow-list).
- DataRequestVoiceService.start_collection builds the collection script for
  the requested fields.
- start_collection does NOT silently fake a completed collection — it carries
  an explicit prepared/initiated/fallback status, never "completed".

ALL voice-orchestrator imports are mocked so the heavy real import never loads
(importing voice_screening_orchestrator at module load drops the SSH session).
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------
class _FakeCandidate:
    def __init__(self, name="Maria", phone="+5511999999999", email="m@x.com"):
        self.id = uuid.uuid4()
        self.name = name
        self.phone = phone
        self.email = email


class _FakeDataRequest:
    def __init__(self, fields_requested=None):
        self.id = uuid.uuid4()
        self.candidate_id = uuid.uuid4()
        self.company_id = uuid.uuid4()
        self.token = "tok-abc"
        self.fields_requested = fields_requested or [
            {"name": "cpf", "label": "CPF", "field_type": "cpf", "is_required": True},
            {"name": "rg", "label": "RG", "field_type": "text", "is_required": True},
        ]
        self.fields_completed = []
        self.collection_method = None
        self.sent_via_email = False
        self.sent_via_whatsapp = False
        self.email_sent_at = None
        self.whatsapp_sent_at = None
        self.is_blocking = False


def _fake_db(data_request, candidate):
    db = MagicMock()

    async def _get(model, ident):
        # Return data_request first, candidate second based on id match.
        if ident == data_request.id:
            return data_request
        if ident == data_request.candidate_id or ident == candidate.id:
            return candidate
        return None

    db.get = AsyncMock(side_effect=_get)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


# ---------------------------------------------------------------------------
# TEST 1 — send_notification accepts "voice" and routes to voice service
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_notification_accepts_voice_channel_and_routes():
    from app.domains.communication.services.data_request_service import (
        DataRequestService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    cand.id = dr.candidate_id
    db = _fake_db(dr, cand)

    with patch(
        "app.domains.communication.services.data_request_voice_service.DataRequestVoiceService"
    ) as MockVoice:
        instance = MockVoice.return_value
        instance.start_collection = AsyncMock(
            return_value={
                "status": "voice_collection_prepared",
                "channel": "voice",
                "fields": ["cpf", "rg"],
            }
        )

        result = await DataRequestService().send_notification(
            db, dr.id, channels=["voice"]
        )

    assert "voice" in result, f"voice channel missing from result: {result}"
    # Must NOT be an 'unsupported channel' error.
    assert result["voice"].get("error") != "unsupported_channel"
    instance.start_collection.assert_awaited_once()


# ---------------------------------------------------------------------------
# TEST 2 — invalid channel is rejected (allow-list not permissive)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_notification_rejects_invalid_channel():
    from app.domains.communication.services.data_request_service import (
        DataRequestService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    cand.id = dr.candidate_id
    db = _fake_db(dr, cand)

    result = await DataRequestService().send_notification(
        db, dr.id, channels=["telegram"]
    )

    assert "telegram" in result, (
        "invalid channel should surface an explicit error entry, not be "
        f"silently dropped: {result}"
    )
    assert result["telegram"]["success"] is False
    assert result["telegram"]["error"] == "unsupported_channel"


# ---------------------------------------------------------------------------
# TEST 3 — start_collection builds the collection script for the fields
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_voice_start_collection_builds_script():
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    cand.id = dr.candidate_id
    db = _fake_db(dr, cand)

    # Mock the lazily-imported voice orchestrator so the heavy import never loads.
    fake_session = MagicMock()
    fake_session.status = "fallback"  # Twilio not configured in tests
    fake_session.session_id = "vs-1"
    fake_orch = MagicMock()
    fake_orch.initiate_call = AsyncMock(return_value=fake_session)

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator.voice_screening_orchestrator",
        fake_orch,
    ):
        result = await DataRequestVoiceService().start_collection(
            db, dr.id, cand.phone
        )

    # The prepared result must carry the requested fields.
    assert "fields" in result
    assert set(result["fields"]) >= {"cpf", "rg"}
    assert result["channel"] == "voice"


# ---------------------------------------------------------------------------
# TEST 4 — start_collection never fakes "completed"
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_voice_start_collection_does_not_fake_completed():
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    cand.id = dr.candidate_id
    db = _fake_db(dr, cand)

    fake_session = MagicMock()
    fake_session.status = "fallback"
    fake_session.session_id = "vs-1"
    fake_orch = MagicMock()
    fake_orch.initiate_call = AsyncMock(return_value=fake_session)

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator.voice_screening_orchestrator",
        fake_orch,
    ):
        result = await DataRequestVoiceService().start_collection(
            db, dr.id, cand.phone
        )

    status = result.get("status")
    assert status is not None, f"start_collection must carry an explicit status: {result}"
    assert status != "completed", (
        "start_collection must NOT report a fake completed collection "
        f"(anti-silent-fallback): {result}"
    )
    assert status in {
        "voice_collection_prepared",
        "voice_collection_initiated",
        "voice_collection_fallback",
    }, f"unexpected status: {status}"
