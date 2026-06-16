"""
TDD: bulk_start_screening MUST call TriagemSessionService.create_session per candidate.
Ghost write bug: old code writes directly to candidate.additional_data["screening_sessions"] JSONB
instead of calling TriagemSessionService.create_session(), making sessions invisible to the
triagem flow.
"""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_candidate(cid: str, status: str = "new", active: bool = True):
    return SimpleNamespace(
        id=uuid.UUID(cid),
        status=status,
        is_active=active,
        additional_data={},
        updated_at=None,
        last_activity_at=None,
        name="Test User",
        email="test@example.com",
    )


def _make_repo(candidates, job_vacancy=None):
    repo = SimpleNamespace()
    repo.db = AsyncMock()  # AsyncSession mock

    jv = job_vacancy or SimpleNamespace(
        id=uuid.uuid4(),
        title="Eng Role",
        governance_rules={},
        company_id="company-uuid",
    )

    async def get_candidate_by_id(cid):
        return candidates.get(str(cid))

    async def get_job_vacancy_by_id(jid):
        return jv

    async def get_default_company():
        return SimpleNamespace(additional_data={})

    async def get_company_by_id(cid):
        return SimpleNamespace(additional_data={})

    async def get_vacancy_channel_counts(jid):
        return {"organic": 0, "sourcing": 0}

    async def commit():
        return None

    async def rollback():
        return None

    repo.get_candidate_by_id = get_candidate_by_id
    repo.get_job_vacancy_by_id = get_job_vacancy_by_id
    repo.get_default_company = get_default_company
    repo.get_company_by_id = get_company_by_id
    repo.get_vacancy_channel_counts = get_vacancy_channel_counts
    repo.commit = commit
    repo.rollback = rollback
    return repo


def _make_user():
    return SimpleNamespace(id=uuid.UUID("11111111-1111-1111-1111-111111111111"))


@pytest.mark.asyncio
async def test_bulk_start_screening_calls_triagem_service_create_session():
    """bulk_start_screening MUST call TriagemSessionService.create_session for each candidate."""
    from app.api.v1 import bulk_actions

    cids = [str(uuid.uuid4()), str(uuid.uuid4())]
    job_id = str(uuid.uuid4())
    candidates = {c: _make_candidate(c) for c in cids}
    repo = _make_repo(candidates)
    user = _make_user()

    request = bulk_actions.BulkStartScreeningRequest(
        candidate_ids=cids,
        job_vacancy_id=job_id,
        screening_type="text",
    )

    mock_session = SimpleNamespace(id="session-1", token="tok123")

    with patch.object(
        bulk_actions, "TriagemSessionService"
    ) as mock_svc_cls:
        mock_svc_inst = MagicMock()
        mock_svc_inst.create_session = AsyncMock(return_value=mock_session)
        mock_svc_cls.return_value = mock_svc_inst

        result = await bulk_actions.bulk_start_screening(
            request=request,
            current_user=user,
            repo=repo,
            company_id="company-uuid",
        )

    assert mock_svc_inst.create_session.call_count == 2, (
        f"Expected create_session called 2x, got {mock_svc_inst.create_session.call_count}. "
        "Ghost write bug: sessions written to JSONB additional_data instead of TriagemSessionService."
    )
    assert result.successful == 2
    assert result.failed == 0


@pytest.mark.asyncio
async def test_bulk_start_screening_not_ghost_writing_to_jsonb():
    """bulk_start_screening MUST NOT write screening_sessions directly into additional_data JSONB."""
    from app.api.v1 import bulk_actions

    cid = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    candidate = _make_candidate(cid)
    candidates = {cid: candidate}
    repo = _make_repo(candidates)
    user = _make_user()

    request = bulk_actions.BulkStartScreeningRequest(
        candidate_ids=[cid],
        job_vacancy_id=job_id,
    )

    mock_session = SimpleNamespace(id="s1", token="tok")

    with patch.object(bulk_actions, "TriagemSessionService") as mock_svc_cls:
        mock_svc_inst = MagicMock()
        mock_svc_inst.create_session = AsyncMock(return_value=mock_session)
        mock_svc_cls.return_value = mock_svc_inst

        await bulk_actions.bulk_start_screening(
            request=request,
            current_user=user,
            repo=repo,
            company_id="company-uuid",
        )

    # Ghost write would have set candidate.additional_data["screening_sessions"]
    add_data = candidate.additional_data
    assert "screening_sessions" not in add_data, (
        "Ghost write detected: 'screening_sessions' was written into candidate.additional_data. "
        "This creates invisible sessions that never appear in the triagem flow."
    )


@pytest.mark.asyncio
async def test_bulk_start_screening_voice_mode_passed_to_service():
    """voice_mode=True when screening_type='voice'."""
    from app.api.v1 import bulk_actions

    cid = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    candidates = {cid: _make_candidate(cid)}
    repo = _make_repo(candidates)
    user = _make_user()

    request = bulk_actions.BulkStartScreeningRequest(
        candidate_ids=[cid],
        job_vacancy_id=job_id,
        screening_type="voice",
    )

    mock_session = SimpleNamespace(id="s1", token="tok")

    with patch.object(bulk_actions, "TriagemSessionService") as mock_svc_cls:
        mock_svc_inst = MagicMock()
        mock_svc_inst.create_session = AsyncMock(return_value=mock_session)
        mock_svc_cls.return_value = mock_svc_inst

        await bulk_actions.bulk_start_screening(
            request=request,
            current_user=user,
            repo=repo,
            company_id="company-uuid",
        )

    assert mock_svc_inst.create_session.call_count == 1
    call_kwargs = mock_svc_inst.create_session.call_args.kwargs
    assert call_kwargs.get("voice_mode") is True, (
        f"Expected voice_mode=True for screening_type='voice', got: {call_kwargs}"
    )
