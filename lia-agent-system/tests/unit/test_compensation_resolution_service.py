"""Unit puro — motor de resolucao % -> R$ (compensation_resolution_service).

Sentinela do UNICO ponto de multiplicacao da remuneracao. Antes deste motor o
"% do salario" nunca virava R$. Estes testes pinam a derivacao canonica:
    R$ = (% / 100) x faixa_salarial[nivel]
e garantem que verbas escopadas a niveis herdam a banda sem redigitar faixa.
"""
import pytest

from app.domains.company.services import compensation_resolution_service as svc


SENIOR_BAND = {"min": 11000, "mid": 14000, "max": 17000, "currency": "BRL"}
BAND_MAP = {
    "junior": {"min": 4000, "mid": 6000, "max": 8000, "currency": "BRL"},
    "pleno": {"min": 7000, "mid": 9500, "max": 12000, "currency": "BRL"},
    "senior": SENIOR_BAND,
}


def test_percent_of_salary_derives_rs():
    plr = {"value_type": "percent", "min_pct": 5.0, "max_pct": 20.0}
    r = svc.resolve_for_band(plr, SENIOR_BAND)
    assert r["basis"] == "percent_of_salary"
    assert r["min"] == pytest.approx(550.0)   # 5% de 11000
    assert r["max"] == pytest.approx(3400.0)  # 20% de 17000
    assert r["currency"] == "BRL"


def test_target_pct_fallback_when_no_range():
    bonus = {"value_type": "percent", "target_pct": 10.0}
    r = svc.resolve_for_band(bonus, SENIOR_BAND)
    assert r["basis"] == "percent_of_salary"
    assert r["min"] == pytest.approx(1100.0)
    assert r["max"] == pytest.approx(1700.0)


def test_currency_value_is_fixed_not_derived():
    fixed = {"value_type": "currency", "min_amount": 1000, "max_amount": 5000}
    r = svc.resolve_for_band(fixed, SENIOR_BAND)
    assert r["basis"] == "fixed"
    assert r["min"] == 1000
    assert r["max"] == 5000


def test_plr_n_salaries_from_spec():
    plr = {"value_type": "currency", "spec": {"n_salaries_min": 1, "n_salaries_max": 2}}
    r = svc.resolve_for_band(plr, SENIOR_BAND)
    assert r["basis"] == "n_salaries"
    assert r["min"] == pytest.approx(11000.0)  # 1x min
    assert r["max"] == pytest.approx(34000.0)  # 2x max


def test_undefined_when_no_pct_and_no_amount():
    empty = {"value_type": "percent"}
    r = svc.resolve_for_band(empty, SENIOR_BAND)
    assert r["basis"] == "undefined"
    assert r["min"] is None and r["max"] is None


def test_undefined_when_pct_but_no_band():
    plr = {"value_type": "percent", "min_pct": 5.0, "max_pct": 20.0}
    r = svc.resolve_for_band(plr, None)
    assert r["basis"] == "undefined"


def test_resolve_for_levels_empty_scope_is_all_levels():
    bonus = {"value_type": "percent", "min_pct": 10.0, "max_pct": 10.0, "seniority_levels": []}
    out = svc.resolve_for_levels(bonus, BAND_MAP)
    assert set(out.keys()) == {"junior", "pleno", "senior"}
    assert out["junior"]["min"] == pytest.approx(400.0)   # 10% de 4000
    assert out["senior"]["max"] == pytest.approx(1700.0)  # 10% de 17000


def test_resolve_for_levels_scoped_subset():
    bonus = {"value_type": "percent", "min_pct": 10.0, "max_pct": 10.0,
             "seniority_levels": ["senior"]}
    out = svc.resolve_for_levels(bonus, BAND_MAP)
    assert set(out.keys()) == {"senior"}


def test_resolve_for_levels_all_wildcard():
    bonus = {"value_type": "percent", "min_pct": 1.0, "max_pct": 1.0,
             "seniority_levels": ["all"]}
    out = svc.resolve_for_levels(bonus, BAND_MAP)
    assert set(out.keys()) == {"junior", "pleno", "senior"}


def test_resolve_for_salary_range_override():
    plr = {"value_type": "percent", "min_pct": 5.0, "max_pct": 20.0}
    r = svc.resolve_for_salary_range(plr, {"min": 10000, "max": 20000, "currency": "BRL"})
    assert r["basis"] == "percent_of_salary"
    assert r["min"] == pytest.approx(500.0)
    assert r["max"] == pytest.approx(4000.0)


def test_works_with_orm_like_object():
    class C:
        value_type = "percent"
        min_pct = 5.0
        max_pct = 20.0
        min_amount = None
        max_amount = None
        target_pct = None
        currency = "BRL"
        spec = None
        seniority_levels = ["senior"]

    out = svc.resolve_for_levels(C(), BAND_MAP)
    assert out["senior"]["min"] == pytest.approx(550.0)
