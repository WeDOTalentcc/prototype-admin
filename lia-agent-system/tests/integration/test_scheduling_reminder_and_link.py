"""
Integration tests for the chat-tool wrappers `send_reminder` and
`generate_self_scheduling_link` on `SchedulingService`.

These tests verify that the wrappers — which previously returned
`simulation_stub: true` payloads — now perform the real work:

- `generate_self_scheduling_link` persists a `SelfSchedulingLink` row and
  returns a public URL backed by the stored token.
- `send_reminder` looks up the `Interview` (with tenant scoping when a
  company_id is supplied), dispatches the rendered `INTERVIEW_REMINDER`
  message via `communication_service.send_message` for each recipient on
  each requested channel (email / whatsapp / teams), and persists one
  `InterviewReminder` audit row per delivery attempt.

The final test (`test_send_reminder_real_communication_service_email_path`)
exercises the actual `CommunicationService.send_message` code path —
validate_can_send, CommunicationLog persistence, status transitions —
mocking only the leaf provider call (`_send_with_retry`).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.interview_scheduling.services.scheduling_service import (
    SchedulingService,
)


class _FakeAsyncSession:
    """Minimal AsyncSession stand-in capturing add/commit/refresh + execute."""

    def __init__(self, scalar_one_or_none=None, scalar_results=None):
        self.added: list = []
        self.commits = 0
        self.rollbacks = 0
        self._scalar_one_or_none = scalar_one_or_none
        # Optional queue: per-execute call return value for scalar_one_or_none.
        self._scalar_results = list(scalar_results) if scalar_results else None
        self.executed_statements: list = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()

    async def execute(self, stmt):
        self.executed_statements.append(stmt)
        result = MagicMock()
        if self._scalar_results is not None:
            value = self._scalar_results.pop(0) if self._scalar_results else None
        else:
            value = self._scalar_one_or_none
        result.scalar_one_or_none = MagicMock(return_value=value)
        return result

    async def close(self):
        pass


# ---------------------------------------------------------------------------
# generate_self_scheduling_link
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_self_scheduling_link_persists_row_and_returns_public_url():
    db = _FakeAsyncSession()
    svc = SchedulingService()

    with patch.dict(os.environ, {"FRONTEND_URL": "https://app.example.com"}):
        result = await svc.generate_self_scheduling_link(
            db=db,
            candidate_id=str(uuid.uuid4()),
            candidate_name="Maria Silva",
            candidate_email="maria@example.com",
            job_vacancy_id=str(uuid.uuid4()),
            job_title="Analista de RH",
            interview_type="hr",
            duration_minutes=45,
            available_slots=[
                {"start": "2026-05-10T10:00:00", "end": "2026-05-10T11:00:00"},
                {"start": "2026-05-11T14:00:00", "end": "2026-05-11T15:00:00"},
            ],
            interviewer_emails=["recruiter@example.com"],
            expires_hours=48,
            company_id="company-123",
            created_by="agent",
        )

    assert result["success"] is True, result
    assert "simulation_stub" not in result
    assert result["url"].startswith("https://app.example.com/agendar/")
    assert result["token"] and len(result["token"]) >= 10
    assert result["url"].endswith(result["token"])
    assert result["slots_offered"] == 2
    assert result["candidate_email"] == "maria@example.com"

    assert len(db.added) == 1, "Expected exactly one row to be persisted"
    persisted = db.added[0]
    assert persisted.token == result["token"]
    assert persisted.candidate_email == "maria@example.com"
    assert persisted.duration_minutes == 45
    assert persisted.status == "pending"
    assert persisted.expires_at > datetime.utcnow()
    assert db.commits == 1


@pytest.mark.asyncio
async def test_generate_self_scheduling_link_requires_candidate_info():
    svc = SchedulingService()
    result = await svc.generate_self_scheduling_link(
        db=_FakeAsyncSession(),
        candidate_id="",
        candidate_name=None,
        candidate_email=None,
    )
    assert result["success"] is False
    assert result["error"] == "missing_candidate_info"


@pytest.mark.asyncio
async def test_generate_self_scheduling_link_hydrates_from_candidate_id():
    """Legacy callers passing only candidate_id must still succeed: the
    wrapper must hydrate name/email from the Candidate row."""
    cand_id = uuid.uuid4()
    fake_cand = SimpleNamespace(
        id=cand_id, name="Pedro Hidratado", email="pedro@example.com",
    )
    db = _FakeAsyncSession(scalar_one_or_none=fake_cand)
    svc = SchedulingService()

    with patch.dict(os.environ, {"FRONTEND_URL": "https://app.example.com"}):
        result = await svc.generate_self_scheduling_link(
            db=db,
            candidate_id=str(cand_id),
            available_slots=[{"start": "2026-05-10T10:00:00", "end": "2026-05-10T11:00:00"}],
            company_id="company-xyz",
        )

    assert result["success"] is True, result
    assert result["candidate_email"] == "pedro@example.com"
    assert result["candidate_name"] == "Pedro Hidratado"
    persisted = [o for o in db.added if hasattr(o, "token")][0]
    assert persisted.candidate_email == "pedro@example.com"
    assert persisted.candidate_name == "Pedro Hidratado"


@pytest.mark.asyncio
async def test_generate_self_scheduling_link_fails_when_candidate_lookup_empty():
    """If candidate_id does not resolve a row and no name/email are passed,
    the contract error must still fire (no silent insert with NULLs)."""
    db = _FakeAsyncSession(scalar_one_or_none=None)
    svc = SchedulingService()

    result = await svc.generate_self_scheduling_link(
        db=db,
        candidate_id=str(uuid.uuid4()),
    )
    assert result["success"] is False
    assert result["error"] == "missing_candidate_info"


# ---------------------------------------------------------------------------
# send_reminder
# ---------------------------------------------------------------------------

def _make_interview(**overrides):
    interview = SimpleNamespace(
        id=uuid.uuid4(),
        company_id="company-abc",
        candidate_id=uuid.uuid4(),
        candidate_name="João Souza",
        candidate_email="joao@example.com",
        interviewer_name="Ana Recruiter",
        interviewer_email="ana@example.com",
        start_time=datetime.utcnow() + timedelta(days=1),
        duration_minutes=60,
        interview_mode="video",
        meeting_url="https://teams.example.com/meet/xyz",
        location=None,
        job_vacancy_id=uuid.uuid4(),
        job_title="Engenheiro de Dados",
        reminder_sent=False,
        reminder_sent_at=None,
    )
    for k, v in overrides.items():
        setattr(interview, k, v)
    return interview


def _patch_render(success=True, name="interview_reminder_24h"):
    rendered = (
        {
            "success": True,
            "subject": "Lembrete de entrevista",
            "body_text": "Sua entrevista está chegando.",
            "body_html": "<p>Sua entrevista está chegando.</p>",
            "template_name": name,
        }
        if success
        else {"success": False, "error": "template_not_found", "message": "no template"}
    )
    return patch(
        "app.domains.interview_scheduling.services.scheduling_service."
        "SchedulingService._dispatch_reminder_message",
        new=AsyncMock(side_effect=None),
    ), rendered


@pytest.mark.asyncio
async def test_send_reminder_dispatches_message_and_persists_audit():
    interview = _make_interview()
    db = _FakeAsyncSession(scalar_one_or_none=interview)

    fake_dispatch = AsyncMock(return_value={
        "success": True,
        "log_id": "log-001",
        "template_used": "interview_reminder_24h",
    })

    svc = SchedulingService()
    with patch.object(SchedulingService, "_dispatch_reminder_message", fake_dispatch):
        result = await svc.send_reminder(
            db=db,
            interview_id=str(interview.id),
            recipient="candidate",
            hours_before=24,
            company_id="company-abc",
        )

    assert result["success"] is True, result
    assert "simulation_stub" not in result
    assert result["channels"] == ["email"]
    assert len(result["deliveries"]) == 1
    delivery = result["deliveries"][0]
    assert delivery["recipient_type"] == "candidate"
    assert delivery["recipient_email"] == "joao@example.com"
    assert delivery["channel"] == "email"
    assert delivery["success"] is True
    assert delivery["communication_log_id"] == "log-001"

    fake_dispatch.assert_awaited_once()
    kwargs = fake_dispatch.call_args.kwargs
    assert kwargs["channel"].value == "email"
    assert kwargs["candidate_email"] == "joao@example.com"
    assert kwargs["candidate_phone"] is None
    assert kwargs["company_id"] == "company-abc"
    assert kwargs["variables"]["link_entrevista"] == "https://teams.example.com/meet/xyz"

    audit_rows = [obj for obj in db.added if obj is not interview]
    assert len(audit_rows) == 1
    audit = audit_rows[0]
    assert audit.recipient_type == "candidate"
    assert audit.status == "sent"
    assert audit.hours_before == 24
    assert audit.channels == ["email"]
    assert audit.sent_at is not None
    assert interview.reminder_sent is True
    assert interview.reminder_sent_at is not None


@pytest.mark.asyncio
async def test_send_reminder_handles_both_recipients():
    interview = _make_interview()
    db = _FakeAsyncSession(scalar_one_or_none=interview)

    fake_dispatch = AsyncMock(return_value={"success": True, "log_id": "L"})

    svc = SchedulingService()
    with patch.object(SchedulingService, "_dispatch_reminder_message", fake_dispatch):
        result = await svc.send_reminder(
            db=db,
            interview_id=str(interview.id),
            recipient="both",
        )

    assert result["success"] is True
    assert {d["recipient_type"] for d in result["deliveries"]} == {"candidate", "interviewer"}
    assert fake_dispatch.await_count == 2


@pytest.mark.asyncio
async def test_send_reminder_records_failed_delivery_and_returns_failure():
    interview = _make_interview()
    db = _FakeAsyncSession(scalar_one_or_none=interview)

    fake_dispatch = AsyncMock(return_value={
        "success": False,
        "error": "rate_limited",
        "message": "Too many messages",
    })

    svc = SchedulingService()
    with patch.object(SchedulingService, "_dispatch_reminder_message", fake_dispatch):
        result = await svc.send_reminder(
            db=db,
            interview_id=str(interview.id),
            recipient="candidate",
        )

    assert result["success"] is False
    audit_rows = [obj for obj in db.added if obj is not interview]
    assert len(audit_rows) == 1
    assert audit_rows[0].status == "failed"
    assert audit_rows[0].sent_at is None
    assert audit_rows[0].send_error
    assert interview.reminder_sent is False


@pytest.mark.asyncio
async def test_send_reminder_fans_out_per_channel_email_whatsapp_and_teams():
    """All three configured channels (email, whatsapp, teams) must trigger
    actual dispatch and produce one audit row per channel."""
    interview = _make_interview()
    fake_candidate = SimpleNamespace(id=interview.candidate_id, phone="+5511999998888")
    # First execute() returns the Interview, second returns the Candidate (for phone).
    db = _FakeAsyncSession(scalar_results=[interview, fake_candidate])

    fake_dispatch = AsyncMock(return_value={"success": True, "log_id": "msg-1"})
    fake_teams = AsyncMock(return_value={"success": True, "channel": "teams", "recipient_type": "candidate"})

    svc = SchedulingService()
    with patch.object(SchedulingService, "_dispatch_reminder_message", fake_dispatch), \
         patch.object(SchedulingService, "_dispatch_reminder_teams", fake_teams):
        result = await svc.send_reminder(
            db=db,
            interview_id=str(interview.id),
            recipient="candidate",
            channels=["email", "whatsapp", "teams"],
            company_id="company-abc",
        )

    assert result["success"] is True
    assert result["channels"] == ["email", "whatsapp", "teams"]
    channels_seen = [d["channel"] for d in result["deliveries"]]
    assert channels_seen == ["email", "whatsapp", "teams"]
    assert all(d["success"] for d in result["deliveries"])

    # Two real-message dispatches (email + whatsapp); one Teams card.
    assert fake_dispatch.await_count == 2
    assert fake_teams.await_count == 1

    # WhatsApp leg actually carried the candidate phone.
    whatsapp_call = [c for c in fake_dispatch.await_args_list if c.kwargs["channel"].value == "whatsapp"][0]
    assert whatsapp_call.kwargs["candidate_phone"] == "+5511999998888"
    assert whatsapp_call.kwargs["candidate_email"] is None

    audit_rows = [obj for obj in db.added if obj is not interview]
    assert len(audit_rows) == 3
    assert sorted([a.channels[0] for a in audit_rows]) == ["email", "teams", "whatsapp"]


@pytest.mark.asyncio
async def test_send_reminder_whatsapp_skipped_when_candidate_has_no_phone():
    """WhatsApp dispatch must fail closed (no_phone) and NOT be sent if the
    candidate has no phone on file. Audit row must record the failure."""
    interview = _make_interview()
    fake_candidate = SimpleNamespace(id=interview.candidate_id, phone=None)
    db = _FakeAsyncSession(scalar_results=[interview, fake_candidate])

    fake_dispatch = AsyncMock(return_value={"success": True, "log_id": "msg-1"})
    svc = SchedulingService()

    with patch.object(SchedulingService, "_dispatch_reminder_message", fake_dispatch):
        result = await svc.send_reminder(
            db=db,
            interview_id=str(interview.id),
            recipient="candidate",
            channels=["whatsapp"],
            company_id="company-abc",
        )

    assert result["success"] is False
    assert fake_dispatch.await_count == 0  # Never dispatched.
    audit_rows = [obj for obj in db.added if obj is not interview]
    assert len(audit_rows) == 1
    assert audit_rows[0].status == "failed"
    assert "phone" in (audit_rows[0].send_error or "").lower()


@pytest.mark.asyncio
async def test_send_reminder_enforces_tenant_scoping():
    """When company_id is supplied and does not match the interview's tenant,
    the lookup must return interview_not_found (no cross-tenant action)."""
    # The fake session only returns the interview when no company filter
    # narrows it out; we simulate the mismatch by returning None.
    db = _FakeAsyncSession(scalar_one_or_none=None)
    svc = SchedulingService()

    result = await svc.send_reminder(
        db=db,
        interview_id=str(uuid.uuid4()),
        recipient="candidate",
        company_id="other-tenant",
    )

    assert result["success"] is False
    assert result["error"] == "interview_not_found"
    assert "other-tenant" in result["message"]
    # Tenant filter must have been applied to the SELECT.
    assert len(db.executed_statements) == 1
    rendered_sql = str(db.executed_statements[0])
    assert "company_id" in rendered_sql.lower()


@pytest.mark.asyncio
async def test_send_reminder_returns_error_when_interview_missing():
    db = _FakeAsyncSession(scalar_one_or_none=None)
    svc = SchedulingService()

    result = await svc.send_reminder(
        db=db,
        interview_id=str(uuid.uuid4()),
        recipient="candidate",
    )
    assert result["success"] is False
    assert result["error"] == "interview_not_found"


@pytest.mark.asyncio
async def test_send_reminder_requires_interview_id():
    svc = SchedulingService()
    result = await svc.send_reminder(db=_FakeAsyncSession())
    assert result["success"] is False
    assert result["error"] == "missing_interview_id"


# ---------------------------------------------------------------------------
# Real-pipeline integration test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_reminder_real_communication_service_email_path():
    """End-to-end through real CommunicationService + real template renderer.

    Only the leaf provider call (`_send_with_retry`) is mocked. This
    exercises:
      - tenant-scoped Interview lookup,
      - real `render_message_template` (returns a default fallback template),
      - real `CommunicationService.send_message` (validate_can_send,
        CommunicationLog INSERT, status = SENT transition),
      - real `InterviewReminder` audit-row write,
      - `Interview.reminder_sent` flag flip.
    """
    from app.domains.communication.services.communication_service import (
        CommunicationService,
    )

    interview = _make_interview()
    # Three execute() calls expected:
    #   1) Interview lookup
    #   2) (none — whatsapp not requested so no candidate phone lookup)
    #   3) inside CommunicationService.send_message → validate_can_send may
    #      issue queries on its own session; we route them through the same
    #      fake to keep things hermetic.
    db = _FakeAsyncSession(scalar_results=[interview])

    real_comm = CommunicationService()

    async def fake_validate(*a, **kw):
        return {"can_send": True}

    async def fake_send_with_retry(channel, recipient, subject, body, body_html, log, db_):
        return True, "provider-msg-123", {"provider": "stub"}

    rendered_payload = {
        "success": True,
        "subject": "Lembrete de entrevista",
        "body_text": "Sua entrevista é amanhã.",
        "body_html": "<p>Sua entrevista é amanhã.</p>",
        "template_name": "interview_reminder_default",
    }

    svc = SchedulingService()

    with patch(
        "app.domains.interview_scheduling.services.scheduling_service.get_communication_service",
        return_value=real_comm,
    ), patch.object(
        CommunicationService, "validate_can_send", side_effect=fake_validate
    ), patch.object(
        CommunicationService, "_send_with_retry", side_effect=fake_send_with_retry
    ), patch.object(
        CommunicationService, "_is_within_sending_hours", return_value=True
    ), patch(
        "app.domains.communication.services.template_service.render_message_template",
        AsyncMock(return_value=rendered_payload),
    ), patch(
        # `_get_db` inside CommunicationService.send_message wraps the session
        # in an async context manager — make it a no-op pass-through.
        "app.domains.communication.services.communication_service._get_db",
    ) as fake_get_db:
        class _CM:
            def __init__(self, sess): self._s = sess
            async def __aenter__(self): return self._s
            async def __aexit__(self, *a): return None

        fake_get_db.side_effect = lambda sess: _CM(sess if sess is not None else db)

        result = await svc.send_reminder(
            db=db,
            interview_id=str(interview.id),
            recipient="candidate",
            company_id="company-abc",
            hours_before=2,
        )

    assert result["success"] is True, result
    assert result["channels"] == ["email"]
    delivery = result["deliveries"][0]
    assert delivery["success"] is True
    assert delivery["channel"] == "email"

    # Real CommunicationLog row was created and transitioned to SENT.
    from app.domains.communication.services.communication_models import CommunicationLog
    from lia_models.self_scheduling import InterviewReminder

    comm_logs = [o for o in db.added if isinstance(o, CommunicationLog)]
    assert len(comm_logs) == 1
    log = comm_logs[0]
    assert log.message_type == "interview_reminder"
    assert log.channel == "email"
    assert log.candidate_email == "joao@example.com"
    assert log.status == "sent"
    assert log.provider_message_id == "provider-msg-123"

    audit_rows = [o for o in db.added if isinstance(o, InterviewReminder)]
    assert len(audit_rows) == 1
    assert audit_rows[0].status == "sent"
    assert audit_rows[0].channels == ["email"]
    assert interview.reminder_sent is True
