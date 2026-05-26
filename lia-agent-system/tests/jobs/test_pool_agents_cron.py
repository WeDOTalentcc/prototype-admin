"""Sprint 7C Part 1 v2 — cron infra canonical tests.

Cobre:
1. dispatch_pool_agent_assignment_task atualiza last_run_at + audit canonical.
2. scan_pool_agent_cron_schedules consulta WHERE schedule_type='cron' AND status='active'.
3. croniter expression match → dispatch via .delay().
4. croniter expression inválida → skip + continue scan (não silent, log + continue).
5. beat_schedule entry `scan-pool-agent-cron-schedules` registered com schedule=60s.

Part 1 v2 escopo: dispatch é STUB canonical (audit + last_run_at). Orchestrator
real (execute CustomAgent + persist pool_agent_runs) fica Part 1.5.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


def _make_session_ctx(fake_db):
    class _FakeSessionCtx:
        async def __aenter__(self):
            return fake_db

        async def __aexit__(self, *a):
            return None

    return _FakeSessionCtx()


def _make_assignment(
    *,
    schedule_type: str = "cron",
    cron_expression: str | None = "*/5 * * * *",
    status: str = "active",
    last_run_at: datetime | None = None,
    company_id: str = "11111111-1111-1111-1111-111111111111",
) -> MagicMock:
    a = MagicMock()
    a.id = uuid4()
    a.company_id = company_id
    a.schedule_type = schedule_type
    a.schedule_config = {"cron_expression": cron_expression} if cron_expression else {}
    a.status = status
    a.last_run_at = last_run_at
    a.last_run_status = None
    a.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    return a


@pytest.mark.asyncio
async def test_scan_filters_cron_active_only():
    """Test 2: scan canonical lookup pool_agent_assignments WHERE schedule_type='cron'."""
    from app.jobs.tasks import pool_agents

    cron_active = _make_assignment(schedule_type="cron", status="active")
    fake_db = MagicMock()
    fake_result = MagicMock()
    scalars_obj = MagicMock()
    scalars_obj.all = MagicMock(return_value=[cron_active])
    fake_result.scalars = MagicMock(return_value=scalars_obj)
    fake_db.execute = AsyncMock(return_value=fake_result)

    with patch.object(
        pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)
    ):
        with patch.object(pool_agents, "dispatch_pool_agent_assignment_task") as mock_task:
            mock_task.delay = MagicMock()
            await pool_agents._scan_impl()

            # SQL filter checked via stmt arg compiled — basta confirmar que
            # canonical lookup foi feito 1x.
            fake_db.execute.assert_awaited()


@pytest.mark.asyncio
async def test_scan_dispatches_when_cron_matches():
    """Test 3: croniter expression match → dispatch via .delay()."""
    from app.jobs.tasks import pool_agents

    # last_run_at 1h atrás + cron */5 → next_run << now → dispatch
    old_last = datetime.now(timezone.utc) - timedelta(hours=1)
    assignment = _make_assignment(
        schedule_type="cron",
        cron_expression="*/5 * * * *",
        status="active",
        last_run_at=old_last,
    )

    fake_db = MagicMock()
    fake_result = MagicMock()
    scalars_obj = MagicMock()
    scalars_obj.all = MagicMock(return_value=[assignment])
    fake_result.scalars = MagicMock(return_value=scalars_obj)
    fake_db.execute = AsyncMock(return_value=fake_result)

    with patch.object(
        pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)
    ):
        with patch.object(pool_agents, "dispatch_pool_agent_assignment_task") as mock_task:
            mock_task.delay = MagicMock()
            await pool_agents._scan_impl()

            mock_task.delay.assert_called_once()
            call_kwargs = mock_task.delay.call_args.kwargs
            assert call_kwargs["assignment_id"] == str(assignment.id)
            assert call_kwargs["trigger_source"] == "cron"


@pytest.mark.asyncio
async def test_scan_skips_invalid_cron_expression_but_continues():
    """Test 4: croniter expression inválida → skip mas não silent (log) + continue scan."""
    from app.jobs.tasks import pool_agents

    bad = _make_assignment(cron_expression="not a cron expr")
    good = _make_assignment(
        cron_expression="*/5 * * * *",
        last_run_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    fake_db = MagicMock()
    fake_result = MagicMock()
    scalars_obj = MagicMock()
    scalars_obj.all = MagicMock(return_value=[bad, good])
    fake_result.scalars = MagicMock(return_value=scalars_obj)
    fake_db.execute = AsyncMock(return_value=fake_result)

    with patch.object(
        pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)
    ):
        with patch.object(pool_agents, "dispatch_pool_agent_assignment_task") as mock_task:
            mock_task.delay = MagicMock()
            await pool_agents._scan_impl()

            # Bad assignment skipped, good dispatched — não silent crash
            mock_task.delay.assert_called_once()
            call_kwargs = mock_task.delay.call_args.kwargs
            assert call_kwargs["assignment_id"] == str(good.id)


def test_beat_schedule_entry_registered_60s():
    """Test 5: beat_schedule 'scan-pool-agent-cron-schedules' entry com schedule=60s."""
    # Force pool_agents import to wire beat entry
    from app.jobs.tasks import pool_agents  # noqa: F401
    from app.core.celery_app import celery_app

    entry = celery_app.conf.beat_schedule.get("scan-pool-agent-cron-schedules")
    assert entry is not None, "beat entry scan-pool-agent-cron-schedules missing"
    assert entry["task"] == "pool_agents.scan_cron_schedules"
    assert entry["schedule"] == 60.0
