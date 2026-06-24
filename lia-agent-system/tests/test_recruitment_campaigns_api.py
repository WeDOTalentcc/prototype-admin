"""Tests for /api/v1/recruitment_campaigns endpoints.

TDD Phase 2 — Red→Green for list, create, get, advance_stage.
Uses httpx AsyncClient with ASGITransport and FastAPI dependency_overrides.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.recruitment_campaigns import router
from app.auth.dependencies import get_current_user_or_demo
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id

# ── Constants ──────────────────────────────────────────────────────────────

COMPANY_ID = "company-test-uuid-1"
CAMPAIGN_ID = str(uuid.uuid4())


# ── Mocks ──────────────────────────────────────────────────────────────────

def _make_user():
    u = MagicMock()
    u.id = "user-test-1"
    u.email = "test@wedotalent.cc"
    u.company_id = COMPANY_ID
    return u


def _make_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    return db


def _make_campaign(data=None):
    base = {
        "id": uuid.UUID(CAMPAIGN_ID),
        "company_id": COMPANY_ID,
        "created_by": "test@wedotalent.cc",
        "name": "Campanha Engenharia Q3",
        "description": None,
        "job_id": None,
        "talent_pool_id": None,
        "status": "active",
        "automation_level": "semi",
        "current_stage_index": 0,
        "stages": [
            {"name": "sourcing", "order": 1},
            {"name": "screening", "order": 2},
            {"name": "interview", "order": 3},
        ],
        "total_candidates": 0,
        "candidates_screened": 0,
        "candidates_contacted": 0,
        "candidates_interviewed": 0,
        "candidates_offered": 0,
        "candidates_hired": 0,
        "stage_history": [],
        "created_at": None,
        "updated_at": None,
    }
    base.update(data or {})
    m = MagicMock()
    for k, v in base.items():
        setattr(m, k, v)
    return m


# ── App fixture ────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1")
    # Override auth and db dependencies
    _app.dependency_overrides[get_current_user_or_demo] = _make_user
    _app.dependency_overrides[get_db] = _make_db
    _app.dependency_overrides[require_company_id] = lambda: COMPANY_ID
    return _app


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_campaigns_empty(app):
    with patch("app.api.v1.recruitment_campaigns.CampaignRepository") as MockRepo:
        MockRepo.return_value.list_by_company = AsyncMock(return_value=([], 0))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/recruitment_campaigns")

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_campaigns_returns_items(app):
    campaign = _make_campaign()
    with patch("app.api.v1.recruitment_campaigns.CampaignRepository") as MockRepo:
        MockRepo.return_value.list_by_company = AsyncMock(return_value=([campaign], 1))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/recruitment_campaigns")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["data"][0]["name"] == "Campanha Engenharia Q3"
    assert body["data"][0]["status"] == "active"
    assert len(body["data"][0]["stages"]) == 3


@pytest.mark.asyncio
async def test_create_campaign_returns_201(app):
    campaign = _make_campaign()
    with (
        patch("app.api.v1.recruitment_campaigns.CampaignRepository") as MockRepo,
        patch("app.services.quota_enforcement.enforce_quota", new_callable=AsyncMock),
    ):
        MockRepo.return_value.create = AsyncMock(return_value=campaign)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/recruitment_campaigns",
                json={"name": "Campanha Engenharia Q3"},
            )

    assert resp.status_code == 201
    assert resp.json()["name"] == "Campanha Engenharia Q3"


@pytest.mark.asyncio
async def test_create_campaign_extra_field_rejected(app):
    """WeDoBaseModel extra=forbid — unknown fields must return 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/recruitment_campaigns",
            json={"name": "Test", "company_id": "hack-tenant"},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_campaign_found(app):
    campaign = _make_campaign()
    with patch("app.api.v1.recruitment_campaigns.CampaignRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=campaign)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/v1/recruitment_campaigns/{CAMPAIGN_ID}")

    assert resp.status_code == 200
    assert resp.json()["id"] == CAMPAIGN_ID


@pytest.mark.asyncio
async def test_get_campaign_not_found_returns_404(app):
    with patch("app.api.v1.recruitment_campaigns.CampaignRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=None)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/v1/recruitment_campaigns/{CAMPAIGN_ID}")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_advance_stage_increments_index(app):
    advanced = _make_campaign({"current_stage_index": 1})
    with patch("app.api.v1.recruitment_campaigns.CampaignRepository") as MockRepo:
        MockRepo.return_value.advance_stage = AsyncMock(return_value=advanced)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(f"/api/v1/recruitment_campaigns/{CAMPAIGN_ID}/advance-stage")

    assert resp.status_code == 200
    assert resp.json()["current_stage_index"] == 1


@pytest.mark.asyncio
async def test_advance_stage_wrong_company_returns_404(app):
    with patch("app.api.v1.recruitment_campaigns.CampaignRepository") as MockRepo:
        MockRepo.return_value.advance_stage = AsyncMock(return_value=None)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(f"/api/v1/recruitment_campaigns/{CAMPAIGN_ID}/advance-stage")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stages_projected_correctly(app):
    """Stages deve ter status: completed/in_progress/pending conforme current_stage_index."""
    campaign = _make_campaign({"current_stage_index": 1})
    with patch("app.api.v1.recruitment_campaigns.CampaignRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=campaign)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/v1/recruitment_campaigns/{CAMPAIGN_ID}")

    stages = resp.json()["stages"]
    assert stages[0]["status"] == "completed"
    assert stages[1]["status"] == "in_progress"
    assert stages[2]["status"] == "pending"
