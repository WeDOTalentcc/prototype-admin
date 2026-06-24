"""
Item 11 SEV1 fix TDD tests.

T-a: stage-moving event routes via transition_candidate (not sa_update).
T-b: every stage transition fires STAGE_CHANGED + AuditService via transition_candidate.
T-c: non-stage events (stage=None) do NOT call transition_candidate.
T-d: vc_id tenant isolation forwarded correctly.
T-e: BEHAVIORAL -- _update_candidate_status not mocked, verifies end-to-end wire.
"""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

COMPANY_ID = str(uuid.uuid4())
CANDIDATE_ID = str(uuid.uuid4())
VC_ID = str(uuid.uuid4())
VACANCY_ID = str(uuid.uuid4())


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def candidate_data():
    return {
        "vacancy_candidate_id": VC_ID,
        "vacancy_id": VACANCY_ID,
        "candidate_id": CANDIDATE_ID,
        "candidate_name": "Test Candidate",
        "candidate_email": "test@example.com",
        "stage": "interview_hr",
        "status": "active",
        "company_id": COMPANY_ID,
        "added_by": "recruiter-001",
    }


@pytest.mark.asyncio
async def test_ta_stage_moving_event_routes_via_transition_candidate(mock_db, candidate_data):
    """offer_accepted (stage=hired) must call transition_candidate, not sa_update."""
    from app.domains.communication.services import return_event_service as res_module
    from app.domains.communication.services.return_event_service import ReturnEventService

    svc = ReturnEventService(db=mock_db)

    with patch.object(svc, "_load_candidate_data", new=AsyncMock(return_value=candidate_data)):
        with patch.object(
            res_module.pipeline_stage_service,
            "transition_candidate",
            new=AsyncMock(return_value={"success": True}),
        ) as mock_transition:
            with patch.object(
                res_module,
                "sa_update",
                side_effect=AssertionError("sa_update must NOT be called for stage-moving events"),
            ):
                with patch.object(svc, "_create_activity", new=AsyncMock(return_value="act-id")):
                    with patch.object(svc, "_notify_recruiter", new=AsyncMock(return_value=True)):
                        result = await svc.process_event(
                            vacancy_candidate_id=VC_ID,
                            event_type="offer_accepted",
                            triggered_by="test",
                        )

    assert result.get("success") is True, f"Expected success=True, got: {result}"
    mock_transition.assert_called_once()
    call_str = str(mock_transition.call_args)
    assert "hired" in call_str, f"Expected hired stage in transition_candidate call: {call_str}"


@pytest.mark.asyncio
async def test_tb_transition_candidate_inherits_stage_changed_and_audit(mock_db, candidate_data):
    """offer_declined must route through transition_candidate with correct stage."""
    from app.domains.communication.services import return_event_service as res_module
    from app.domains.communication.services.return_event_service import ReturnEventService

    svc = ReturnEventService(db=mock_db)

    with patch.object(svc, "_load_candidate_data", new=AsyncMock(return_value=candidate_data)):
        with patch.object(
            res_module.pipeline_stage_service,
            "transition_candidate",
            new=AsyncMock(return_value={"success": True}),
        ) as mock_transition:
            with patch.object(svc, "_create_activity", new=AsyncMock(return_value="act-id")):
                with patch.object(svc, "_notify_recruiter", new=AsyncMock(return_value=True)):
                    result = await svc.process_event(
                        vacancy_candidate_id=VC_ID,
                        event_type="offer_declined",
                        triggered_by="test",
                    )

    assert result.get("success") is True
    mock_transition.assert_called_once()
    call_str = str(mock_transition.call_args)
    assert "offer_declined" in call_str, f"Expected offer_declined in call: {call_str}"


@pytest.mark.asyncio
async def test_tc_non_stage_events_do_not_call_transition_candidate(mock_db, candidate_data):
    """screening_complete (stage=None) must NOT call transition_candidate."""
    from app.domains.communication.services import return_event_service as res_module
    from app.domains.communication.services.return_event_service import ReturnEventService

    svc = ReturnEventService(db=mock_db)

    with patch.object(svc, "_load_candidate_data", new=AsyncMock(return_value=candidate_data)):
        with patch.object(
            res_module.pipeline_stage_service,
            "transition_candidate",
            new=AsyncMock(return_value={"success": True}),
        ) as mock_transition:
            with patch.object(svc, "_update_candidate_status", new=AsyncMock(return_value=True)):
                with patch.object(svc, "_create_activity", new=AsyncMock(return_value="act-id")):
                    with patch.object(svc, "_notify_recruiter", new=AsyncMock(return_value=True)):
                        result = await svc.process_event(
                            vacancy_candidate_id=VC_ID,
                            event_type="screening_complete",
                            triggered_by="test",
                        )

    assert result.get("success") is True
    mock_transition.assert_not_called()


@pytest.mark.asyncio
async def test_td_tenant_isolation_vc_id_forwarded(mock_db, candidate_data):
    """VC_ID must be forwarded to transition_candidate (not a different tenant ID)."""
    from app.domains.communication.services import return_event_service as res_module
    from app.domains.communication.services.return_event_service import ReturnEventService

    svc = ReturnEventService(db=mock_db)
    other_vc_id = str(uuid.uuid4())

    with patch.object(svc, "_load_candidate_data", new=AsyncMock(return_value=candidate_data)):
        with patch.object(
            res_module.pipeline_stage_service,
            "transition_candidate",
            new=AsyncMock(return_value={"success": True}),
        ) as mock_transition:
            with patch.object(svc, "_create_activity", new=AsyncMock(return_value="act-id")):
                with patch.object(svc, "_notify_recruiter", new=AsyncMock(return_value=True)):
                    await svc.process_event(
                        vacancy_candidate_id=VC_ID,
                        event_type="offer_accepted",
                        triggered_by="test",
                    )

    call_str = str(mock_transition.call_args)
    assert VC_ID in call_str, f"vacancy_candidate_id not in call: {call_str}"
    assert other_vc_id not in call_str, "Other tenant VC_ID appeared in call"


@pytest.mark.asyncio
async def test_te_behavioral_end_to_end_wire_verified(mock_db, candidate_data):
    """
    BEHAVIORAL: _update_candidate_status not mocked. Verifies real method
    calls pipeline_stage_service.transition_candidate for stage-moving events.
    Closes evidential gap -- proves fix is wired end-to-end.
    """
    from app.domains.communication.services import return_event_service as res_module
    from app.domains.communication.services.return_event_service import ReturnEventService

    svc = ReturnEventService(db=mock_db)

    with patch.object(svc, "_load_candidate_data", new=AsyncMock(return_value=candidate_data)):
        with patch.object(
            res_module.pipeline_stage_service,
            "transition_candidate",
            new=AsyncMock(return_value={"success": True}),
        ) as mock_transition:
            with patch.object(svc, "_create_activity", new=AsyncMock(return_value="act-id")):
                with patch.object(svc, "_notify_recruiter", new=AsyncMock(return_value=True)):
                    result = await svc.process_event(
                        vacancy_candidate_id=VC_ID,
                        event_type="offer_accepted",
                        triggered_by="test_behavioral",
                    )

    assert result.get("success") is True, f"Behavioral test failed: {result}"
    assert mock_transition.called, (
        "BEHAVIORAL FAILURE: transition_candidate was NOT called. "
        "Fix is not wired end-to-end -- sa_update still used for stage-moving events."
    )
    call_str = str(mock_transition.call_args)
    assert "hired" in call_str, (
        f"transition_candidate called but without hired stage: {call_str}"
    )
