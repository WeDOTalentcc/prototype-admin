"""Unit tests for WsiEffectivenessRepository - Sprint B Phase 3.

Cobertura: Welford correctness, multi-tenancy, validation.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


@pytest.fixture
def fake_company() -> str:
    return f"co-{uuid4()}"


# -- Welford math validation -------------------------------------------------


def test_welford_update_first_sample():
    """Primeiro sample: n=1, mean=x, m2=0."""
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    n, mean, m2 = WsiEffectivenessRepository._welford_update(0, 0.0, 0.0, 50.0)
    assert n == 1
    assert mean == 50.0
    assert m2 == 0.0


def test_welford_update_two_samples_mean_correct():
    """2 samples 50 e 70: mean=60, m2=200 (variance population=100)."""
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    repo_cls = WsiEffectivenessRepository
    n, mean, m2 = repo_cls._welford_update(0, 0.0, 0.0, 50.0)
    n, mean, m2 = repo_cls._welford_update(n, mean, m2, 70.0)
    assert n == 2
    assert mean == 60.0
    # M2 = (50-60)^2 + (70-60)^2 = 100 + 100 = 200
    assert abs(m2 - 200.0) < 0.001


def test_welford_update_three_samples_running_mean():
    """3 samples 60, 70, 80: mean = 70."""
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    repo_cls = WsiEffectivenessRepository
    n, mean, m2 = 0, 0.0, 0.0
    for x in [60.0, 70.0, 80.0]:
        n, mean, m2 = repo_cls._welford_update(n, mean, m2, x)
    assert n == 3
    assert abs(mean - 70.0) < 0.001
    # variance = ((60-70)^2 + (70-70)^2 + (80-70)^2) = 200, m2 = 200
    assert abs(m2 - 200.0) < 0.001


def test_compute_discrimination_no_data_returns_zero():
    """Sem amostras suficientes - discrimination = 0."""
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    disc = WsiEffectivenessRepository._compute_discrimination(
        0.0, 0.0, 0,  # hired
        0.0, 0.0, 0,  # rejected
    )
    assert disc == 0.0


def test_compute_discrimination_separate_means():
    """Hired mean=80, rejected mean=40, low variance: discrimination alta positivo."""
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    # Hired n=10, mean=80, M2=10 (var=1.1, std~1.05)
    # Rejected n=10, mean=40, M2=10
    # Pooled var = (10+10)/19 ~= 1.05, std ~= 1.026
    # disc = (80-40)/1.026 ~= 38.98
    disc = WsiEffectivenessRepository._compute_discrimination(
        80.0, 10.0, 10,
        40.0, 10.0, 10,
    )
    assert disc > 30  # pooled std small, mean diff huge
    assert disc < 50


# -- Multi-tenancy fail-closed -----------------------------------------------


@pytest.mark.asyncio
async def test_record_outcome_requires_company_id():
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    repo = WsiEffectivenessRepository(db=AsyncMock())
    with pytest.raises(ValueError, match="company_id"):
        await repo.record_outcome(
            company_id="",
            skill_probed="active_listening",
            parent_id="communication_collaboration",
            outcome="hired",
            score=80.0,
        )


@pytest.mark.asyncio
async def test_record_outcome_validates_outcome_enum():
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    repo = WsiEffectivenessRepository(db=AsyncMock())
    with pytest.raises(ValueError, match="outcome"):
        await repo.record_outcome(
            company_id="co-x",
            skill_probed="active_listening",
            parent_id="communication_collaboration",
            outcome="invalid_outcome",
            score=80.0,
        )


@pytest.mark.asyncio
async def test_record_outcome_validates_score_range():
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    repo = WsiEffectivenessRepository(db=AsyncMock())
    with pytest.raises(ValueError, match="score"):
        await repo.record_outcome(
            company_id="co-x",
            skill_probed="active_listening",
            parent_id="communication_collaboration",
            outcome="hired",
            score=150.0,  # >100
        )


@pytest.mark.asyncio
async def test_get_or_none_requires_company_id():
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    repo = WsiEffectivenessRepository(db=AsyncMock())
    with pytest.raises(ValueError, match="company_id"):
        await repo.get_or_none("", "active_listening")


@pytest.mark.asyncio
async def test_get_by_skills_requires_company_id():
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    repo = WsiEffectivenessRepository(db=AsyncMock())
    with pytest.raises(ValueError, match="company_id"):
        await repo.get_by_skills("", ["x"])


@pytest.mark.asyncio
async def test_get_by_skills_empty_list_returns_empty():
    from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
        WsiEffectivenessRepository,
    )
    repo = WsiEffectivenessRepository(db=AsyncMock())
    result = await repo.get_by_skills("co-x", [])
    assert result == {}
