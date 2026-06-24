"""
GAP-03-008: HITL gate em bulk_delete + bulk_assign — TDD RED→GREEN
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID


def _make_bulk_delete_request(candidate_ids=None, permanent=False):
    from app.api.v1.bulk_actions import BulkDeleteRequest
    return BulkDeleteRequest(
        candidate_ids=candidate_ids or ["00000000-0000-0000-0000-000000000001"],
        permanent=permanent,
    )


def _make_bulk_assign_request(candidate_ids=None, job_vacancy_id=None):
    from app.api.v1.bulk_actions import BulkAssignJobRequest
    return BulkAssignJobRequest(
        candidate_ids=candidate_ids or ["00000000-0000-0000-0000-000000000001"],
        job_vacancy_id=job_vacancy_id or "00000000-0000-0000-0000-000000000002",
    )


# ──────────────────────────────────────────────────────────────────────────────
# bulk_delete HITL gate
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bulk_delete_hitl_gate_blocks_when_gate_on():
    """LIA_HITL_GATE=on → bulk_delete retorna needs_confirmation antes de deletar."""
    from app.api.v1.bulk_actions import bulk_delete_candidates
    from fastapi.responses import JSONResponse

    req = _make_bulk_delete_request()
    mock_user = MagicMock(); mock_user.id = "user-1"
    mock_repo = AsyncMock()
    mock_repo.get_candidate_by_id = AsyncMock(return_value=MagicMock())

    with patch.dict(os.environ, {"LIA_HITL_GATE": "true"}):
        result = await bulk_delete_candidates(
            request=req,
            current_user=mock_user,
            repo=mock_repo,
            company_id="comp-1",
        )

    # Should be JSONResponse with 202 and needs_confirmation
    assert isinstance(result, JSONResponse)
    import json
    body = json.loads(result.body)
    assert body.get("needs_confirmation") is True
    assert result.status_code == 202
    # Repo must NOT have been called (no delete happened)
    mock_repo.get_candidate_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_bulk_delete_hitl_gate_dormant_when_gate_off():
    """LIA_HITL_GATE=off (default) → bulk_delete executa normalmente."""
    from app.api.v1.bulk_actions import bulk_delete_candidates

    mock_candidate = MagicMock()
    mock_candidate.is_active = True
    mock_repo = AsyncMock()
    mock_repo.get_candidate_by_id = AsyncMock(return_value=mock_candidate)
    mock_repo.commit = AsyncMock()

    mock_user = MagicMock(); mock_user.id = "user-1"

    with patch.dict(os.environ, {"LIA_HITL_GATE": ""}):
        with patch("app.api.v1.bulk_actions.audit_service", AsyncMock()):
            result = await bulk_delete_candidates(
                request=_make_bulk_delete_request(),
                current_user=mock_user,
                repo=mock_repo,
                company_id="comp-1",
            )

    # Should NOT be a JSONResponse — should be a BulkOperationResult
    from fastapi.responses import JSONResponse
    assert not isinstance(result, JSONResponse)
    # repo WAS called
    mock_repo.get_candidate_by_id.assert_awaited_once()


# ──────────────────────────────────────────────────────────────────────────────
# bulk_assign HITL gate
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bulk_assign_hitl_gate_blocks_when_gate_on():
    """LIA_HITL_GATE=on → bulk_assign retorna needs_confirmation antes de atribuir."""
    from app.api.v1.bulk_actions import bulk_assign_to_job
    from fastapi.responses import JSONResponse

    req = _make_bulk_assign_request()
    mock_user = MagicMock(); mock_user.id = "user-1"
    mock_repo = AsyncMock()
    mock_repo.get_job_vacancy_by_id = AsyncMock(return_value=MagicMock())
    mock_repo.get_candidate_by_id = AsyncMock(return_value=MagicMock())

    with patch.dict(os.environ, {"LIA_HITL_GATE": "true"}):
        result = await bulk_assign_to_job(
            request=req,
            current_user=mock_user,
            repo=mock_repo,
            company_id="comp-1",
        )

    assert isinstance(result, JSONResponse)
    import json
    body = json.loads(result.body)
    assert body.get("needs_confirmation") is True
    assert result.status_code == 202
    mock_repo.get_candidate_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_bulk_assign_hitl_gate_dormant_when_gate_off():
    """LIA_HITL_GATE=off (default) → bulk_assign executa normalmente."""
    from app.api.v1.bulk_actions import bulk_assign_to_job

    mock_vacancy = MagicMock()
    mock_vacancy.company_id = "comp-1"
    mock_candidate = MagicMock()
    mock_candidate.additional_data = {}
    mock_candidate.updated_at = None

    mock_repo = AsyncMock()
    mock_repo.get_job_vacancy_by_id = AsyncMock(return_value=mock_vacancy)
    mock_repo.get_candidate_by_id = AsyncMock(return_value=mock_candidate)
    mock_repo.commit = AsyncMock()

    mock_user = MagicMock(); mock_user.id = "user-1"

    with patch.dict(os.environ, {"LIA_HITL_GATE": ""}):
        with patch("app.api.v1.bulk_actions.audit_service", AsyncMock()):
            result = await bulk_assign_to_job(
                request=_make_bulk_assign_request(),
                current_user=mock_user,
                repo=mock_repo,
                company_id="comp-1",
            )

    from fastapi.responses import JSONResponse
    assert not isinstance(result, JSONResponse)
    mock_repo.get_job_vacancy_by_id.assert_awaited_once()
