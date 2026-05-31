"""Consolidacao WSI Fase 2.4b: rank_traits canonico em cv_screening.

Pina a formula F3 deterministica (LLM + O*NET + senioridade/dept-blend) portada
do fork job_creation para o canonico. Testes PUROS (sem LLM/DB).
"""
import pytest

from app.domains.cv_screening.services.wsi_service.bigfive import (
    rank_traits,
    get_blend_score,
    TRAITS,
)


@pytest.mark.medium
def test_llm_only_formula_known_value():
    # openness: 0.40*0.8 + 0.35*0.5(default onet) + 0.25*0.1(pleno boost) = 0.52
    out = rank_traits({"openness": 0.8}, "pleno", role_archetype="default")
    o = next(r for r in out if r["trait"] == "openness")
    assert o["blend_method"] == "llm_only"
    assert abs(o["score"] - 0.52) < 1e-6


@pytest.mark.medium
def test_returns_all_five_traits_ranked_and_normalized():
    out = rank_traits({t: 0.6 for t in TRAITS}, "senior")
    assert {r["trait"] for r in out} == set(TRAITS)
    # ordenado desc por score
    scores = [r["score"] for r in out]
    assert scores == sorted(scores, reverse=True)
    # rank sequencial 1..5
    assert [r["rank"] for r in out] == [1, 2, 3, 4, 5]
    # weights somam ~1.0
    assert abs(sum(r["weight"] for r in out) - 1.0) < 0.01


@pytest.mark.medium
def test_deterministic():
    a = rank_traits({"openness": 0.7, "stability": 0.4}, "lead")
    b = rank_traits({"openness": 0.7, "stability": 0.4}, "lead")
    assert a == b


class _FakeBlend:
    method = "dept_blend"
    openness_score = 0.9
    conscientiousness_score = 0.9
    extraversion_score = 0.9
    agreeableness_score = 0.9
    stability_score = 0.9


class _FakeCulture:
    method = "company_culture"
    openness_score = 0.2
    conscientiousness_score = 0.2
    extraversion_score = 0.2
    agreeableness_score = 0.2
    stability_score = 0.2


@pytest.mark.medium
def test_dept_blend_4layer_formula():
    # openness: 0.40*0.5 + 0.20*0.5(onet default) + (0.15+0.25)*0.9 = 0.2+0.1+0.36 = 0.66
    out = rank_traits({"openness": 0.5}, "pleno", dept_blend=_FakeBlend())
    o = next(r for r in out if r["trait"] == "openness")
    assert o["blend_method"] == "dept_blend"
    assert abs(o["score"] - 0.66) < 1e-6


@pytest.mark.medium
def test_company_culture_3layer_formula():
    # openness: 0.40*0.5 + 0.35*0.5 + 0.25*0.2 = 0.2+0.175+0.05 = 0.425
    out = rank_traits({"openness": 0.5}, "pleno", dept_blend=_FakeCulture())
    o = next(r for r in out if r["trait"] == "openness")
    assert o["blend_method"] == "company_culture"
    assert abs(o["score"] - 0.425) < 1e-6


@pytest.mark.medium
def test_get_blend_score_failsoft():
    assert get_blend_score(None, "openness") == 0.5
    assert get_blend_score(_FakeBlend(), "openness") == 0.9


@pytest.mark.medium
def test_role_archetype_prior_applied():
    # engineering conscientiousness onet=0.8 -> 0.40*0.5 + 0.35*0.8 + 0.25*0.1(pleno boost) = 0.2+0.28+0.025=0.505
    out = rank_traits({"conscientiousness": 0.5}, "pleno", role_archetype="engineering")
    c = next(r for r in out if r["trait"] == "conscientiousness")
    assert abs(c["score"] - 0.505) < 1e-6
