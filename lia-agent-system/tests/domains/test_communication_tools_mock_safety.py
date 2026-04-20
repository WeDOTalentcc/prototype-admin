"""Regression tests for communication tool mock safety — Task #691.

Ensures that send_email, send_whatsapp, and schedule_interview:
  1. ALWAYS return is_mock=True when a candidate is found
  2. ALWAYS return dispatch_status="not_dispatched" (never "dispatched")
  3. NEVER return success=True without the mock_notice field

These tests guard against accidental removal of the mock flags when a developer
connects the real CommunicationDispatcher (ADR-018 / Task #673). When the real
dispatcher is connected, these tests must be updated — they serve as a reminder.
"""
from __future__ import annotations

import uuid
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
    return c


def _make_db_session(candidate: MagicMock | None):
    """Return an async context manager yielding a DB session with the given candidate."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = candidate

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


CANDIDATE_ID = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# send_email — mock safety
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_email_happy_path_is_mock():
    """When candidate is found with email, result must carry is_mock=True."""
    from app.domains.communication.tools.communication_tools import send_email

    with patch("app.domains.communication.tools.communication_tools.AsyncSessionLocal",
               return_value=_make_db_session(_mock_candidate())):
        result = await send_email(
            candidate_id=CANDIDATE_ID,
            subject="Convite para entrevista",
            body="Olá, você tem uma entrevista amanhã.",
        )

    assert result.get("is_mock") is True, "send_email must always return is_mock=True"
    assert result.get("dispatch_status") == "not_dispatched", (
        "send_email must return dispatch_status='not_dispatched' until real dispatcher is wired"
    )
    assert "mock_notice" in result, "send_email must include a mock_notice field"


@pytest.mark.asyncio
async def test_send_email_dispatch_status_never_dispatched():
    """Under no code path should dispatch_status be 'dispatched' while is_mock=True."""
    from app.domains.communication.tools.communication_tools import send_email

    with patch("app.domains.communication.tools.communication_tools.AsyncSessionLocal",
               return_value=_make_db_session(_mock_candidate())):
        result = await send_email(candidate_id=CANDIDATE_ID, subject="Test", body="Test body")

    if result.get("is_mock"):
        assert result.get("dispatch_status") != "dispatched", (
            "If is_mock=True, dispatch_status must NOT be 'dispatched'"
        )


# ---------------------------------------------------------------------------
# send_whatsapp — mock safety
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_whatsapp_happy_path_is_mock():
    """When candidate is found with phone, result must carry is_mock=True."""
    from app.domains.communication.tools.communication_tools import send_whatsapp

    with patch("app.domains.communication.tools.communication_tools.AsyncSessionLocal",
               return_value=_make_db_session(_mock_candidate())):
        result = await send_whatsapp(
            candidate_id=CANDIDATE_ID,
            message="Sua entrevista está confirmada para amanhã.",
        )

    assert result.get("is_mock") is True, "send_whatsapp must always return is_mock=True"
    assert result.get("dispatch_status") == "not_dispatched", (
        "send_whatsapp must return dispatch_status='not_dispatched' until real dispatcher is wired"
    )
    assert "mock_notice" in result, "send_whatsapp must include a mock_notice field"


@pytest.mark.asyncio
async def test_send_whatsapp_dispatch_status_never_dispatched():
    """Under no code path should dispatch_status be 'dispatched' while is_mock=True."""
    from app.domains.communication.tools.communication_tools import send_whatsapp

    with patch("app.domains.communication.tools.communication_tools.AsyncSessionLocal",
               return_value=_make_db_session(_mock_candidate())):
        result = await send_whatsapp(candidate_id=CANDIDATE_ID, message="Test")

    if result.get("is_mock"):
        assert result.get("dispatch_status") != "dispatched", (
            "If is_mock=True, dispatch_status must NOT be 'dispatched'"
        )


# ---------------------------------------------------------------------------
# schedule_interview — mock safety
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_interview_happy_path_is_mock():
    """When candidate is found, schedule_interview must carry is_mock=True."""
    from app.domains.communication.tools.communication_tools import schedule_interview

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = _mock_candidate()

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.communication.tools.communication_tools.AsyncSessionLocal",
               return_value=cm):
        result = await schedule_interview(
            candidate_id=CANDIDATE_ID,
            interview_date="2026-05-15",
            interview_time="14:00",
            interview_type="video",
            job_id=str(uuid.uuid4()),
        )

    assert result.get("is_mock") is True, "schedule_interview must always return is_mock=True"
    assert result.get("dispatch_status") == "not_dispatched", (
        "schedule_interview must return dispatch_status='not_dispatched' until real dispatcher is wired"
    )


@pytest.mark.asyncio
async def test_schedule_interview_invite_sent_is_false():
    """schedule_interview must never claim an invite was actually sent (invite_sent=False)."""
    from app.domains.communication.tools.communication_tools import schedule_interview

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = _mock_candidate()

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.communication.tools.communication_tools.AsyncSessionLocal",
               return_value=cm):
        result = await schedule_interview(
            candidate_id=CANDIDATE_ID,
            interview_date="2026-05-20",
            interview_time="10:00",
            interview_type="presencial",
        )

    if "data" in result:
        assert result["data"].get("invite_sent") is not True, (
            "schedule_interview.data.invite_sent must not be True while dispatch is mocked"
        )
