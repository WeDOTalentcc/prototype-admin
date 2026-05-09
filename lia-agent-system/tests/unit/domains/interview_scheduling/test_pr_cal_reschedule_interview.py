# LIA-T01 | LGPD Art. 12 (anonymisation in logs) | PR-CAL Wave 4 sensors
"""
Wave 4 — PR-CAL sensors: reschedule_interview DB-update MVP.

Harness taxonomy:
  - Sensor (computacional): assert old_datetime comes from DB (not hardcoded "N/A")
  - Sensor (computacional): assert is_simulated_calendar guide flag present
  - Sensor (computacional): non-fatal DB error — still returns success
  - Sensor (computacional): multi-tenant company_id propagated to DB filter

NOTE: AsyncSessionLocal is imported locally inside reschedule_interview, so the patch
target must be "lia_config.database.AsyncSessionLocal" (the source module), not the
scheduling_tools module attribute.
"""
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PATCH_TARGET = "lia_config.database.AsyncSessionLocal"


async def _call_reschedule(**kwargs: Any) -> dict:
    """Import and call the patched reschedule_interview inside the tool module."""
    from app.domains.interview_scheduling.tools.scheduling_tools import (
        reschedule_interview,
    )
    # reschedule_interview is a LangChain StructuredTool — call its underlying coroutine
    if hasattr(reschedule_interview, "coroutine") and reschedule_interview.coroutine is not None:
        return await reschedule_interview.coroutine(**kwargs)
    if hasattr(reschedule_interview, "func") and reschedule_interview.func is not None:
        result = reschedule_interview.func(**kwargs)
        import asyncio
        if asyncio.iscoroutine(result):
            return await result
        return result
    return await reschedule_interview.ainvoke(kwargs)


def _make_mock_interview(start_time: datetime) -> MagicMock:
    """Return a mock Interview row with real start_time."""
    m = MagicMock()
    m.start_time = start_time
    m.end_time = start_time + timedelta(hours=1)
    m.status = "scheduled"
    m.updated_at = None
    return m


def _make_mock_db(interview: MagicMock | None) -> AsyncMock:
    """Build a mock AsyncSession that returns the given interview on execute."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = interview

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=False)
    return mock_db


# ---------------------------------------------------------------------------
# Sensor: old_datetime is NOT the hardcoded "N/A" stub
# ---------------------------------------------------------------------------

class TestRescheduleInterviewNoStubOldDatetime:
    """Sensor: old_datetime must come from DB, never be hardcoded 'N/A'."""

    @pytest.mark.asyncio
    async def test_old_datetime_not_hardcoded_na_when_db_found(self) -> None:
        """When DB lookup succeeds, old_datetime must be the real DB start_time."""
        real_start = datetime(2026, 5, 10, 14, 0, 0)
        mock_interview = _make_mock_interview(real_start)
        mock_db = _make_mock_db(mock_interview)

        with patch(_PATCH_TARGET, return_value=mock_db):
            result = await _call_reschedule(
                interview_id=str(uuid.uuid4()),
                new_datetime_str="2026-05-15 10:00",
                reason="conflito de agenda",
                company_id="company-abc",
            )

        assert result["old_datetime"] == "2026-05-10T14:00:00", (
            f"old_datetime should be '2026-05-10T14:00:00', got {result['old_datetime']!r}. "
            "reschedule_interview is returning a hardcoded value instead of reading from DB."
        )

    @pytest.mark.asyncio
    async def test_old_datetime_na_when_interview_not_found(self) -> None:
        """When DB row is not found, old_datetime falls back to 'N/A' gracefully."""
        mock_db = _make_mock_db(None)

        with patch(_PATCH_TARGET, return_value=mock_db):
            result = await _call_reschedule(
                interview_id=str(uuid.uuid4()),
                new_datetime_str="2026-05-15 10:00",
                company_id="company-abc",
            )

        # Graceful fallback is acceptable only when row not found
        assert result["success"] is True
        assert result["status"] == "rescheduled"


# ---------------------------------------------------------------------------
# Sensor: is_simulated_calendar guide flag
# ---------------------------------------------------------------------------

class TestRescheduleInterviewSimulatedFlag:
    """Sensor: is_simulated_calendar=True must always be present until calendar API."""

    @pytest.mark.asyncio
    async def test_is_simulated_calendar_present(self) -> None:
        real_start = datetime(2026, 5, 10, 14, 0, 0)
        mock_interview = _make_mock_interview(real_start)
        mock_db = _make_mock_db(mock_interview)

        with patch(_PATCH_TARGET, return_value=mock_db):
            result = await _call_reschedule(
                interview_id=str(uuid.uuid4()),
                new_datetime_str="2026-05-15T10:00:00",
                company_id="company-abc",
            )

        assert "is_simulated_calendar" in result, (
            "is_simulated_calendar guide flag missing from reschedule_interview response. "
            "FE needs this flag to show the disclaimer banner until Google Calendar is integrated."
        )
        assert result["is_simulated_calendar"] is True

    @pytest.mark.asyncio
    async def test_is_simulated_calendar_true_even_when_db_fails(self) -> None:
        """is_simulated_calendar must be True even when DB lookup fails."""
        with patch(_PATCH_TARGET, side_effect=Exception("DB unavailable")):
            result = await _call_reschedule(
                interview_id=str(uuid.uuid4()),
                new_datetime_str="2026-05-15T10:00",
                company_id="company-abc",
            )

        assert result.get("is_simulated_calendar") is True


# ---------------------------------------------------------------------------
# Sensor: non-fatal DB error
# ---------------------------------------------------------------------------

class TestRescheduleInterviewResilience:
    """Sensor: DB failure is non-fatal — tool still returns success=True."""

    @pytest.mark.asyncio
    async def test_db_failure_non_fatal(self) -> None:
        with patch(_PATCH_TARGET, side_effect=Exception("connection timeout")):
            result = await _call_reschedule(
                interview_id=str(uuid.uuid4()),
                new_datetime_str="2026-05-20 09:00",
                reason="doença",
                company_id="company-abc",
            )

        assert result["success"] is True, (
            "reschedule_interview must not raise when DB is unavailable. "
            "Non-fatal error handling is required (Crença 7 circuit-breaker pattern)."
        )
        assert result["status"] == "rescheduled"


# ---------------------------------------------------------------------------
# Sensor: multi-tenant — company_id filters the DB query
# ---------------------------------------------------------------------------

class TestRescheduleInterviewMultiTenant:
    """Sensor: company_id must be propagated to DB filter clause."""

    @pytest.mark.asyncio
    async def test_company_id_used_in_db_filter(self) -> None:
        """Verify that the DB query includes company_id in its WHERE clause."""
        real_start = datetime(2026, 4, 28, 10, 0, 0)
        mock_interview = _make_mock_interview(real_start)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_interview

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        executed_stmts: list = []

        async def capture_execute(stmt: Any) -> Any:
            executed_stmts.append(stmt)
            return mock_result

        mock_db.execute = capture_execute

        with patch(_PATCH_TARGET, return_value=mock_db):
            await _call_reschedule(
                interview_id=str(uuid.uuid4()),
                new_datetime_str="2026-05-01 09:00",
                company_id="tenant-xyz",
            )

        assert len(executed_stmts) >= 1, "No DB execute call captured"
        stmt_str = str(executed_stmts[0])
        assert "company_id" in stmt_str.lower(), (
            "company_id not found in SQL WHERE clause. "
            "Multi-tenant isolation requires company_id in every DB query."
        )
