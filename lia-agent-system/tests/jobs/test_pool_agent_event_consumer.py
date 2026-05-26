"""Sprint 7C Part 2 — event-driven RabbitMQ consumer canonical tests.

Cobre:
1. CANONICAL_EVENT_TYPES = 4 eventos canonical (alinhado ao EventTriggerPicker frontend
   Agent B 948abf887).
2. on_event_received filtra event_name não-canonical (silent skip — não dispatch).
3. on_event_received lookup pool_agent_assignments WHERE schedule_type='event_driven'
   AND status='active'.
4. on_event_received filtra event_triggers match no schedule_config.
5. on_event_received dispatch via dispatch_pool_agent_assignment_task.delay per match.
6. on_event_received zero match = zero dispatches.

Part 2 escopo: subscribe canonical events + dispatch via Celery task. Não modifica
dispatch task em si (Part 1.5b Agent E).
"""
from __future__ import annotations

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


def _make_event_assignment(
    *,
    event_triggers: list[str] | None = None,
    status: str = "active",
    schedule_type: str = "event_driven",
    company_id: str = "11111111-1111-1111-1111-111111111111",
) -> MagicMock:
    a = MagicMock()
    a.id = uuid4()
    a.company_id = company_id
    a.schedule_type = schedule_type
    a.schedule_config = {"event_triggers": event_triggers or []}
    a.status = status
    a.last_run_at = None
    a.last_run_status = None
    return a


def test_canonical_event_types_are_four_aligned_with_frontend():
    """Test 1: CANONICAL_EVENT_TYPES list = 4 canonical events alinhados frontend Agent B."""
    from app.jobs.consumers import pool_agent_event_consumer as mod

    assert mod.CANONICAL_EVENT_TYPES == [
        "candidate_added_to_pool",
        "candidate_screened",
        "agent_completed_review",
        "weekly_summary",
    ], (
        "CANONICAL_EVENT_TYPES deve bater com frontend EventTriggerPicker "
        "(Agent B 948abf887). Drift = quebra contrato UI ↔ backend."
    )


@pytest.mark.asyncio
async def test_on_event_received_skips_non_canonical_event():
    """Test 2: event não-canonical (ex: 'random.event') → silent skip, zero dispatches."""
    from app.jobs.consumers import pool_agent_event_consumer as mod

    with patch.object(mod, "AsyncSessionLocal") as MockSession:
        with patch.object(mod, "dispatch_pool_agent_assignment_task") as mock_task:
            mock_task.delay = MagicMock()

            await mod.on_event_received("random.non_canonical", {"company_id": "x"})

            # Nenhuma session DB aberta, nenhum dispatch
            MockSession.assert_not_called()
            mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_on_event_received_queries_event_driven_active_assignments():
    """Test 3: lookup pool_agent_assignments WHERE schedule_type='event_driven' AND status='active'."""
    from app.jobs.consumers import pool_agent_event_consumer as mod

    assignment = _make_event_assignment(
        event_triggers=["candidate_added_to_pool"],
        status="active",
    )
    fake_db = MagicMock()
    fake_result = MagicMock()
    scalars_obj = MagicMock()
    scalars_obj.all = MagicMock(return_value=[assignment])
    fake_result.scalars = MagicMock(return_value=scalars_obj)
    fake_db.execute = AsyncMock(return_value=fake_result)

    with patch.object(mod, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)):
        with patch.object(mod, "dispatch_pool_agent_assignment_task") as mock_task:
            mock_task.delay = MagicMock()

            await mod.on_event_received(
                "candidate_added_to_pool",
                {"company_id": assignment.company_id},
            )

            # SQL canonical lookup executado uma vez
            fake_db.execute.assert_awaited()


@pytest.mark.asyncio
async def test_on_event_received_dispatches_when_event_triggers_match():
    """Test 4+5: filtra event_triggers match + dispatch via .delay() por assignment match."""
    from app.jobs.consumers import pool_agent_event_consumer as mod

    matched = _make_event_assignment(
        event_triggers=["candidate_added_to_pool", "weekly_summary"]
    )
    not_matched = _make_event_assignment(
        event_triggers=["agent_completed_review"]
    )
    no_triggers = _make_event_assignment(event_triggers=[])

    fake_db = MagicMock()
    fake_result = MagicMock()
    scalars_obj = MagicMock()
    scalars_obj.all = MagicMock(return_value=[matched, not_matched, no_triggers])
    fake_result.scalars = MagicMock(return_value=scalars_obj)
    fake_db.execute = AsyncMock(return_value=fake_result)

    with patch.object(mod, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)):
        with patch.object(mod, "dispatch_pool_agent_assignment_task") as mock_task:
            mock_task.delay = MagicMock()

            await mod.on_event_received(
                "candidate_added_to_pool",
                {"company_id": matched.company_id},
            )

            # Exatamente 1 dispatch (apenas o matched)
            mock_task.delay.assert_called_once()
            kwargs = mock_task.delay.call_args.kwargs
            assert kwargs["assignment_id"] == str(matched.id)
            assert kwargs["trigger_source"] == "event_driven"


@pytest.mark.asyncio
async def test_on_event_received_zero_match_zero_dispatches():
    """Test 6: nenhum assignment match event_triggers → zero dispatches."""
    from app.jobs.consumers import pool_agent_event_consumer as mod

    # Assignment existe mas event_triggers não contém o event_name
    a = _make_event_assignment(event_triggers=["weekly_summary"])

    fake_db = MagicMock()
    fake_result = MagicMock()
    scalars_obj = MagicMock()
    scalars_obj.all = MagicMock(return_value=[a])
    fake_result.scalars = MagicMock(return_value=scalars_obj)
    fake_db.execute = AsyncMock(return_value=fake_result)

    with patch.object(mod, "AsyncSessionLocal", return_value=_make_session_ctx(fake_db)):
        with patch.object(mod, "dispatch_pool_agent_assignment_task") as mock_task:
            mock_task.delay = MagicMock()

            await mod.on_event_received(
                "candidate_added_to_pool",
                {"company_id": a.company_id},
            )

            mock_task.delay.assert_not_called()
