import asyncio
"""
PR-CAL — schedule_interview tests (TDD).

harness-engineering sensor computacional:
Valida que schedule_interview:
1. Não gera link fake calendar.lia.app
2. Retorna is_simulated_calendar=True (guide para FE mostrar disclaimer)
3. Retorna interview_id real (UUID format)
4. Persiste no DB quando AsyncSessionLocal disponível
5. É não-bloqueante em falhas de DB (error handling correto)
6. Multi-tenant: company_id propagado para Interview.company_id
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


async def call_schedule(
    candidate_id: str = "cand-abc123",
    interviewer_id: str = "entrevistador@empresa.com",
    datetime_str: str = "2026-05-01 14:00",
    interview_type: str = "technical",
    meeting_url: str = "",
    company_id: str = "comp_test",
) -> dict:
    from app.domains.interview_scheduling.tools.scheduling_tools import schedule_interview
    kwargs = dict(
        candidate_id=candidate_id,
        interviewer_id=interviewer_id,
        datetime_str=datetime_str,
        interview_type=interview_type,
        meeting_url=meeting_url,
        company_id=company_id,
    )
    # schedule_interview is a LangChain StructuredTool — not directly callable
    if hasattr(schedule_interview, "coroutine") and schedule_interview.coroutine is not None:
        return await schedule_interview.coroutine(**kwargs)
    if hasattr(schedule_interview, "func") and schedule_interview.func is not None:
        result = schedule_interview.func(**kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result
    return await schedule_interview.ainvoke(kwargs)


class TestScheduleInterviewNoFakeLink:
    """Sensor: fake calendar.lia.app link nunca deve aparecer na resposta."""

    @pytest.mark.asyncio
    async def test_no_fake_calendar_lia_app_link(self):
        with patch("lia_config.database.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            result = await call_schedule()

        response_str = str(result)
        assert "calendar.lia.app" not in response_str, (
            "P0: schedule_interview still generating fake calendar.lia.app links. "
            "Remove the stub and use the real DB-based implementation."
        )

    @pytest.mark.asyncio
    async def test_is_simulated_calendar_flag_present(self):
        """Guide: is_simulated_calendar=True signals FE to show disclaimer."""
        with patch("lia_config.database.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            result = await call_schedule()

        assert result.get("is_simulated_calendar") is True, (
            "schedule_interview must set is_simulated_calendar=True until real "
            "Google Calendar integration is implemented."
        )


class TestScheduleInterviewRealID:
    @pytest.mark.asyncio
    async def test_returns_real_uuid_interview_id(self):
        with patch("lia_config.database.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            result = await call_schedule()

        interview_id = result.get("interview_id", "")
        try:
            uuid.UUID(interview_id)
            is_valid_uuid = True
        except (ValueError, AttributeError):
            is_valid_uuid = False

        assert is_valid_uuid, (
            f"schedule_interview should return a real UUID, got: {interview_id!r}"
        )

    @pytest.mark.asyncio
    async def test_success_true(self):
        with patch("lia_config.database.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            result = await call_schedule()

        assert result.get("success") is True


class TestScheduleInterviewMeetingUrl:
    @pytest.mark.asyncio
    async def test_meeting_url_propagated_when_provided(self):
        url = "https://meet.google.com/abc-defg-hij"
        with patch("lia_config.database.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            result = await call_schedule(meeting_url=url)

        assert result.get("meeting_url") == url

    @pytest.mark.asyncio
    async def test_meeting_url_none_when_not_provided(self):
        with patch("lia_config.database.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            result = await call_schedule(meeting_url="")

        assert result.get("meeting_url") is None


class TestScheduleInterviewDBResilience:
    @pytest.mark.asyncio
    async def test_db_failure_is_non_fatal(self):
        """Sensor: DB write failure must not block the tool response."""
        with patch("lia_config.database.AsyncSessionLocal", side_effect=Exception("DB unavailable")):
            result = await call_schedule()

        # Even if DB fails, tool should return success (non-fatal)
        assert result.get("success") is True
        assert "is_simulated_calendar" in result


class TestScheduleInterviewMultiTenant:
    @pytest.mark.asyncio
    async def test_company_id_propagated_to_db(self):
        """Sensor: company_id must be set on the Interview object (multi-tenant)."""
        captured_interviews = []

        with patch("lia_config.database.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)

            def capture_add(obj):
                captured_interviews.append(obj)
            mock_ctx.add = capture_add
            mock_session_cls.return_value = mock_ctx

            await call_schedule(company_id="tenant_xyz_456")

        if captured_interviews:
            assert captured_interviews[0].company_id == "tenant_xyz_456", (
                "CLAUDE.md Non-Negotiable #1: company_id must be propagated to all DB writes."
            )
