"""test_whatsapp_consent_flow.py — Contract tests for Phase 1b WhatsApp consent flow.

Covers:
  1. SIM response creates ConsentRecord with canal="whatsapp"
  2. NÃO response does NOT create ConsentRecord, sets consent_declined status
  3. consent_request message contains required LGPD fields
  4. consent_request with affirmative vacancy includes Art. 11 text
  5. Session transitions to AWAITING_CONSENT after send_consent_request
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call
from types import SimpleNamespace


# ── Minimal stubs to avoid importing full SQLAlchemy stack ────────────────────


class _FakeSession:
    """Minimal SQLAlchemy AsyncSession stub."""
    def __init__(self):
        self._added = []
        self._flushed = False

    def add(self, obj):
        self._added.append(obj)

    async def flush(self):
        self._flushed = True


class _FakeTriagemSession:
    """Minimal TriagemSession ORM stub."""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.status = kwargs.get("status", "invited")
        self.job_id = kwargs.get("job_id", str(uuid.uuid4()))
        self.job_title = kwargs.get("job_title", "Analista de Dados")
        self.candidate_id = kwargs.get("candidate_id", str(uuid.uuid4()))
        self.candidate_name = kwargs.get("candidate_name", "Maria Silva")
        self.company_id = kwargs.get("company_id", str(uuid.uuid4()))
        self.expires_at = kwargs.get("expires_at", datetime.utcnow() + timedelta(days=2))
        self.started_at = None
        self.metadata_json = kwargs.get("metadata_json", {
            "candidate_phone": "+5511999999999",
        })


def _make_send_ok():
    """A WhatsApp provider mock that returns success."""
    provider = MagicMock()
    send_result = SimpleNamespace(success=True, error=None)
    provider.send_text_message = AsyncMock(return_value=send_result)
    return provider


def _make_send_fail():
    """A WhatsApp provider mock that returns failure."""
    provider = MagicMock()
    send_result = SimpleNamespace(success=False, error="Twilio error 500")
    provider.send_text_message = AsyncMock(return_value=send_result)
    return provider


# ── Actual imports (deferred to allow stub injection) ─────────────────────────


@pytest.fixture
def consent_service_cls():
    """Import the consent service (may fail gracefully in CI without full deps)."""
    try:
        from app.domains.recruitment.services.triagem_session_service.whatsapp_consent import (
            TriagemWhatsAppConsentService,
        )
        return TriagemWhatsAppConsentService
    except ImportError as e:
        pytest.skip(f"Skipping — import failed (likely missing env): {e}")


# ── Test 1: SIM response creates ConsentRecord ────────────────────────────────


@pytest.mark.asyncio
async def test_sim_response_creates_consent_record(consent_service_cls):
    """SIM response must create a ConsentRecord with canal='whatsapp'."""
    db = _FakeSession()
    session = _FakeTriagemSession(
        metadata_json={
            "candidate_phone": "+5511999999999",
            "whatsapp_consent": {
                "consent_text": "Você consente?",
                "consent_version": "1.1",
                "sent_at": datetime.utcnow().isoformat(),
            },
        }
    )
    provider = _make_send_ok()

    svc = consent_service_cls(db)
    result = await svc.handle_consent_response(
        session=session,
        message_body="SIM",
        whatsapp_provider=provider,
        candidate_phone="+5511999999999",
    )

    assert result["consent_given"] is True, "SIM should yield consent_given=True"
    assert result["status"] == "started", "Session should advance to 'started'"
    assert len(db._added) == 1, "Exactly one ConsentRecord should be added to session"

    record = db._added[0]
    assert record.canal == "whatsapp", "ConsentRecord.canal must be 'whatsapp'"
    assert record.is_active is True, "Active consent record"
    assert record.consent_type == "consentimento_audio"
    assert "Art. 7" in record.legal_basis
    assert session.status == "started"


# ── Test 2: NÃO response does NOT create ConsentRecord ───────────────────────


@pytest.mark.asyncio
async def test_nao_response_does_not_create_consent_record(consent_service_cls):
    """NÃO response must NOT create a ConsentRecord and must mark session consent_declined."""
    db = _FakeSession()
    session = _FakeTriagemSession(
        metadata_json={
            "candidate_phone": "+5511999999999",
            "whatsapp_consent": {"sent_at": datetime.utcnow().isoformat()},
        }
    )
    provider = _make_send_ok()

    svc = consent_service_cls(db)
    result = await svc.handle_consent_response(
        session=session,
        message_body="NÃO",
        whatsapp_provider=provider,
        candidate_phone="+5511999999999",
    )

    assert result["consent_given"] is False, "NÃO should yield consent_given=False"
    assert result["status"] == "consent_declined"
    assert len(db._added) == 0, "No ConsentRecord should be created when candidate declines"
    assert session.status == "consent_declined"

    # Verify a polite closing message was sent
    provider.send_text_message.assert_called_once()
    sent_text = provider.send_text_message.call_args[0][1]
    assert "privacidadededados@wedotalent.cc" in sent_text


# ── Test 3: consent_request text contains required LGPD fields ────────────────


def test_consent_request_message_contains_required_lgpd_text():
    """consent_request must mention WeDOTalent, 12 meses, DPO email, and SIM/NAO."""
    try:
        from app.templates.communication_templates import WhatsAppTemplates
    except ImportError:
        pytest.skip("templates import failed")

    text = WhatsAppTemplates.consent_request(job_title="Engenheiro de Software")

    assert "WeDOTalent" in text, "Must identify WeDOTalent as data controller (LGPD Art. 7/9)"
    assert "12 meses" in text, "Must state retention period (12 months)"
    assert "privacidadededados@wedotalent.cc" in text, "Must include DPO contact email"
    assert "SIM" in text, "Must include SIM response option"
    assert "NAO" in text.upper(), "Must include NÃO response option"
    # Ensure no f-string interpolation left unresolved
    assert "{" not in text, "No unresolved template vars"


# ── Test 4: Affirmative vacancy includes Art. 11 text ────────────────────────


def test_consent_request_affirmative_includes_art11_text():
    """When is_affirmative=True, consent_request must include Art. 11 reference."""
    try:
        from app.templates.communication_templates import WhatsAppTemplates
    except ImportError:
        pytest.skip("templates import failed")

    text = WhatsAppTemplates.consent_request(
        job_title="Programador",
        is_affirmative=True,
        affirmative_type="pcd",
    )

    assert "Art. 11" in text, "Affirmative vacancy must include Art. 11 §2º reference"
    assert "PCD" in text.upper() or "pcd" in text.lower(), "Must mention PCD condition"


# ── Test 5: AWAITING_CONSENT state set after send_consent_request ─────────────


@pytest.mark.asyncio
async def test_awaiting_consent_state_set_after_screening_start(consent_service_cls):
    """After send_consent_request, session status must be AWAITING_CONSENT."""
    db = _FakeSession()
    session = _FakeTriagemSession(
        status="invited",
        metadata_json={"candidate_phone": "+5511999999999"},
    )
    provider = _make_send_ok()

    svc = consent_service_cls(db)
    result = await svc.send_consent_request(
        session=session,
        whatsapp_provider=provider,
        is_affirmative=False,
    )

    assert result["success"] is True
    assert result["status"] == "awaiting_consent"
    assert session.status == "awaiting_consent"
    assert db._flushed is True

    # Verify message was actually sent
    provider.send_text_message.assert_called_once()
    call_args = provider.send_text_message.call_args[0]
    assert call_args[0] == "+5511999999999"
    consent_text = call_args[1]
    assert "WeDOTalent" in consent_text


# ── Test 6: Normalised SIM variations are accepted ───────────────────────────


@pytest.mark.asyncio
async def test_sim_variations_accepted(consent_service_cls):
    """SIM variations (S, YES, ACEITO) should all create consent records."""
    for sim_variant in ["S", "YES", "ACEITO", "sim", "s", "yes"]:
        db = _FakeSession()
        session = _FakeTriagemSession(
            metadata_json={
                "candidate_phone": "+5511999999999",
                "whatsapp_consent": {
                    "consent_text": "Você consente?",
                    "consent_version": "1.1",
                    "sent_at": datetime.utcnow().isoformat(),
                },
            }
        )
        provider = _make_send_ok()
        svc = consent_service_cls(db)
        result = await svc.handle_consent_response(
            session=session,
            message_body=sim_variant,
            whatsapp_provider=provider,
            candidate_phone="+5511999999999",
        )
        assert result["consent_given"] is True, f"'{sim_variant}' should be accepted as SIM"
        assert len(db._added) == 1, f"ConsentRecord should be created for '{sim_variant}'"


# ── Test 7: send_consent_request fails gracefully when phone is missing ───────


@pytest.mark.asyncio
async def test_send_consent_request_no_phone_returns_error(consent_service_cls):
    """send_consent_request without phone in metadata must return error without raising."""
    db = _FakeSession()
    session = _FakeTriagemSession(metadata_json={})  # no phone
    provider = _make_send_ok()

    svc = consent_service_cls(db)
    result = await svc.send_consent_request(session=session, whatsapp_provider=provider)

    assert result["success"] is False
    assert result["error"] == "no_phone"
    provider.send_text_message.assert_not_called()
