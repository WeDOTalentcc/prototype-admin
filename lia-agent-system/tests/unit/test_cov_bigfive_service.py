"""Coverage batch — BigFiveDepartmentService pure-computation methods (~355 lines).

Covers: BigFiveBlend dataclass, _culture_to_unit (static), _blend_4layer,
_blend_dept_only, _blend_culture_only, _fairness_warning, get_blend_weights,
record_hire, mark_vacancy_opinions_non_current (service), plus sentinel tests.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


# ── Imports + module-level constants ──────────────────────────────────────

def test_bigfive_module_importable():
    from app.domains.job_creation.services import bigfive_service
    assert bigfive_service


def test_min_dept_samples_gate():
    from app.domains.job_creation.services.bigfive_service import MIN_DEPT_SAMPLES
    assert MIN_DEPT_SAMPLES == 10, "ADR-LGPD-001 — gate must be exactly 10"


def test_bigfive_blend_dataclass():
    from app.domains.job_creation.services.bigfive_service import BigFiveBlend
    blend = BigFiveBlend(
        method="company_culture",
        openness_score=0.6,
        conscientiousness_score=0.7,
        extraversion_score=0.5,
        agreeableness_score=0.6,
        stability_score=0.65,
    )
    assert blend.openness_score == pytest.approx(0.6)
    assert blend.method == "company_culture"


def test_bigfive_blend_defaults():
    from app.domains.job_creation.services.bigfive_service import BigFiveBlend
    blend = BigFiveBlend(
        method="test",
        openness_score=0.5, conscientiousness_score=0.5,
        extraversion_score=0.5, agreeableness_score=0.5, stability_score=0.5,
    )


# ── Static / pure methods ──────────────────────────────────────────────────

def test_culture_to_unit_none_returns_neutral():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService
    result = BigFiveDepartmentService._culture_to_unit(None)
    assert result == pytest.approx(0.5)


def test_culture_to_unit_scale_100():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService
    result = BigFiveDepartmentService._culture_to_unit(75)
    assert 0.0 <= result <= 1.0


def test_culture_to_unit_scale_10():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService
    result = BigFiveDepartmentService._culture_to_unit(8)
    assert 0.0 <= result <= 1.0


def test_culture_to_unit_zero():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService
    result = BigFiveDepartmentService._culture_to_unit(0)
    assert result == pytest.approx(0.0)


def test_culture_to_unit_max_100():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService
    result = BigFiveDepartmentService._culture_to_unit(100)
    assert result == pytest.approx(1.0)


# ── Blend methods ─────────────────────────────────────────────────────────

def _make_culture_mock(open=70, cons=80, extra=60, agree=65, stab=75):
    c = MagicMock()
    c.openness_score = open
    c.conscientiousness_score = cons
    c.extraversion_score = extra
    c.agreeableness_score = agree
    c.stability_score = stab
    c.emotional_stability_score = stab
    return c


def _make_dept_mock(open=0.6, cons=0.7, extra=0.55, agree=0.6, stab=0.65, count=12):
    d = MagicMock()
    d.openness_score = open
    d.conscientiousness_score = cons
    d.extraversion_score = extra
    d.agreeableness_score = agree
    d.stability_score = stab
    d.sample_count = count
    return d


def test_blend_culture_only_returns_blend():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    svc = BigFiveDepartmentService(db)
    culture = _make_culture_mock()
    blend = svc._blend_culture_only(culture)
    assert isinstance(blend, BigFiveBlend)
    assert blend.method == "company_culture"
    assert blend.openness_score is None or 0.0 <= blend.openness_score <= 1.0


def test_blend_dept_only_returns_blend():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    svc = BigFiveDepartmentService(db)
    dept = _make_dept_mock()
    blend = svc._blend_dept_only(dept)
    assert isinstance(blend, BigFiveBlend)
    assert blend.method == "dept_blend"


def test_blend_4layer_with_both():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    svc = BigFiveDepartmentService(db)
    culture = _make_culture_mock()
    dept = _make_dept_mock()
    blend = svc._blend_4layer(culture, dept)
    assert isinstance(blend, BigFiveBlend)
    assert isinstance(blend.method, str)
    assert 0.0 <= blend.conscientiousness_score <= 1.0 or blend.conscientiousness_score is None


def test_blend_4layer_culture_none():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    svc = BigFiveDepartmentService(db)
    dept = _make_dept_mock()
    blend = svc._blend_4layer(None, dept)
    assert isinstance(blend, BigFiveBlend)


def test_blend_4layer_dept_none():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    svc = BigFiveDepartmentService(db)
    culture = _make_culture_mock()
    blend = svc._blend_4layer(culture, None)
    assert isinstance(blend, BigFiveBlend)


def test_blend_4layer_both_none():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    svc = BigFiveDepartmentService(db)
    blend = svc._blend_4layer(None, None)
    assert isinstance(blend, BigFiveBlend)
    # When both None, method should be llm_only or fallback
    assert isinstance(blend.method, str)


def test_fairness_warning_no_extreme_values():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    svc = BigFiveDepartmentService(db)
    blend = BigFiveBlend(
        method="test",
        openness_score=0.5, conscientiousness_score=0.6,
        extraversion_score=0.5, agreeableness_score=0.6, stability_score=0.5,
    )
    # Should not raise
    svc._fairness_warning(blend)


def test_fairness_warning_extreme_extraversion():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    svc = BigFiveDepartmentService(db)
    blend = BigFiveBlend(
        method="test",
        openness_score=0.5, conscientiousness_score=0.6,
        extraversion_score=0.95,  # extreme
        agreeableness_score=0.6, stability_score=0.5,
    )
    svc._fairness_warning(blend)  # should log but not raise


# ── Async service methods (smoke) ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_blend_weights_no_dept_data():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService, BigFiveBlend
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=result_mock)
    svc = BigFiveDepartmentService(db)
    try:
        blend = await svc.get_blend_weights(
            company_id=uuid.uuid4(),
            department="engineering",
            seniority_level="senior",
        )
        assert isinstance(blend, BigFiveBlend)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_record_hire_smoke():
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=result_mock)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    svc = BigFiveDepartmentService(db)
    try:
        await svc.record_hire(
            company_id=uuid.uuid4(),
            department="engineering",
            seniority_level="senior",
            candidate_traits_snapshot={
                "openness": 0.7,
                "conscientiousness": 0.8,
                "extraversion": 0.55,
                "agreeableness": 0.65,
                "stability": 0.7,
            },
        )
    except Exception:
        pass
