"""
Fase 3-4 — LGPD consent gate + recording notice + canonical persistence for
voice-call data collection.

Tests:
- consent BLOCK: no consent → start_collection returns
  "voice_collection_no_consent" and the orchestrator is NEVER instantiated
  (the call is NOT placed).
- consent OK: explicit consent → start_collection proceeds to instantiate the
  orchestrator + place the call (mocked).
- recording notice: the FIRST thing the DataCollectionVoicePlugin says
  (get_next_question) is the LGPD recording/data-collection notice, BEFORE any
  field question.
- canonical persistence: on_session_finalized, with 2 valid + 1 needs_followup
  field, persists ONLY the 2 valid fields via the canonical DataRequestResponse
  model (one row each) + appends to DataRequest.fields_completed with
  source="voice_collection"; the needs_followup field is NEVER persisted.

ALL voice-orchestrator imports + ConsentCheckerService are mocked so the heavy
real import never loads (importing voice_screening_orchestrator at module load
drops the SSH session).
"""
import sys
import types
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------
class _FakeCandidate:
    def __init__(self, name="Maria"):
        self.id = uuid.uuid4()
        self.name = name
        self.phone = "+5511999999999"
        self.email = "m@x.com"


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
    db.add = MagicMock()
    return db


def _consent_result(allowed=True, soft_warning=False):
    r = MagicMock()
    r.allowed = allowed
    r.soft_warning = soft_warning
    return r


def _patch_consent(allowed=True, soft_warning=False):
    """Patch the lazily-imported ConsentCheckerService class."""
    checker_instance = MagicMock()
    checker_instance.check_candidate_consent = AsyncMock(
        return_value=_consent_result(allowed=allowed, soft_warning=soft_warning)
    )
    checker_cls = MagicMock(return_value=checker_instance)
    return patch(
        "app.domains.lgpd.services.consent_checker_service.ConsentCheckerService",
        checker_cls,
    )


# ---------------------------------------------------------------------------
# TEST 1 — consent BLOCK: no consent → no call, explicit status
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_start_collection_blocks_when_no_consent():
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    db = _fake_db(dr, cand)

    fake_orch_cls = MagicMock()  # must NOT be called

    with _patch_consent(allowed=True, soft_warning=True), patch(
        "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
        fake_orch_cls,
    ), patch(
        "app.domains.voice.plugins.data_collection_voice_plugin.DataCollectionVoicePlugin",
        MagicMock(),
    ):
        svc = DataRequestVoiceService()
        result = await svc.start_collection(
            db=db, data_request_id=dr.id, candidate_phone="+5511999999999"
        )

    assert result["status"] == "voice_collection_no_consent", result
    fake_orch_cls.assert_not_called()  # call NOT placed (fail-closed)


@pytest.mark.asyncio
async def test_start_collection_blocks_when_consent_revoked():
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    db = _fake_db(dr, cand)
    fake_orch_cls = MagicMock()

    with _patch_consent(allowed=False, soft_warning=False), patch(
        "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
        fake_orch_cls,
    ), patch(
        "app.domains.voice.plugins.data_collection_voice_plugin.DataCollectionVoicePlugin",
        MagicMock(),
    ):
        svc = DataRequestVoiceService()
        result = await svc.start_collection(
            db=db, data_request_id=dr.id, candidate_phone="+5511999999999"
        )

    assert result["status"] == "voice_collection_no_consent", result
    fake_orch_cls.assert_not_called()


# ---------------------------------------------------------------------------
# TEST 2 — consent OK → proceeds to instantiate orchestrator + place call
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_start_collection_proceeds_with_consent():
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    db = _fake_db(dr, cand)

    fake_session = MagicMock()
    fake_session.status = "fallback"  # Twilio not configured in tests
    fake_session.session_id = "vs-1"
    fake_orch = MagicMock()
    fake_orch.initiate_call = AsyncMock(return_value=fake_session)
    fake_orch_cls = MagicMock(return_value=fake_orch)
    fake_plugin_cls = MagicMock()

    with _patch_consent(allowed=True, soft_warning=False), patch(
        "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
        fake_orch_cls,
    ), patch(
        "app.domains.voice.plugins.data_collection_voice_plugin.DataCollectionVoicePlugin",
        fake_plugin_cls,
    ):
        svc = DataRequestVoiceService()
        result = await svc.start_collection(
            db=db, data_request_id=dr.id, candidate_phone="+5511999999999"
        )

    # Consent OK → orchestrator instantiated + call attempted.
    fake_orch_cls.assert_called_once()
    fake_orch.initiate_call.assert_awaited_once()
    assert result["status"] in {
        "voice_collection_initiated",
        "voice_collection_fallback",
    }, result
    # Plugin constructed WITH the data_request_id (Fase 4 wiring).
    _, kwargs = fake_plugin_cls.call_args
    assert kwargs.get("data_request_id") == dr.id


# ---------------------------------------------------------------------------
# TEST 3 — recording notice is the FIRST utterance
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_recording_notice_is_first_question():
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )

    plugin = DataCollectionVoicePlugin(
        fields=[
            {"name": "cpf", "label": "CPF", "field_type": "cpf", "is_required": True},
        ]
    )
    session = MagicMock()
    session.session_id = "vs-1"
    session.metadata = {}

    await plugin.on_session_initiated(session, db=None)

    first = await plugin.get_next_question(session, db=None)
    assert first == DataCollectionVoicePlugin.RECORDING_NOTICE
    assert "gravada" in first.lower()
    assert "proteção de dados" in first.lower()

    # The NEXT question is a real field prompt, not the notice again.
    second = await plugin.get_next_question(session, db=None)
    assert second is not None
    assert second != DataCollectionVoicePlugin.RECORDING_NOTICE
    assert "cpf" in second.lower()


# ---------------------------------------------------------------------------
# TEST 4 — canonical persistence: only valid fields persisted; needs_followup not
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_finalize_persists_only_valid_fields_via_canonical_model():
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )

    dr = _FakeDataRequest(
        fields_requested=[
            {"name": "cpf", "label": "CPF", "field_type": "cpf", "is_required": True},
            {"name": "rg", "label": "RG", "field_type": "text", "is_required": True},
            {"name": "phone", "label": "Telefone", "field_type": "phone", "is_required": True},
        ]
    )
    db = MagicMock()
    db.get = AsyncMock(return_value=dr)
    db.add = MagicMock()
    db.commit = AsyncMock()

    plugin = DataCollectionVoicePlugin(
        fields=dr.fields_requested,
        data_request_id=dr.id,
    )
    session = MagicMock()
    session.session_id = "vs-1"
    session.metadata = {}
    await plugin.on_session_initiated(session, db=db)

    # Transcript: notice → cpf (valid 11 digits) → rg (valid) → phone (invalid, too short)
    # The plugin pairs candidate utterances positionally with asked field prompts.
    transcript = [
        {"role": "assistant", "text": DataCollectionVoicePlugin.RECORDING_NOTICE},
        {"role": "candidate", "text": "123 456 789 09"},   # cpf → 11 digits valid
        {"role": "candidate", "text": "MG-12.345.678"},     # rg text valid
        {"role": "candidate", "text": "12"},                # phone invalid (too short)
    ]

    result = await plugin.on_session_finalized(session, db=db, transcript=transcript)

    # cpf + rg valid; phone needs follow-up.
    assert "phone" in result["needs_followup"], result
    persisted = result.get("persisted_fields", [])
    assert set(persisted) == {"cpf", "rg"}, persisted

    # Canonical model: one DataRequestResponse row per VALID field (2), no row
    # for the needs_followup phone.
    assert db.add.call_count == 2
    db.commit.assert_awaited()

    # fields_completed appended with source="voice_collection" for the 2 valid.
    completed_names = {f["name"] for f in dr.fields_completed}
    assert completed_names == {"cpf", "rg"}, dr.fields_completed
    assert all(f.get("source") == "voice_collection" for f in dr.fields_completed)
    assert "phone" not in completed_names  # never persisted as answered


@pytest.mark.asyncio
async def test_finalize_no_persist_without_data_request_id():
    """No data_request_id → finalize returns dict but persists nothing."""
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )

    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.get = AsyncMock(return_value=None)

    plugin = DataCollectionVoicePlugin(
        fields=[{"name": "cpf", "label": "CPF", "field_type": "cpf"}],
        # no data_request_id
    )
    session = MagicMock()
    session.session_id = "vs-1"
    session.metadata = {}
    await plugin.on_session_initiated(session, db=db)

    transcript = [
        {"role": "assistant", "text": "notice"},
        {"role": "candidate", "text": "123 456 789 09"},
    ]
    result = await plugin.on_session_finalized(session, db=db, transcript=transcript)
    assert result.get("persisted_fields", []) == []
    db.add.assert_not_called()
