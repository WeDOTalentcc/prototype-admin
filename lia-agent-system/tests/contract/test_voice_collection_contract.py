"""
Contract sensors — pin the voice-collection canonical shape (Voz Fase 6).

These sensors lock the invariants established across Voz Fases 0-5 so a future
change cannot silently diverge:

1. DataRequestService.send_notification's channel allow-list is EXACTLY
   {email, whatsapp, voice} — no silent permissiveness.
2. An unsupported channel ("telegram") is rejected with "unsupported_channel"
   (regression guard against silent-drop).
3. DataRequestVoiceService.start_collection is FAIL-CLOSED on consent: no /
   absent / revoked consent -> "voice_collection_no_consent" AND the voice
   orchestrator is NEVER instantiated (the call is NOT placed).
4. DataCollectionVoicePlugin.plugin_name == "data_collection" AND
   != "wsi_screening" (the Fase 0.5 WSI gate will never fire for collection
   calls — cross-phase integration guard).
5. on_session_finalized persists ONLY valid fields with source="voice_collection"
   via the canonical DataRequestResponse path; needs_followup fields are NEVER
   persisted as answered (anti-silent-fallback + canonical-producer reuse).
6. The LGPD recording notice is the FIRST utterance.

ALL heavy deps (consent service, voice orchestrator, plugin, dispatcher,
whatsapp service) are mocked so the real heavy import never loads (importing
voice_screening_orchestrator at module load drops the SSH session).

Mocking patterns mirror tests/unit/test_voice_consent_and_persist.py +
tests/unit/test_data_collection_voice_plugin.py +
tests/contract/test_data_request_notification.py.
"""
import inspect
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.communication.services.data_request_service import DataRequestService

DISPATCHER = (
    "app.domains.communication.services."
    "communication_dispatcher.communication_dispatcher.send_email"
)


# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------
def _dr(**kw):
    base = dict(
        token="tok123",
        is_blocking=False,
        candidate_id=uuid.uuid4(),
        sent_via_email=False,
        email_sent_at=None,
        sent_via_whatsapp=False,
        whatsapp_sent_at=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _db(data_request, candidate):
    db = MagicMock()
    db.get = AsyncMock(side_effect=[data_request, candidate])
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


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


class _FakeCandidate:
    def __init__(self, name="Maria"):
        self.id = uuid.uuid4()
        self.name = name
        self.phone = "+5511999999999"
        self.email = "m@x.com"


def _consent_result(allowed=True, soft_warning=False):
    r = MagicMock()
    r.allowed = allowed
    r.soft_warning = soft_warning
    return r


def _patch_consent(allowed=True, soft_warning=False):
    checker_instance = MagicMock()
    checker_instance.check_candidate_consent = AsyncMock(
        return_value=_consent_result(allowed=allowed, soft_warning=soft_warning)
    )
    checker_cls = MagicMock(return_value=checker_instance)
    return patch(
        "app.domains.lgpd.services.consent_checker_service.ConsentCheckerService",
        checker_cls,
    )


def _voice_db(data_request, candidate):
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


# ===========================================================================
# SENSOR 1 — channel allow-list is EXACTLY {email, whatsapp, voice}
# ===========================================================================
def test_supported_channels_is_exactly_email_whatsapp_voice():
    """Pins the allow-list literal in send_notification source.

    No silent permissiveness: any channel outside this set is rejected
    (Sensor 2). If someone adds/removes a channel here without wiring + a
    sensor, this fails and forces the decision to be explicit.
    """
    src = inspect.getsource(DataRequestService.send_notification)
    assert '_SUPPORTED_CHANNELS = {"email", "whatsapp", "voice"}' in src, (
        "Canonical channel allow-list drifted. Expected exactly "
        '{"email", "whatsapp", "voice"} in DataRequestService.send_notification. '
        "Found source did not contain the literal set."
    )


# ===========================================================================
# SENSOR 2 — unsupported channel rejected with "unsupported_channel"
# ===========================================================================
@pytest.mark.asyncio
async def test_unsupported_channel_rejected_not_silently_dropped():
    dr = _dr()
    cand = SimpleNamespace(email="c@x.com", phone="+5511999999999", name="Maria")
    db = _db(dr, cand)

    res = await DataRequestService().send_notification(
        db, uuid.uuid4(), channels=["telegram"]
    )

    assert "telegram" in res, res
    assert res["telegram"]["success"] is False
    assert res["telegram"]["error"] == "unsupported_channel", res


# ===========================================================================
# SENSOR 3 — voice collection is FAIL-CLOSED on consent
# ===========================================================================
@pytest.mark.asyncio
async def test_voice_no_consent_blocks_and_orchestrator_not_instantiated():
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    db = _voice_db(dr, cand)

    fake_orch_cls = MagicMock()  # must NOT be called when consent is denied

    # allowed=True + soft_warning=True still means "no firm consent" -> blocked,
    # mirroring test_voice_consent_and_persist.test_start_collection_blocks_when_no_consent.
    with _patch_consent(allowed=True, soft_warning=True), patch(
        "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
        fake_orch_cls,
    ), patch(
        "app.domains.voice.plugins.data_collection_voice_plugin.DataCollectionVoicePlugin",
        MagicMock(),
    ):
        result = await DataRequestVoiceService().start_collection(
            db=db, data_request_id=dr.id, candidate_phone="+5511999999999"
        )

    assert result["status"] == "voice_collection_no_consent", result
    fake_orch_cls.assert_not_called()  # call NOT placed (fail-closed)


@pytest.mark.asyncio
async def test_voice_revoked_consent_blocks_and_orchestrator_not_instantiated():
    from app.domains.communication.services.data_request_voice_service import (
        DataRequestVoiceService,
    )

    dr = _FakeDataRequest()
    cand = _FakeCandidate()
    db = _voice_db(dr, cand)

    fake_orch_cls = MagicMock()

    with _patch_consent(allowed=False, soft_warning=False), patch(
        "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator",
        fake_orch_cls,
    ), patch(
        "app.domains.voice.plugins.data_collection_voice_plugin.DataCollectionVoicePlugin",
        MagicMock(),
    ):
        result = await DataRequestVoiceService().start_collection(
            db=db, data_request_id=dr.id, candidate_phone="+5511999999999"
        )

    assert result["status"] == "voice_collection_no_consent", result
    fake_orch_cls.assert_not_called()


# ===========================================================================
# SENSOR 4 — plugin_name pins the Fase 0.5 cross-phase gate
# ===========================================================================
def test_plugin_name_is_data_collection_not_wsi():
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )

    plugin = DataCollectionVoicePlugin(
        fields=[{"name": "cpf", "label": "CPF", "field_type": "cpf"}]
    )
    # The Fase 0.5 WSI gate keys off plugin_name == "wsi_screening". Collection
    # must NOT match it, otherwise the WSI completion strategy would fire on a
    # plain data-collection call.
    assert plugin.plugin_name == "data_collection"
    assert plugin.plugin_name != "wsi_screening"


# ===========================================================================
# SENSOR 5 — finalize persists ONLY valid fields, source="voice_collection"
# ===========================================================================
@pytest.mark.asyncio
async def test_finalize_persists_only_valid_fields_source_voice_collection():
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

    transcript = [
        {"role": "assistant", "text": DataCollectionVoicePlugin.RECORDING_NOTICE},
        {"role": "candidate", "text": "123 456 789 09"},  # cpf valid (11 digits)
        {"role": "candidate", "text": "MG-12.345.678"},     # rg valid
        {"role": "candidate", "text": "12"},                # phone invalid -> followup
    ]

    result = await plugin.on_session_finalized(session, db=db, transcript=transcript)

    # phone needs follow-up and is NEVER persisted as answered.
    assert "phone" in result["needs_followup"], result
    assert set(result.get("persisted_fields", [])) == {"cpf", "rg"}, result

    # Canonical model: exactly one DataRequestResponse row per VALID field (2),
    # no row for the needs_followup phone.
    assert db.add.call_count == 2
    db.commit.assert_awaited()

    completed_names = {f["name"] for f in dr.fields_completed}
    assert completed_names == {"cpf", "rg"}, dr.fields_completed
    assert all(
        f.get("source") == "voice_collection" for f in dr.fields_completed
    ), dr.fields_completed
    assert "phone" not in completed_names  # never persisted as answered


# ===========================================================================
# SENSOR 6 — LGPD recording notice is the FIRST utterance
# ===========================================================================
@pytest.mark.asyncio
async def test_recording_notice_is_first_utterance():
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )

    plugin = DataCollectionVoicePlugin(
        fields=[{"name": "cpf", "label": "CPF", "field_type": "cpf", "is_required": True}]
    )
    session = MagicMock()
    session.session_id = "vs-1"
    session.metadata = {}
    await plugin.on_session_initiated(session, db=None)

    first = await plugin.get_next_question(session, db=None)
    assert first == DataCollectionVoicePlugin.RECORDING_NOTICE
    assert "gravada" in first.lower()
    assert "proteção de dados" in first.lower()

    # The next utterance must be a real field prompt, not the notice again.
    second = await plugin.get_next_question(session, db=None)
    assert second is not None
    assert second != DataCollectionVoicePlugin.RECORDING_NOTICE
