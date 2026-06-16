"""
Compliance audit tests for bulk_actions and stage_transition_automation
endpoints (Task #311).

Verifies:
- Each candidate processed by a bulk action produces exactly one
  audit_service.log_decision entry (per-candidate trail).
- Free-text fields (rejection reason / message body / notes) are
  intercepted by FairnessGuard and surface as HTTP 422 with the list
  of items that need review.
"""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException


def _make_candidate(cid: str, status: str = "new", active: bool = True):
    return SimpleNamespace(
        id=uuid.UUID(cid),
        status=status,
        is_active=active,
        additional_data={},
        updated_at=None,
        last_activity_at=None,
        last_contacted_at=None,
        communication_consent=True,
        name="Test",
        email="t@example.com",
        current_title=None,
        current_company=None,
    )


def _make_repo(candidates):
    repo = SimpleNamespace()

    async def get_candidate_by_id(cid):
        return candidates.get(str(cid))

    async def commit():
        return None

    async def rollback():
        return None

    async def delete_candidate(c):
        candidates.pop(str(c.id), None)

    repo.get_candidate_by_id = get_candidate_by_id
    repo.commit = commit
    repo.rollback = rollback
    repo.delete_candidate = delete_candidate
    repo.db = None
    return repo


def _make_user():
    return SimpleNamespace(id="user-1", company_id="company-1")


@pytest.mark.asyncio
async def test_bulk_update_status_logs_audit_per_candidate():
    from app.api.v1 import bulk_actions

    cids = [str(uuid.uuid4()) for _ in range(3)]
    candidates = {c: _make_candidate(c, status="new") for c in cids}
    repo = _make_repo(candidates)
    user = _make_user()

    request = bulk_actions.BulkUpdateStatusRequest(
        candidate_ids=cids, new_status="rejected"
    )

    with patch.object(
        bulk_actions.audit_service, "log_decision", new=AsyncMock()
    ) as mock_audit:
        result = await bulk_actions.bulk_update_candidate_status(
            request=request, current_user=user, repo=repo
        )

    assert result.successful == 3
    assert result.failed == 0
    assert mock_audit.await_count == 3
    for call in mock_audit.await_args_list:
        kwargs = call.kwargs
        assert kwargs["agent_name"] == "bulk_actions_api"
        assert kwargs["decision_type"] == "reject_candidate"
        assert kwargs["company_id"] == "company-1"
        assert kwargs["candidate_id"] in cids
        assert any("from_stage: new" in r for r in kwargs["reasoning"])
        assert any("to_stage: rejected" in r for r in kwargs["reasoning"])


@pytest.mark.asyncio
async def test_bulk_assign_job_blocks_discriminatory_notes():
    from app.api.v1 import bulk_actions

    cids = [str(uuid.uuid4())]
    request = bulk_actions.BulkAssignJobRequest(
        candidate_ids=cids,
        job_vacancy_id=str(uuid.uuid4()),
        notes="Apenas homens podem ocupar essa vaga",
    )
    repo = _make_repo({c: _make_candidate(c) for c in cids})
    user = _make_user()

    with patch.object(bulk_actions.audit_service, "log_decision", new=AsyncMock()) as mock_audit:
        with pytest.raises(HTTPException) as exc:
            await bulk_actions.bulk_assign_to_job(
                request=request, current_user=user, repo=repo
            )

    assert exc.value.status_code == 422
    detail = exc.value.detail
    assert detail["error"] == "fairness_blocked"
    assert detail["field"] == "notes"
    assert "needs_review" in detail
    assert mock_audit.await_count == 0


@pytest.mark.asyncio
async def test_bulk_delete_logs_audit_per_candidate():
    from app.api.v1 import bulk_actions

    cids = [str(uuid.uuid4()) for _ in range(2)]
    candidates = {c: _make_candidate(c, status="screening") for c in cids}
    repo = _make_repo(candidates)
    user = _make_user()
    request = bulk_actions.BulkDeleteRequest(candidate_ids=cids, permanent=False)

    with patch.object(bulk_actions.audit_service, "log_decision", new=AsyncMock()) as mock_audit:
        result = await bulk_actions.bulk_delete_candidates(
            request=request, current_user=user, repo=repo
        )

    assert result.successful == 2
    assert mock_audit.await_count == 2
    for call in mock_audit.await_args_list:
        kwargs = call.kwargs
        assert kwargs["decision_type"] == "reject_candidate"
        assert kwargs["agent_name"] == "bulk_actions_api"
        assert kwargs["action"] == "bulk_delete"


@pytest.mark.asyncio
async def test_stage_transition_bulk_predict_logs_audit():
    from app.api.v1 import stage_transition_automation as sta

    cands = [sta.CandidateContext(id=str(uuid.uuid4()), name=f"c{i}") for i in range(3)]
    job = sta.JobContext(id=str(uuid.uuid4()), title="Engineer")
    request = sta.BulkPredictSubStatusRequest(
        candidates=cands,
        from_stage="screening",
        to_stage="rejected",
        job_context=job,
    )

    fake_predict = AsyncMock(return_value={
        "predicted_substatus": "profile_not_aligned",
        "confidence": 0.8,
        "reasoning": "ok",
    })

    with patch.object(sta.stage_transition_service, "predict_substatus", new=fake_predict):
        with patch.object(sta.audit_service, "log_decision", new=AsyncMock()) as mock_audit:
            response = await sta.bulk_predict_substatus(request)

    assert len(response.predictions) == 3
    assert mock_audit.await_count == 3
    for call in mock_audit.await_args_list:
        kwargs = call.kwargs
        assert kwargs["agent_name"] == "automation_engine"
        assert kwargs["decision_type"] == "reject_candidate"


@pytest.mark.asyncio
async def test_stage_transition_bulk_generate_blocks_discriminatory_message():
    from app.api.v1 import stage_transition_automation as sta

    cands = [sta.CandidateContext(id="c-1", name="Alice")]
    job = sta.JobContext(id="job-1", title="Engineer")
    request = sta.BulkGenerateMessagesRequest(
        candidates=cands,
        job_context=job,
        to_stage="rejected",
        substatus_map={"c-1": "profile_not_aligned"},
    )

    fake_generate = AsyncMock(return_value={
        "subject": "x",
        "body": "Olá Alice, infelizmente buscamos apenas homens para essa posição.",
        "metadata": {"generated_by": "lia_claude"},
    })

    with patch.object(sta.stage_transition_service, "generate_message", new=fake_generate):
        with patch.object(sta.audit_service, "log_decision", new=AsyncMock()) as mock_audit:
            with pytest.raises(HTTPException) as exc:
                await sta.bulk_generate_messages(request)

    assert exc.value.status_code == 422
    detail = exc.value.detail
    assert detail["error"] == "fairness_blocked"
    assert "c-1" in detail["needs_review"]
    assert mock_audit.await_count == 0
