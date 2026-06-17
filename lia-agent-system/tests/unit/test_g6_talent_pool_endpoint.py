"""
TDD tests for GET /analytics/predictions/talent-pool/{job_id}.

Covers:
1. Response shape validation (all required keys present)
2. Company_id auth enforcement (missing dependency → 422/401)
3. Empty vacancy (zero candidates returns zeros, not an error)
4. Vacancy not found returns 404
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


# ── Fixtures ────────────────────────────────────────────────────────────────

def _make_mock_repo(
    job=True,
    total=5,
    stage_counts=None,
    avg_hours=48.0,
    top_candidates=None,
):
    repo = AsyncMock()
    if job:
        mock_job = MagicMock()
        repo.get_job_by_id_and_company.return_value = mock_job
    else:
        repo.get_job_by_id_and_company.return_value = None

    repo.get_total_candidates_for_vacancy.return_value = total
    default_stages = {"screening": 2, "interview": 1, "offer": 1, "hired": 1}
    repo.get_stage_counts_for_vacancy.return_value = stage_counts if stage_counts is not None else default_stages
    repo.get_avg_time_to_hire.return_value = avg_hours
    repo.get_top_candidates_with_score.return_value = top_candidates or []
    return repo


def _make_app_with_endpoint():
    """Build minimal FastAPI app wiring the router under test."""
    from app.api.v1.predictive_analytics import router

    app = FastAPI()
    app.include_router(router)
    return app


# ── Test 1: response shape ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_talent_pool_endpoint_returns_expected_shape():
    """Endpoint must return all required keys in the expected shape."""
    from app.api.v1.predictive_analytics import get_talent_pool_insights

    mock_repo = _make_mock_repo()
    mock_db = AsyncMock()

    # Mock predictive_analytics_service.generate_pipeline_forecast
    mock_forecast = {
        "fill_probability": 65.0,
        "weekly_forecast": [
            {"week": 1, "expected_hires": 0},
            {"week": 2, "expected_hires": 1},
        ],
    }

    with patch(
        "app.api.v1.predictive_analytics.predictive_analytics_service.generate_pipeline_forecast",
        new_callable=AsyncMock,
        return_value=mock_forecast,
    ):
        result = await get_talent_pool_insights(
            job_id="test-job-123",
            db=mock_db,
            company_id="test-company-abc",
            repo=mock_repo,
        )

    assert result["success"] is True
    data = result["data"]

    # Top-level keys
    assert "job_id" in data
    assert "company_id" in data
    assert "metrics" in data
    assert "hiring_probability" in data
    assert "pipeline_prediction" in data
    assert "top_skills" in data

    # Metrics keys
    m = data["metrics"]
    for key in [
        "total_candidates", "in_screening", "in_interview", "in_offer",
        "hired", "rejected", "conversion_rate", "avg_time_to_fill_days",
    ]:
        assert key in m, f"Missing metrics key: {key}"

    # Hiring probability keys
    hp = data["hiring_probability"]
    assert "probability" in hp
    assert "confidence" in hp

    # Pipeline prediction keys
    pp = data["pipeline_prediction"]
    assert "closure_probability" in pp
    assert "estimated_days_to_close" in pp
    assert "confidence_level" in pp

    # Values are correct types
    assert isinstance(m["total_candidates"], int)
    assert isinstance(m["conversion_rate"], float)
    assert isinstance(hp["probability"], float)
    assert hp["confidence"] in ("high", "medium", "low")
    assert pp["confidence_level"] in ("high", "medium", "low")


# ── Test 2: company_id auth enforcement ─────────────────────────────────────

def test_talent_pool_endpoint_requires_company_id():
    """Without company_id dependency satisfied, request should fail (422)."""
    app = _make_app_with_endpoint()
    client = TestClient(app, raise_server_exceptions=False)

    # Call without Authorization header → require_company_id raises HTTP exception
    response = client.get("/analytics/predictions/talent-pool/some-job-id")
    # Should be 401 or 422 (depends on how require_company_id is implemented)
    assert response.status_code in (401, 403, 404, 422), (
        f"Expected auth error, got {response.status_code}: {response.text}"
    )


# ── Test 3: empty vacancy returns zeros, not error ───────────────────────────

@pytest.mark.asyncio
async def test_talent_pool_endpoint_with_empty_vacancy():
    """Vacancy with zero candidates must return zeros, not raise an exception."""
    from app.api.v1.predictive_analytics import get_talent_pool_insights

    mock_repo = _make_mock_repo(total=0, stage_counts={}, avg_hours=None, top_candidates=[])
    mock_db = AsyncMock()

    mock_forecast = {"fill_probability": 0.0, "weekly_forecast": []}

    with patch(
        "app.api.v1.predictive_analytics.predictive_analytics_service.generate_pipeline_forecast",
        new_callable=AsyncMock,
        return_value=mock_forecast,
    ):
        result = await get_talent_pool_insights(
            job_id="empty-job-456",
            db=mock_db,
            company_id="company-abc",
            repo=mock_repo,
        )

    assert result["success"] is True
    data = result["data"]
    m = data["metrics"]
    assert m["total_candidates"] == 0
    assert m["in_screening"] == 0
    assert m["in_interview"] == 0
    assert m["conversion_rate"] == 0.0
    assert m["avg_time_to_fill_days"] is None

    # With 0 candidates, probability should be 0
    hp = data["hiring_probability"]
    assert hp["probability"] == 0.0
    assert hp["confidence"] == "low"

    # top_skills should be empty list
    assert data["top_skills"] == []


# ── Test 4: job not found returns 404 ───────────────────────────────────────

@pytest.mark.asyncio
async def test_talent_pool_endpoint_job_not_found():
    """When job does not belong to company, endpoint returns 404."""
    from fastapi import HTTPException
    from app.api.v1.predictive_analytics import get_talent_pool_insights

    mock_repo = _make_mock_repo(job=False)
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_talent_pool_insights(
            job_id="nonexistent-job",
            db=mock_db,
            company_id="company-abc",
            repo=mock_repo,
        )

    assert exc_info.value.status_code == 404


# ── Test 5: conversion_rate computed correctly ───────────────────────────────

@pytest.mark.asyncio
async def test_talent_pool_conversion_rate_calculation():
    """Conversion rate = hired / total * 100, rounded to 1 decimal."""
    from app.api.v1.predictive_analytics import get_talent_pool_insights

    mock_repo = _make_mock_repo(
        total=10,
        stage_counts={"screening": 4, "interview": 3, "offer": 2, "hired": 1},
    )
    mock_db = AsyncMock()

    with patch(
        "app.api.v1.predictive_analytics.predictive_analytics_service.generate_pipeline_forecast",
        new_callable=AsyncMock,
        return_value={"fill_probability": 50.0, "weekly_forecast": []},
    ):
        result = await get_talent_pool_insights(
            job_id="job-conv-test",
            db=mock_db,
            company_id="company-abc",
            repo=mock_repo,
        )

    m = result["data"]["metrics"]
    assert m["total_candidates"] == 10
    assert m["hired"] == 1
    assert m["conversion_rate"] == 10.0  # 1/10 * 100


# ── Test 6: pipeline forecast fallback does not break endpoint ───────────────

@pytest.mark.asyncio
async def test_talent_pool_pipeline_forecast_fallback():
    """If pipeline forecast raises an exception, endpoint still returns successfully."""
    from app.api.v1.predictive_analytics import get_talent_pool_insights

    mock_repo = _make_mock_repo()
    mock_db = AsyncMock()

    with patch(
        "app.api.v1.predictive_analytics.predictive_analytics_service.generate_pipeline_forecast",
        new_callable=AsyncMock,
        side_effect=RuntimeError("service unavailable"),
    ):
        result = await get_talent_pool_insights(
            job_id="job-fallback",
            db=mock_db,
            company_id="company-abc",
            repo=mock_repo,
        )

    assert result["success"] is True
    pp = result["data"]["pipeline_prediction"]
    assert pp["closure_probability"] == 0.0
    assert pp["estimated_days_to_close"] is None
    assert pp["confidence_level"] == "low"
