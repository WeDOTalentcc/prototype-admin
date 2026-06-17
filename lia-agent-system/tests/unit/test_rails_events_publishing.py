"""
Unit tests for UC-P0-21: ensure the 3 missing Rails events are published
when AI takes pipeline, interview scheduling, and offer actions.

TDD approach:
  1. Tests written first — they FAIL until publish calls are added (red)
  2. Add publish_rails_event calls to the 3 trigger functions (green)
  3. All 3 tests pass
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mapping(data: dict):
    """Return a lightweight MagicMock that behaves like a SQLAlchemy row mapping."""
    m = MagicMock()
    m.__getitem__ = lambda self, k: data[k]
    m.get = lambda k, default=None: data.get(k, default)
    for k, v in data.items():
        setattr(m, k, v)
    return m


# ---------------------------------------------------------------------------
# Test 1: pipeline.moved
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_move_publishes_event():
    """_wrap_move_candidate must call publish_rails_event with event_type='pipeline.moved'."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_move_candidate

    prev_row = _make_mapping({"stage": "applied", "status": "active"})
    execute_result_prev = MagicMock()
    execute_result_prev.mappings.return_value.first.return_value = prev_row

    update_result = MagicMock()
    update_result.rowcount = 1

    session_mock = AsyncMock()
    session_mock.execute = AsyncMock(
        side_effect=[execute_result_prev, update_result]
    )
    session_mock.commit = AsyncMock()

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=session_mock)
    cm.__aexit__ = AsyncMock(return_value=False)

    mock_publish = AsyncMock()

    with patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.AsyncSessionLocal",
        return_value=cm,
    ), patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.publish_rails_event",
        mock_publish,
    ):
        result = await _wrap_move_candidate(
            candidate_id="cand-001",
            target_stage="interview",
            reason="Score above threshold",
            company_id="comp-001",
            job_id="job-001",
            apply_id="apply-001",
        )

    assert result["success"] is True
    mock_publish.assert_called_once()
    call_args = mock_publish.call_args
    kwargs = call_args.kwargs if call_args.kwargs else {}
    args = call_args.args if call_args.args else ()
    event_type = kwargs.get("event_type") or (args[0] if args else None)
    assert event_type == "pipeline.moved", (
        f"Expected event_type='pipeline.moved', got {event_type!r}. "
        "Did you add publish_rails_event to _wrap_move_candidate?"
    )


# ---------------------------------------------------------------------------
# Test 2: interview.scheduled
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_interview_publishes_event():
    """_wrap_schedule_interview must call publish_rails_event with event_type='interview.scheduled'."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_schedule_interview

    cand_row = _make_mapping({"name": "Ana Lima", "email": "ana@test.com"})
    vc_row = _make_mapping({"vacancy_id": "vac-001", "job_title": "Dev Backend"})

    exec_cand = MagicMock()
    exec_cand.mappings.return_value.first.return_value = cand_row

    exec_vc = MagicMock()
    exec_vc.mappings.return_value.first.return_value = vc_row

    exec_insert = MagicMock()

    session_mock = AsyncMock()
    session_mock.execute = AsyncMock(side_effect=[exec_cand, exec_vc, exec_insert])
    session_mock.commit = AsyncMock()

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=session_mock)
    cm.__aexit__ = AsyncMock(return_value=False)

    mock_publish = AsyncMock()

    with patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.AsyncSessionLocal",
        return_value=cm,
    ), patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.publish_rails_event",
        mock_publish,
    ):
        result = await _wrap_schedule_interview(
            candidate_id="cand-001",
            datetime="2026-06-15T10:00:00",
            type="video",
            company_id="comp-001",
            apply_id="apply-001",
        )

    assert result["success"] is True
    mock_publish.assert_called_once()
    call_args = mock_publish.call_args
    kwargs = call_args.kwargs if call_args.kwargs else {}
    args = call_args.args if call_args.args else ()
    event_type = kwargs.get("event_type") or (args[0] if args else None)
    assert event_type == "interview.scheduled", (
        f"Expected event_type='interview.scheduled', got {event_type!r}. "
        "Did you add publish_rails_event to _wrap_schedule_interview?"
    )


# ---------------------------------------------------------------------------
# Test 3: offer.sent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_offer_sent_publishes_event():
    """handle_offer_sent must call publish_rails_event with event_type='offer.sent'."""
    from app.domains.automation.services.automation_handlers import handle_offer_sent

    db_mock = AsyncMock()

    activity_service_mock = AsyncMock()
    activity_service_mock.create_activity = AsyncMock(return_value=None)

    mock_publish = AsyncMock()

    with patch(
        "app.domains.analytics.services.activity_service.ActivityService",
        return_value=activity_service_mock,
    ), patch(
        "app.domains.automation.services.automation_handlers.publish_rails_event",
        mock_publish,
    ):
        result = await handle_offer_sent(
            candidate_id="cand-001",
            vacancy_id="vac-001",
            company_id="comp-001",
            db=db_mock,
            offer_details={"salary": 8000, "channel": "email"},
        )

    assert result.get("action") == "offer_sent"
    mock_publish.assert_called_once()
    call_args = mock_publish.call_args
    kwargs = call_args.kwargs if call_args.kwargs else {}
    args = call_args.args if call_args.args else ()
    event_type = kwargs.get("event_type") or (args[0] if args else None)
    assert event_type == "offer.sent", (
        f"Expected event_type='offer.sent', got {event_type!r}. "
        "Did you add publish_rails_event to handle_offer_sent?"
    )
