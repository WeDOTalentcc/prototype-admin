"""Agent J — emit canonical event weekly_summary (scheduled Celery beat).

Tests:
- emit_weekly_summary_impl agrega distinct companies dos pool_agent_runs ultima semana
- emit_weekly_summary_impl emite 1 PlatformEvent canonical per company
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_session_ctx(fake_db):
    class _FakeSessionCtx:
        async def __aenter__(self):
            return fake_db

        async def __aexit__(self, *a):
            return None

    return _FakeSessionCtx()


@pytest.mark.asyncio
async def test_weekly_summary_emits_event_per_company():
    """Task agrega companies + emite weekly_summary canonical 1x per company."""
    from app.jobs.tasks import pool_agents

    company_a = "11111111-1111-1111-1111-111111111111"
    company_b = "22222222-2222-2222-2222-222222222222"

    fake_db = MagicMock()
    fake_db.commit = AsyncMock()

    result = MagicMock()
    result.fetchall = MagicMock(return_value=[(company_a,), (company_b,)])
    fake_db.execute = AsyncMock(return_value=result)

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch.object(pool_agents, "publish_platform_event", new=AsyncMock(return_value=True)) as mock_emit:
        await pool_agents._emit_weekly_summary_impl()

    weekly = [
        c for c in mock_emit.await_args_list
        if c.args and getattr(c.args[0], "event_type", "") == "weekly_summary"
    ]
    assert len(weekly) == 2, f"esperava 2 emits (1 per company), achei {len(weekly)}"
    company_ids_emitted = {c.args[0].company_id for c in weekly}
    assert company_ids_emitted == {company_a, company_b}
    for c in weekly:
        ev = c.args[0]
        assert "week_starting" in ev.payload
        assert "week_ending" in ev.payload


@pytest.mark.asyncio
async def test_weekly_summary_no_companies_no_emit():
    """Sem companies com runs na ultima semana, nao emite nada (graceful)."""
    from app.jobs.tasks import pool_agents

    fake_db = MagicMock()
    fake_db.commit = AsyncMock()
    result = MagicMock()
    result.fetchall = MagicMock(return_value=[])
    fake_db.execute = AsyncMock(return_value=result)

    with patch.object(pool_agents, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)), \
         patch.object(pool_agents, "publish_platform_event", new=AsyncMock(return_value=True)) as mock_emit:
        await pool_agents._emit_weekly_summary_impl()

    weekly = [
        c for c in mock_emit.await_args_list
        if c.args and getattr(c.args[0], "event_type", "") == "weekly_summary"
    ]
    assert weekly == []


def test_beat_schedule_registers_weekly_summary():
    """Beat schedule registra emit-pool-agent-weekly-summary."""
    from app.core.celery_app import celery_app
    from app.jobs.tasks import pool_agents  # noqa: F401 — side effect import

    schedule = celery_app.conf.beat_schedule or {}
    assert "emit-pool-agent-weekly-summary" in schedule
    entry = schedule["emit-pool-agent-weekly-summary"]
    assert entry["task"] == "pool_agents.emit_weekly_summary"
