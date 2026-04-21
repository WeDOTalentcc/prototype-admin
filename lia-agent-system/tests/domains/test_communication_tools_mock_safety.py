"""Regression tests for communication tools real-dispatch wiring — Task #693.

Ensures that send_email, send_whatsapp, and schedule_interview:
  1. Call the real CommunicationDispatcher (no `is_mock=True` flag in happy path)
  2. Return `dispatch_status="dispatched"` when the provider succeeds
  3. Return `dispatch_status="failed"` and `success=False` when provider errors
  4. schedule_interview persists a real Interview row via SchedulingService
"""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_candidate(*, has_email: bool = True) -> MagicMock:
    """Return a mock Candidate ORM object."""
    c = MagicMock()
    c.name = "Maria Candidata"
    c.email = "maria@example.com" if has_email else None
    c.phone = "+5511999999999" if has_email else None
    c.first_name = "Maria"
    c.company_id = uuid.uuid4()
    return c


def _make_db_session(candidate: MagicMock | None, job: MagicMock | None = None):
    """Return an async context manager yielding a DB session.

    Each call to `execute()` returns a fresh result so that a candidate lookup
    followed by a job lookup both succeed.
    """
    results = [candidate, job]

    async def _execute(*_a, **_kw):
        idx = min(len(results) - 1, _execute.call_count)
        _execute.call_count += 1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = results[idx]
        return mock_result
    _execute.call_count = 0

    mock_session = AsyncMock()
    mock_session.execute = _execute
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


CANDIDATE_ID = str(uuid.uuid4())
JOB_ID = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# send_email — real dispatch wiring
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_email_calls_real_dispatcher_on_success():
    from app.domains.communication.tools.communication_tools import send_email
    from app.domains.communication.services import communication_dispatcher as dispatcher_module

    dispatch_mock = MagicMock(return_value={
        "success": True,
        "message_id": "mg-abc123",
        "mock": False,
        "provider": "mailgun",
        "channel": "email",
        "recipient": "maria@example.com",
        "timestamp": datetime.utcnow().isoformat(),
    })

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(_mock_candidate()),
    ), patch.object(dispatcher_module.communication_dispatcher, "send_email", dispatch_mock):
        result = await send_email(
            candidate_id=CANDIDATE_ID,
            subject="Convite para entrevista",
            body="Olá, você tem uma entrevista amanhã.",
        )

    assert result["success"] is True
    assert result["dispatch_status"] == "dispatched"
    assert result.get("is_mock") is not True
    assert "mock_notice" not in result
    assert result["data"]["message_id"] == "mg-abc123"
    assert result["data"]["provider"] == "mailgun"
    assert dispatch_mock.called
    kwargs = dispatch_mock.call_args.kwargs
    assert kwargs["to_email"] == "maria@example.com"
    assert kwargs["subject"] == "Convite para entrevista"


@pytest.mark.asyncio
async def test_send_email_returns_failed_when_provider_errors():
    from app.domains.communication.tools.communication_tools import send_email
    from app.domains.communication.services import communication_dispatcher as dispatcher_module

    dispatch_mock = MagicMock(return_value={
        "success": False,
        "error": "mailgun status 500",
        "provider": "none",
    })

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(_mock_candidate()),
    ), patch.object(dispatcher_module.communication_dispatcher, "send_email", dispatch_mock):
        result = await send_email(
            candidate_id=CANDIDATE_ID, subject="Test", body="Body",
        )

    assert result["success"] is False
    assert result["dispatch_status"] == "failed"
    assert "mailgun status 500" in result["error"]


@pytest.mark.asyncio
async def test_send_email_requires_subject_and_body():
    from app.domains.communication.tools.communication_tools import send_email

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(_mock_candidate()),
    ):
        result = await send_email(candidate_id=CANDIDATE_ID)

    assert result["success"] is False
    assert result["error"] == "missing_subject_or_body"


@pytest.mark.asyncio
async def test_load_email_template_refuses_cross_tenant_uuid():
    """Tenant isolation: a template owned by company A must not be returned to company B."""
    from app.domains.communication.tools.communication_tools import _load_email_template

    foreign_template = MagicMock()
    foreign_template.id = uuid.uuid4()
    foreign_template.company_id = "company-A"
    foreign_template.is_system = False
    foreign_template.subject = "secret"
    foreign_template.body_html = "<p>secret</p>"
    foreign_template.body_text = "secret"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = foreign_template
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    rendered = await _load_email_template(
        mock_db, str(foreign_template.id), variables={}, company_id="company-B"
    )
    assert rendered is None


@pytest.mark.asyncio
async def test_send_email_with_template_id_renders_and_dispatches():
    """When template_id is provided, subject/body are not required."""
    from app.domains.communication.tools import communication_tools as ct
    from app.domains.communication.services import communication_dispatcher as dispatcher_module

    dispatch_mock = MagicMock(return_value={
        "success": True, "message_id": "mg-tpl",
        "mock": False, "provider": "mailgun",
    })

    async def _fake_loader(_db, template_id, variables=None, company_id=None):
        return {
            "subject": f"Olá {variables.get('candidate_name', '')}",
            "body_html": "<p>Olá {{candidate_name}}</p>".replace(
                "{{candidate_name}}", str(variables.get("candidate_name", ""))
            ),
            "body_text": "Olá",
        }

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(_mock_candidate()),
    ), patch.object(dispatcher_module.communication_dispatcher, "send_email", dispatch_mock), \
         patch.object(ct, "_load_email_template", _fake_loader):
        result = await ct.send_email(
            candidate_id=CANDIDATE_ID,
            template_id="screening_passed",
        )

    assert result["success"] is True
    assert result["dispatch_status"] == "dispatched"
    assert result["data"]["template_used"] is True
    assert dispatch_mock.called
    kwargs = dispatch_mock.call_args.kwargs
    assert "Maria" in kwargs["subject"]
    assert "Olá" in kwargs["body_html"]


@pytest.mark.asyncio
async def test_send_bulk_email_works_with_template_only():
    """Regression: send_bulk_email passes only template_id and must succeed."""
    from app.domains.communication.tools import communication_tools as ct
    from app.domains.communication.services import communication_dispatcher as dispatcher_module

    dispatch_mock = MagicMock(return_value={
        "success": True, "message_id": "mg-bulk",
        "mock": False, "provider": "mailgun",
    })

    async def _fake_loader(_db, template_id, variables=None, company_id=None):
        return {
            "subject": "Bulk subject",
            "body_html": "<p>Bulk body</p>",
            "body_text": "Bulk body",
        }

    cids = [str(uuid.uuid4()), str(uuid.uuid4())]

    with patch(
        "app.core.database.AsyncSessionLocal",
        side_effect=lambda: _make_db_session(_mock_candidate()),
    ), patch.object(dispatcher_module.communication_dispatcher, "send_email", dispatch_mock), \
         patch.object(ct, "_load_email_template", _fake_loader):
        result = await ct.send_bulk_email(candidate_ids=cids, template_id="any")

    assert result["success"] is True
    assert result["data"]["success_count"] == 2
    assert dispatch_mock.call_count == 2


# ---------------------------------------------------------------------------
# send_whatsapp — real dispatch wiring
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_whatsapp_calls_real_dispatcher_on_success():
    from app.domains.communication.tools.communication_tools import send_whatsapp
    from app.domains.communication.services import communication_dispatcher as dispatcher_module

    dispatch_mock = MagicMock(return_value={
        "success": True,
        "message_id": "SM12345",
        "mock": False,
        "channel": "whatsapp",
        "recipient": "+5511999999999",
        "timestamp": datetime.utcnow().isoformat(),
    })

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(_mock_candidate()),
    ), patch.object(dispatcher_module.communication_dispatcher, "send_whatsapp", dispatch_mock):
        result = await send_whatsapp(
            candidate_id=CANDIDATE_ID,
            message="Sua entrevista está confirmada para amanhã.",
        )

    assert result["success"] is True
    assert result["dispatch_status"] == "dispatched"
    assert result.get("is_mock") is not True
    assert "mock_notice" not in result
    assert result["data"]["message_id"] == "SM12345"
    assert dispatch_mock.called
    assert dispatch_mock.call_args.kwargs["to_phone"] == "+5511999999999"


@pytest.mark.asyncio
async def test_send_whatsapp_returns_failed_when_provider_errors():
    from app.domains.communication.tools.communication_tools import send_whatsapp
    from app.domains.communication.services import communication_dispatcher as dispatcher_module

    dispatch_mock = MagicMock(return_value={
        "success": False,
        "error": "Twilio error 21610",
    })

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(_mock_candidate()),
    ), patch.object(dispatcher_module.communication_dispatcher, "send_whatsapp", dispatch_mock):
        result = await send_whatsapp(candidate_id=CANDIDATE_ID, message="hello")

    assert result["success"] is False
    assert result["dispatch_status"] == "failed"
    assert "Twilio error 21610" in result["error"]


# ---------------------------------------------------------------------------
# schedule_interview — real DB record + invite email
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_interview_creates_real_db_record_and_sends_invite():
    from app.domains.communication.tools.communication_tools import schedule_interview
    from app.domains.communication.services import communication_dispatcher as dispatcher_module
    from app.domains.interview_scheduling.services import scheduling_service as scheduling_module

    candidate = _mock_candidate()
    job = MagicMock()
    job.title = "Engenheira de Software"

    fake_interview = MagicMock()
    fake_interview.id = uuid.uuid4()

    create_mock = AsyncMock(return_value=fake_interview)
    dispatch_mock = MagicMock(return_value={
        "success": True,
        "message_id": "mg-xyz",
        "mock": False,
        "provider": "mailgun",
    })

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(candidate, job),
    ), patch.object(scheduling_module.SchedulingService, "create_interview", create_mock), \
         patch.object(dispatcher_module.communication_dispatcher, "send_email", dispatch_mock):
        result = await schedule_interview(
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            interview_type="video",
            datetime_str="2026-05-15T14:00:00",
        )

    assert result["success"] is True
    assert result["dispatch_status"] == "dispatched"
    assert result.get("is_mock") is not True
    assert result["data"]["interview_id"] == str(fake_interview.id)
    assert result["data"]["invite_sent"] is True
    assert create_mock.called
    assert dispatch_mock.called


@pytest.mark.asyncio
async def test_schedule_interview_attaches_ics_to_invite_email():
    from app.domains.communication.tools.communication_tools import schedule_interview
    from app.domains.communication.services import communication_dispatcher as dispatcher_module
    from app.domains.interview_scheduling.services import scheduling_service as scheduling_module

    candidate = _mock_candidate()
    fake_interview = MagicMock()
    fake_interview.id = uuid.uuid4()

    create_mock = AsyncMock(return_value=fake_interview)
    ics_payload = "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR"
    ics_mock = MagicMock(return_value=ics_payload)
    dispatch_mock = MagicMock(return_value={
        "success": True, "message_id": "mg-ics", "mock": False, "provider": "mailgun",
    })

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(candidate, None),
    ), patch.object(scheduling_module.SchedulingService, "create_interview", create_mock), \
         patch.object(scheduling_module.SchedulingService, "generate_ics_content", ics_mock), \
         patch.object(dispatcher_module.communication_dispatcher, "send_email", dispatch_mock):
        result = await schedule_interview(
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            interview_type="video",
            datetime_str="2026-06-01T15:00:00",
        )

    assert result["success"] is True
    assert result["data"]["ics_attached"] is True
    kwargs = dispatch_mock.call_args.kwargs
    attachments = kwargs.get("attachments")
    assert attachments and len(attachments) == 1
    assert attachments[0]["filename"] == "invite.ics"
    assert "VCALENDAR" in attachments[0]["content"]


@pytest.mark.asyncio
async def test_schedule_interview_invite_failure_does_not_fail_scheduling():
    from app.domains.communication.tools.communication_tools import schedule_interview
    from app.domains.communication.services import communication_dispatcher as dispatcher_module
    from app.domains.interview_scheduling.services import scheduling_service as scheduling_module

    candidate = _mock_candidate()
    fake_interview = MagicMock()
    fake_interview.id = uuid.uuid4()

    create_mock = AsyncMock(return_value=fake_interview)
    dispatch_mock = MagicMock(return_value={"success": False, "error": "smtp down"})

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_make_db_session(candidate, None),
    ), patch.object(scheduling_module.SchedulingService, "create_interview", create_mock), \
         patch.object(dispatcher_module.communication_dispatcher, "send_email", dispatch_mock):
        result = await schedule_interview(
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            interview_type="video",
            datetime_str="2026-05-20T10:00:00",
        )

    assert result["success"] is True
    assert result["data"]["invite_sent"] is False
    assert "smtp down" in (result["data"].get("invite_error") or "")
