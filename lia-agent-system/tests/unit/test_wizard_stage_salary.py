"""
Unit tests for stage_salary.handle_salary — F.3 cross-reference with
ats_job_history_service.get_similar_jobs.

Coverage:
  - fail-open: ATS service raises -> pipeline keeps 2 sources (history + market)
  - empty ATS: get_similar_jobs returns [] -> sources_used has only history+market
  - happy path: ATS returns valid jobs -> ats_history added as 3rd source
  - LGPD cutoff: jobs older than 12 months are discarded
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def base_inputs():
    """Minimal inputs that drive handle_salary into the pick_canonical path."""
    return dict(
        db=object(),  # truthy non-None placeholder
        company_id="company-test-1",
        job_draft={"cargo": "Desenvolvedor Python", "senioridade": "Pleno"},
        company_benefits=[],
        benchmarks={
            "internal_salary": {},
            "market_salary": {"min": 8000, "max": 12000, "median": 10000},
            "combined_recommendation": {
                "recommended_min": 8500,
                "recommended_max": 12500,
                "confidence": "medium",
                "sample_size": 5,
            },
            "learning_adjustments": {},
        },
        field_origins={},
        suggestions_data={},
    )


def _make_ats_job(
    salary_min=10000,
    salary_max=14000,
    days_old=30,
    title="Desenvolvedor Python Pleno",
    seniority="pleno",
):
    """Build a minimal ATSJobDescription mock-equivalent."""
    from app.domains.job_management.services.ats_job_history_service import (
        ATSJobDescription,
    )
    return ATSJobDescription(
        ats_job_id="job-1",
        ats_type="gupy",
        title=title,
        seniority=seniority,
        salary_min=salary_min,
        salary_max=salary_max,
        created_at=datetime.utcnow() - timedelta(days=days_old),
        closed_at=datetime.utcnow() - timedelta(days=max(0, days_old - 5)),
    )


@pytest.mark.asyncio
async def test_fail_open_when_ats_service_raises(base_inputs):
    """ATS service crash must NOT break pipeline; sources_used keeps history+market."""
    from app.domains.job_management.services.wizard_step_service import stage_salary

    with patch.object(
        stage_salary,
        "get_historical_salary_patterns",
        new=AsyncMock(return_value={"has_data": False}),
    ), patch.object(
        stage_salary.ats_job_history_service,
        "get_similar_jobs",
        new=AsyncMock(side_effect=RuntimeError("ats down")),
    ):
        msg, suggestions, origins = await stage_salary.handle_salary(**base_inputs)

    assert "canonical_salary_suggestion" in suggestions
    sources = suggestions["canonical_salary_suggestion"]["sources_used"]
    assert "ats_history" not in sources
    assert "market" in sources


@pytest.mark.asyncio
async def test_empty_ats_history_keeps_two_sources(base_inputs):
    """No similar ATS jobs -> 3rd source not added, pipeline OK."""
    from app.domains.job_management.services.wizard_step_service import stage_salary

    with patch.object(
        stage_salary,
        "get_historical_salary_patterns",
        new=AsyncMock(return_value={"has_data": False}),
    ), patch.object(
        stage_salary.ats_job_history_service,
        "get_similar_jobs",
        new=AsyncMock(return_value=[]),
    ):
        msg, suggestions, origins = await stage_salary.handle_salary(**base_inputs)

    sources = suggestions["canonical_salary_suggestion"]["sources_used"]
    assert sources == ["market"]


@pytest.mark.asyncio
async def test_ats_history_used_as_third_source(base_inputs):
    """ATS returns recent jobs with salary data -> ats_history present in sources_used."""
    from app.domains.job_management.services.wizard_step_service import stage_salary

    fake_jobs = [
        _make_ats_job(salary_min=11000, salary_max=15000, days_old=10),
        _make_ats_job(salary_min=10500, salary_max=14500, days_old=60),
        _make_ats_job(salary_min=12000, salary_max=16000, days_old=120),
    ]

    with patch.object(
        stage_salary,
        "get_historical_salary_patterns",
        new=AsyncMock(return_value={"has_data": False}),
    ), patch.object(
        stage_salary.ats_job_history_service,
        "get_similar_jobs",
        new=AsyncMock(return_value=fake_jobs),
    ):
        msg, suggestions, origins = await stage_salary.handle_salary(**base_inputs)

    canonical = suggestions["canonical_salary_suggestion"]
    assert "ats_history" in canonical["sources_used"]


@pytest.mark.asyncio
async def test_lgpd_cutoff_drops_old_jobs(base_inputs):
    """Jobs older than 12 months must be discarded for LGPD/data freshness."""
    from app.domains.job_management.services.wizard_step_service import stage_salary

    # All jobs 400 days old -> should all be discarded
    fake_jobs = [
        _make_ats_job(salary_min=11000, salary_max=15000, days_old=400),
        _make_ats_job(salary_min=10500, salary_max=14500, days_old=500),
    ]

    with patch.object(
        stage_salary,
        "get_historical_salary_patterns",
        new=AsyncMock(return_value={"has_data": False}),
    ), patch.object(
        stage_salary.ats_job_history_service,
        "get_similar_jobs",
        new=AsyncMock(return_value=fake_jobs),
    ):
        msg, suggestions, origins = await stage_salary.handle_salary(**base_inputs)

    sources = suggestions["canonical_salary_suggestion"]["sources_used"]
    assert "ats_history" not in sources
