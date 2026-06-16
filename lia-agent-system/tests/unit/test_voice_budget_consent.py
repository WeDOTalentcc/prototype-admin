"""Tests específicos de budget/consent para DataRequestVoiceService."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class _FakeCandidate:
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = "Maria"
        self.phone = "+5511999999999"
        self.email = "m@x.com"


class _FakeDataRequest:
    def __init__(self):
        self.id = uuid.uuid4()
        self.candidate_id = uuid.uuid4()
        self.company_id = uuid.uuid4()
        self.token = "tok-abc"
        self.fields_requested = [
            {"name": "cpf", "label": "CPF", "field_type": "cpf", "is_required": True},
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


@pytest.mark.asyncio
async def test_budget_exceeded_blocks_call():
    """When monthly budget is exceeded, start_collection must return
    voice_collection_budget_exceeded and NOT place a call."""
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
        VOICE_CALLS_MONTHLY_DEFAULT_LIMIT,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    cand.id = dr.candidate_id
    db = _fake_db(dr, cand)

    result = MagicMock()
    result.allowed = True
    result.soft_warning = False
    checker = MagicMock()
    checker.check_candidate_consent = AsyncMock(return_value=result)

    with patch(
        "app.domains.lgpd.services.consent_checker_service.ConsentCheckerService",
        MagicMock(return_value=checker),
    ), patch(
        "app.domains.communication.services.data_request_voice_service._check_voice_budget",
        AsyncMock(return_value=(False, VOICE_CALLS_MONTHLY_DEFAULT_LIMIT)),
    ):
        result = await DataRequestVoiceService().start_collection(
            db, dr.id, cand.phone
        )

    assert result["status"] == "voice_collection_budget_exceeded", f"got: {result}"
    assert result["limit"] == VOICE_CALLS_MONTHLY_DEFAULT_LIMIT
    assert result["channel"] == "voice"


@pytest.mark.asyncio
async def test_consent_revoked_blocks_call():
    """When LGPD consent is revoked, start_collection must return
    voice_collection_no_consent (fail-closed, no re-solicit)."""
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    cand.id = dr.candidate_id
    db = _fake_db(dr, cand)

    with patch.object(
        DataRequestVoiceService,
        "_classify_consent",
        AsyncMock(return_value="revoked"),
    ):
        result = await DataRequestVoiceService().start_collection(
            db, dr.id, cand.phone
        )

    assert result["status"] == "voice_collection_no_consent", f"got: {result}"
    assert result["channel"] == "voice"


@pytest.mark.asyncio
async def test_data_request_not_found_returns_error():
    """When data_request_id is not found, start_collection returns explicit error."""
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    db = MagicMock()
    db.get = AsyncMock(return_value=None)

    result = await DataRequestVoiceService().start_collection(
        db, uuid.uuid4(), "+5511999999999"
    )

    assert result["status"] == "error"
    assert result.get("error") == "data_request_not_found"
    assert result["channel"] == "voice"
