"""Tests for Campaign multi-vacancy + Agent Studio wiring (migration 289)."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: CampaignCreate schema accepts job_ids and agent_ids
# ---------------------------------------------------------------------------
def test_campaign_create_schema_accepts_multi_fields():
    from app.api.v1.recruitment_campaigns import CampaignCreate
    job_id1 = str(uuid.uuid4())
    job_id2 = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    c = CampaignCreate(
        name="Campanha Multi",
        job_ids=[job_id1, job_id2],
        agent_ids=[agent_id],
    )
    assert c.job_ids == [job_id1, job_id2]
    assert c.agent_ids == [agent_id]


# ---------------------------------------------------------------------------
# Test 2: CampaignUpdate schema accepts job_ids and agent_ids
# ---------------------------------------------------------------------------
def test_campaign_update_schema_accepts_multi_fields():
    from app.api.v1.recruitment_campaigns import CampaignUpdate
    job_id = str(uuid.uuid4())
    u = CampaignUpdate(job_ids=[job_id], agent_ids=["agent-abc"])
    assert u.job_ids == [job_id]
    assert u.agent_ids == ["agent-abc"]


# ---------------------------------------------------------------------------
# Test 3: RecruitmentCampaign model has job_ids and agent_ids columns
# ---------------------------------------------------------------------------
def test_campaign_model_has_new_columns():
    from lia_models.recruitment_campaign import RecruitmentCampaign
    from sqlalchemy import inspect as sa_inspect
    cols = {c.key for c in sa_inspect(RecruitmentCampaign).mapper.column_attrs}
    assert "job_ids" in cols, "job_ids column missing from model"
    assert "agent_ids" in cols, "agent_ids column missing from model"


# ---------------------------------------------------------------------------
# Test 4: send_outreach_email handler is in execute_action handler_map
# ---------------------------------------------------------------------------
def test_send_outreach_handler_registered():
    from app.domains.recruitment_campaign.domain import RecruitmentCampaignDomain
    domain = RecruitmentCampaignDomain()
    # Build handler_map to verify key exists
    mock_ctx = MagicMock()
    # Access execute_action source to confirm mapping
    import inspect
    src = inspect.getsource(domain.execute_action)
    assert "send_outreach_email" in src, "send_outreach_email not in handler_map"


# ---------------------------------------------------------------------------
# Test 5: CampaignRepository list_by_job_id_in_array exists and fails-closed
# ---------------------------------------------------------------------------
def test_campaign_repo_list_by_job_id_invalid_uuid_returns_empty():
    """Invalid UUID should return [] without crashing (fail-safe)."""
    import asyncio
    from app.repositories.campaign_repository import CampaignRepository

    db = MagicMock()
    repo = CampaignRepository(db)

    async def run():
        return await repo.list_by_job_id_in_array(
            company_id="company-abc",
            job_id="not-a-uuid",
        )

    result = asyncio.get_event_loop().run_until_complete(run())
    assert result == [], "Invalid UUID should return empty list"
