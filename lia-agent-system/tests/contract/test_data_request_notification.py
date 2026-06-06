"""
Sensor: data_request_service.send_notification envia DE VERDADE (não-stub).

Auditoria Paulo 2026-06-06 (épico coleta multi-canal — Sistema B canônico).
Antes era stub: marcava sent_via_email/whatsapp = True SEM despachar.
Agora delega ao CommunicationDispatcher (email) e ao DataRequestWhatsAppService (whatsapp).

Invariantes travadas:
- email sucesso -> sent_via_email=True + results.email.success
- email falha -> NÃO marca enviado (anti-fake-success, REGRA 4 anti-silent)
- candidato sem email -> pula com erro explícito, sem marcar enviado
- whatsapp delega ao serviço canônico (start_collection)
"""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domains.communication.services.data_request_service import DataRequestService

DISPATCHER = "app.domains.communication.services.communication_dispatcher.communication_dispatcher.send_email"
WA_START = "app.domains.communication.services.data_request_whatsapp_service.DataRequestWhatsAppService.start_collection"


def _db(data_request, candidate):
    db = MagicMock()
    db.get = AsyncMock(side_effect=[data_request, candidate])
    db.commit = AsyncMock()
    return db


def _dr(**kw):
    base = dict(
        token="tok123", is_blocking=False, candidate_id=uuid4(),
        sent_via_email=False, email_sent_at=None,
        sent_via_whatsapp=False, whatsapp_sent_at=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_email_real_send_sets_flag_on_success():
    dr = _dr()
    cand = SimpleNamespace(email="c@x.com", phone="+5511999999999", name="Maria Silva")
    db = _db(dr, cand)
    with patch(DISPATCHER, return_value={"success": True, "provider": "mailgun", "message_id": "m1"}) as send_email:
        res = await DataRequestService().send_notification(db, uuid4(), channels=["email"])
    send_email.assert_called_once()
    # portal link no corpo
    _, kwargs = send_email.call_args
    assert "tok123" in kwargs["body_html"]
    assert res["email"]["success"] is True
    assert dr.sent_via_email is True


@pytest.mark.asyncio
async def test_email_failure_does_not_fake_success():
    dr = _dr()
    cand = SimpleNamespace(email="c@x.com", phone=None, name="João")
    db = _db(dr, cand)
    with patch(DISPATCHER, return_value={"success": False, "error": "smtp down"}):
        res = await DataRequestService().send_notification(db, uuid4(), channels=["email"])
    assert res["email"]["success"] is False
    assert res["email"]["error"] == "smtp down"
    assert dr.sent_via_email is False  # anti-fake


@pytest.mark.asyncio
async def test_email_skipped_when_candidate_has_no_email():
    dr = _dr()
    cand = SimpleNamespace(email=None, phone=None, name="X")
    db = _db(dr, cand)
    res = await DataRequestService().send_notification(db, uuid4(), channels=["email"])
    assert res["email"]["success"] is False
    assert res["email"]["error"] == "candidate_no_email"
    assert dr.sent_via_email is False


@pytest.mark.asyncio
async def test_whatsapp_delegates_to_canonical_service():
    dr = _dr()
    cand = SimpleNamespace(email=None, phone="+5511988887777", name="Ana")
    db = _db(dr, cand)
    with patch(WA_START, new=AsyncMock(return_value=True)) as start:
        res = await DataRequestService().send_notification(db, uuid4(), channels=["whatsapp"])
    start.assert_awaited_once()
    assert res["whatsapp"]["success"] is True
    assert dr.sent_via_whatsapp is True


@pytest.mark.asyncio
async def test_whatsapp_skipped_when_no_phone():
    dr = _dr()
    cand = SimpleNamespace(email=None, phone=None, name="Y")
    db = _db(dr, cand)
    res = await DataRequestService().send_notification(db, uuid4(), channels=["whatsapp"])
    assert res["whatsapp"]["success"] is False
    assert res["whatsapp"]["error"] == "candidate_no_phone"
    assert dr.sent_via_whatsapp is False
