"""Unit tests for BigFiveDepartmentService - Sprint B Phase 2 (canonical).

Cobertura:
- get_blend_weights: llm_only / company_culture / dept_blend
- 4-layer formula matematica (asserts numericos)
- Stability semantics consistente (alto = bom)
- Toggle gates respeitados
- record_hire: whitelist OCEAN, running average, decay temporal
- Multi-tenancy: company_id obrigatorio
- Fairness warning emitido (sem teatro de bloqueio)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# -- Fixtures locais ---------------------------------------------------------


@pytest.fixture
def fake_company_a() -> str:
    return f"company-a-{uuid4()}"


@pytest.fixture
def fake_company_b() -> str:
    return f"company-b-{uuid4()}"


def _make_culture_profile(
    openness=60, conscientiousness=70,
    extraversion=50, agreeableness=65, stability=55,
):
    """CompanyCultureProfile mock (scores 0-100 inteiros)."""
    m = MagicMock()
    m.openness_score = openness
    m.conscientiousness_score = conscientiousness
    m.extraversion_score = extraversion
    m.agreeableness_score = agreeableness
    m.stability_score = stability
    return m


def _make_dept_profile(
    sample_count=15,
    openness=0.70, conscientiousness=0.78,
    extraversion=0.48, agreeableness=0.60, stability=0.70,
    last_updated_at=None,
):
    """BigFiveDepartmentProfile mock (scores 0-1 floats, alto=bom)."""
    m = MagicMock()
    m.sample_count = sample_count
    m.openness_score = openness
    m.conscientiousness_score = conscientiousness
    m.extraversion_score = extraversion
    m.agreeableness_score = agreeableness
    m.stability_score = stability
    m.last_updated_at = last_updated_at or datetime.utcnow()
    return m


def _make_toggle(
    enabled=True,
    bigfive_company_culture=True,
    bigfive_department_history=False,
):
    return {
        "enabled": enabled,
        "bigfive_company_culture": bigfive_company_culture,
        "bigfive_department_history": bigfive_department_history,
        "wsi_question_effectiveness": False,
        "jd_similar_suggestion": True,
    }


# -- Multi-tenancy ----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_blend_requires_company_id():
    """company_id vazio levanta ValueError (fail-closed)."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    svc = BigFiveDepartmentService(db=AsyncMock())
    with pytest.raises(ValueError, match="company_id"):
        await svc.get_blend_weights(
            company_id="",
            department="engineering",
            seniority_level="senior",
        )


@pytest.mark.asyncio
async def test_record_hire_requires_company_id():
    """record_hire com company_id vazio levanta ValueError."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    svc = BigFiveDepartmentService(db=AsyncMock())
    with pytest.raises(ValueError, match="company_id"):
        await svc.record_hire(
            company_id="",
            department="eng",
            seniority_level="senior",
            candidate_traits_snapshot={"openness": 0.7},
        )


# -- Blend method routing ---------------------------------------------------


@pytest.mark.asyncio
async def test_blend_no_history_no_culture_returns_llm_only(fake_company_a):
    """Sem dept e sem culture - method=llm_only com scores None."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    svc = BigFiveDepartmentService(db=AsyncMock())
    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=None)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=None)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle())):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    assert blend.method == "llm_only"
    assert blend.openness_score is None
    assert blend.stability_score is None


@pytest.mark.asyncio
async def test_blend_culture_only_returns_company_culture_normalized(fake_company_a):
    """Culture (0-100) presente mas sem dept - method=company_culture, scores normalizados 0-1."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    culture = _make_culture_profile(openness=60, stability=80)
    svc = BigFiveDepartmentService(db=AsyncMock())

    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=None)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=culture)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle())):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    assert blend.method == "company_culture"
    # Asserts numericos da normalizacao 0-100 -> 0-1
    assert blend.openness_score == 0.6
    assert blend.stability_score == 0.8


@pytest.mark.asyncio
async def test_blend_dept_below_threshold_falls_back_to_culture(fake_company_a):
    """sample_count < 10 - dept ignorado, vira company_culture (3-layer)."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    dept = _make_dept_profile(sample_count=5)
    culture = _make_culture_profile()
    svc = BigFiveDepartmentService(db=AsyncMock())

    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=dept)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=culture)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle(
             bigfive_department_history=True))):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    assert blend.method == "company_culture"


@pytest.mark.asyncio
async def test_blend_dept_above_threshold_with_culture_returns_dept_blend(fake_company_a):
    """sample_count >= 10 + culture + ambos toggles ON - method=dept_blend (4-layer)."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    dept = _make_dept_profile(sample_count=20)
    culture = _make_culture_profile()
    svc = BigFiveDepartmentService(db=AsyncMock())

    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=dept)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=culture)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle(
             bigfive_department_history=True))):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    assert blend.method == "dept_blend"
    # Stability scores devem estar populados pelos 4 layers
    assert blend.stability_score is not None
    assert 0.0 <= blend.stability_score <= 1.0


@pytest.mark.asyncio
async def test_blend_dept_only_no_culture(fake_company_a):
    """Dept presente sem culture - method=dept_blend com scores diretos do dept."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    dept = _make_dept_profile(sample_count=20, stability=0.65)
    svc = BigFiveDepartmentService(db=AsyncMock())

    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=dept)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=None)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle(
             bigfive_department_history=True))):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    assert blend.method == "dept_blend"
    # Sem culture - scores devem ser os do dept profile direto
    assert blend.stability_score == 0.65


# -- 4-layer formula matematica ---------------------------------------------


@pytest.mark.asyncio
async def test_4layer_blend_formula_is_weighted_average(fake_company_a):
    """Verifica formula: (culture_w * c + dept_w * d) / (culture_w + dept_w).

    Pesos: culture=0.15, dept=0.25, total prior=0.40.
    Inputs:
      culture.openness=80 (normaliza pra 0.8)
      dept.openness=0.4
    Esperado: (0.15*0.8 + 0.25*0.4) / 0.40 = (0.12 + 0.10) / 0.40 = 0.55
    """
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    culture = _make_culture_profile(openness=80)
    dept = _make_dept_profile(sample_count=20, openness=0.4)
    svc = BigFiveDepartmentService(db=AsyncMock())

    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=dept)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=culture)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle(
             bigfive_department_history=True))):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    expected = (0.15 * 0.8 + 0.25 * 0.4) / (0.15 + 0.25)  # 0.55
    assert abs(blend.openness_score - expected) < 0.001, \
        f"Expected ~{expected}, got {blend.openness_score}"


@pytest.mark.asyncio
async def test_stability_no_inversion_in_blend(fake_company_a):
    """Stability semantics consistente: alto=bom, sem inversao.

    culture.stability=80 (=> 0.8) e dept.stability=0.7.
    Esperado: (0.15*0.8 + 0.25*0.7) / 0.40 = (0.12 + 0.175) / 0.40 = 0.7375
    """
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    culture = _make_culture_profile(stability=80)
    dept = _make_dept_profile(sample_count=20, stability=0.7)
    svc = BigFiveDepartmentService(db=AsyncMock())

    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=dept)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=culture)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle(
             bigfive_department_history=True))):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    expected = (0.15 * 0.8 + 0.25 * 0.7) / (0.15 + 0.25)  # 0.7375
    assert abs(blend.stability_score - expected) < 0.001


# -- Toggle gates -----------------------------------------------------------


@pytest.mark.asyncio
async def test_toggle_master_off_disables_all_layers(fake_company_a):
    """master enabled=False - skip all layers, retorna llm_only mesmo com data."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    dept = _make_dept_profile(sample_count=50)
    culture = _make_culture_profile()
    svc = BigFiveDepartmentService(db=AsyncMock())

    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=dept)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=culture)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle(enabled=False))):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    assert blend.method == "llm_only"


@pytest.mark.asyncio
async def test_toggle_dept_off_skips_layer4(fake_company_a):
    """bigfive_department_history=False - skip dept mesmo com samples."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    dept = _make_dept_profile(sample_count=50)
    culture = _make_culture_profile()
    svc = BigFiveDepartmentService(db=AsyncMock())

    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=dept)), \
         patch.object(svc, "_get_culture_profile", AsyncMock(return_value=culture)), \
         patch.object(svc, "_get_toggles", AsyncMock(return_value=_make_toggle(
             bigfive_department_history=False))):
        blend = await svc.get_blend_weights(
            company_id=fake_company_a,
            department="engineering",
            seniority_level="senior",
        )

    assert blend.method == "company_culture"


# -- record_hire (running average + temporal decay + PII guard) -------------


@pytest.mark.asyncio
async def test_record_hire_rejects_pii_keys(fake_company_a):
    """LGPD: keys fora da whitelist OCEAN levantam ValueError."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    svc = BigFiveDepartmentService(db=AsyncMock())
    with pytest.raises(ValueError, match="invalid keys"):
        await svc.record_hire(
            company_id=fake_company_a,
            department="eng",
            seniority_level="senior",
            candidate_traits_snapshot={
                "openness": 0.7,
                "candidate_email": "x@y.com",  # PII - deve bloquear
            },
        )


@pytest.mark.asyncio
async def test_record_hire_calls_upsert_with_existing_profile(fake_company_a):
    """record_hire passa existing_profile pra upsert (evita double lookup P1.5)."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    profile = _make_dept_profile(sample_count=10, last_updated_at=datetime.utcnow())
    mock_repo = MagicMock()
    mock_repo.upsert = AsyncMock()

    svc = BigFiveDepartmentService(db=AsyncMock())
    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=profile)), \
         patch.object(svc, "repo", mock_repo):
        await svc.record_hire(
            company_id=fake_company_a,
            department="eng",
            seniority_level="senior",
            candidate_traits_snapshot={"openness": 0.9, "stability": 0.8},
        )

    mock_repo.upsert.assert_called_once()
    call_kwargs = mock_repo.upsert.call_args.kwargs
    assert call_kwargs["existing_profile"] is profile  # P1.5 fix
    assert call_kwargs["company_id"] == fake_company_a
    # trait_delta deve conter apenas as keys passadas (defesa em profundidade)
    assert "openness" in call_kwargs["trait_delta"]
    assert "stability" in call_kwargs["trait_delta"]


@pytest.mark.asyncio
async def test_record_hire_applies_temporal_decay(fake_company_a):
    """Profile > 18m recebe sample_weight < 1.0 (lambda 0.05)."""
    from app.domains.job_creation.services.bigfive_service import (
        BigFiveDepartmentService,
        TEMPORAL_DECAY_LAMBDA,
        DECAY_THRESHOLD_DAYS,
    )

    old_date = datetime.utcnow() - timedelta(days=600)
    profile = _make_dept_profile(sample_count=20, last_updated_at=old_date)
    mock_repo = MagicMock()
    mock_repo.upsert = AsyncMock()

    svc = BigFiveDepartmentService(db=AsyncMock())
    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=profile)), \
         patch.object(svc, "repo", mock_repo):
        await svc.record_hire(
            company_id=fake_company_a,
            department="eng",
            seniority_level="senior",
            candidate_traits_snapshot={"openness": 0.9},
        )

    weight = mock_repo.upsert.call_args.kwargs["sample_weight"]
    assert weight < 1.0, f"Expected decayed weight < 1.0, got {weight}"
    # Asserto numerico aproximado: weight = exp(-0.05 * (600-548)/30) ~= exp(-0.0867) ~= 0.917
    import math
    expected = math.exp(-TEMPORAL_DECAY_LAMBDA * (600 - DECAY_THRESHOLD_DAYS) / 30.0)
    assert abs(weight - expected) < 0.01


# -- Multi-tenancy isolation ------------------------------------------------


@pytest.mark.asyncio
async def test_record_hire_multi_tenancy_no_cross_contamination(fake_company_a, fake_company_b):
    """Hire de A nao toca profile de B (repo.upsert recebe company_id correto)."""
    from app.domains.job_creation.services.bigfive_service import BigFiveDepartmentService

    profile_a = _make_dept_profile(sample_count=10)
    mock_repo = MagicMock()
    mock_repo.upsert = AsyncMock()

    svc = BigFiveDepartmentService(db=AsyncMock())
    with patch.object(svc, "_get_dept_profile", AsyncMock(return_value=profile_a)), \
         patch.object(svc, "repo", mock_repo):
        await svc.record_hire(
            company_id=fake_company_a,
            department="eng",
            seniority_level="senior",
            candidate_traits_snapshot={"openness": 0.9},
        )

    # Apenas company_a foi tocada
    upserted_company = mock_repo.upsert.call_args.kwargs["company_id"]
    assert upserted_company == fake_company_a
    assert upserted_company != fake_company_b


# -- Constants exposed -----------------------------------------------------


def test_constants_exposed():
    """Constants permanecem visiveis pra que callers possam usar mesmas thresholds."""
    from app.domains.job_creation.services.bigfive_service import (
        DECAY_THRESHOLD_DAYS,
        FAIRNESS_THRESHOLD,
        MIN_DEPT_SAMPLES,
        TEMPORAL_DECAY_LAMBDA,
        WEIGHTS_4L,
    )

    assert MIN_DEPT_SAMPLES == 10
    assert TEMPORAL_DECAY_LAMBDA == 0.05
    assert DECAY_THRESHOLD_DAYS == 548
    assert FAIRNESS_THRESHOLD == 0.10
    # Pesos 4-layer: prior + LLM + O*NET = 1.0
    assert WEIGHTS_4L["llm"] + WEIGHTS_4L["onet"] + WEIGHTS_4L["culture"] + WEIGHTS_4L["dept"] == 1.0


# -- Repository whitelist ---------------------------------------------------


def test_repository_whitelist_constants():
    """ALLOWED_TRAITS expoe apenas 5 OCEAN traits + stability (sem neuroticism)."""
    from app.domains.job_creation.repositories.bigfive_department_profile_repository import (
        ALLOWED_TRAITS,
    )

    assert ALLOWED_TRAITS == frozenset({
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "stability",
    })
    assert "neuroticism" not in ALLOWED_TRAITS  # P0.5 fix
