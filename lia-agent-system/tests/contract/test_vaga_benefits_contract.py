"""Contract sensors para a integracao Beneficios catalogo<->vaga (2026-05-31).

Pinam: (1) parser backward-compat nunca descarta item e classifica source
corretamente; (2) match-keys casam EN (catalogo) com PT (vaga); (3) logica de
matching do repo (dimensoes + curinga 'all' + dept). Tudo puro/sincrono.
"""
import pytest

from app.domains.job_creation.helpers.vaga_benefits import (
    VagaBenefit,
    parse_vaga_benefits,
    snapshot_from_catalog,
    to_rails_names,
    vaga_benefits_to_jsonb,
)
from app.domains.job_creation.helpers.vacancy_vocab import (
    to_match_contract_key,
    to_match_seniority_key,
)
from app.domains.company.repositories.company_benefit_repository import (
    CompanyBenefitRepository,
)


# --- parser backward-compat ------------------------------------------------
def test_parse_string_legacy_becomes_inline():
    out = parse_vaga_benefits(["Vale Refeicao", "Plano"])
    assert [b.source for b in out] == ["inline", "inline"]
    assert [b.benefit_id for b in out] == [None, None]


def test_parse_id_name_becomes_catalog():
    out = parse_vaga_benefits([{"id": "abc", "name": "Gympass"}, {"name": "Day Off"}])
    assert (out[0].source, out[0].benefit_id) == ("catalog", "abc")
    assert (out[1].source, out[1].benefit_id) == ("inline", None)


def test_parse_full_snapshot_preserved():
    out = parse_vaga_benefits([{
        "benefit_id": "u1", "source": "catalog", "name": "Plano",
        "category": "health", "value_type": "informative", "seniority_levels": ["all"],
    }])
    assert out[0].category == "health"
    assert out[0].seniority_levels == ["all"]


def test_parse_none_and_single():
    assert parse_vaga_benefits(None) == []
    assert len(parse_vaga_benefits("Vale")) == 1


def test_parse_never_drops_unknown():
    # dict sem name nem id -> descartado (nada utilizavel); demais preservados
    out = parse_vaga_benefits(["X", {"name": "Y"}, {}])
    assert sorted(b.name for b in out) == ["X", "Y"]


def test_to_rails_names_and_jsonb():
    raw = ["A", {"id": "1", "name": "B"}]
    assert to_rails_names(raw) == ["A", "B"]
    j = vaga_benefits_to_jsonb(parse_vaga_benefits(raw))
    assert all("attached_at" in d and "source" in d for d in j)


def test_snapshot_from_catalog_dict():
    vb = snapshot_from_catalog(
        {"id": "x", "name": "Plano", "category": "health", "seniority_levels": ["junior"]},
        overrides={"value_details": "so nesta vaga"},
    )
    assert vb.source == "catalog" and vb.benefit_id == "x"
    assert vb.catalog_overrides == {"value_details": "so nesta vaga"}
    assert vb.value_details == "so nesta vaga"


# --- match keys EN catalogo <-> PT vaga ------------------------------------
@pytest.mark.parametrize("en,pt", [
    ("director", "Diretor"), ("c-level", "Diretor"), ("manager", "Gerente"),
    ("coordinator", "Coordenador"), ("senior", "Senior"), ("junior", "Junior"),
    ("staff", "Especialista"), ("intern", "Estagio"),
])
def test_seniority_match_key_bilingual(en, pt):
    assert to_match_seniority_key(en) == to_match_seniority_key(pt)


@pytest.mark.parametrize("en,pt", [("clt", "CLT"), ("pj", "PJ"), ("intern", "Estagio")])
def test_contract_match_key_bilingual(en, pt):
    assert to_match_contract_key(en) == to_match_contract_key(pt)


# --- repo matching logic (static) ------------------------------------------
def _sk(v):
    return to_match_seniority_key(v)


def test_dimension_empty_matches_all():
    assert CompanyBenefitRepository._matches_dimension_list([], _sk("Diretor"), _sk) is True


def test_dimension_all_wildcard():
    assert CompanyBenefitRepository._matches_dimension_list(["all"], _sk("Junior"), _sk) is True


def test_dimension_bilingual_match_and_miss():
    assert CompanyBenefitRepository._matches_dimension_list(["director"], _sk("Diretor"), _sk) is True
    assert CompanyBenefitRepository._matches_dimension_list(["junior"], _sk("Diretor"), _sk) is False


def test_department_matching():
    dp = CompanyBenefitRepository._matches_department
    assert dp({}, "Engenharia") is True
    assert dp({"Engenharia": True, "RH": False}, "engenharia") is True
    assert dp({"RH": True}, "Engenharia") is False
    assert dp({"all": True}, "Qualquer") is True
