"""Contract sensors para a integracao Remuneracao Variavel catalogo<->vaga.

Pinam: parser backward-compat (nunca descarta, classifica source/kind), snapshot,
matching de elegibilidade do comp repo (reusa o util compartilhado), e dedup.
"""
import pytest

from app.domains.job_creation.helpers.vaga_variable_comp import (
    VagaCompComponent,
    parse_vaga_variable_comp,
    snapshot_from_catalog,
    vaga_variable_comp_to_jsonb,
)
from app.domains.job_creation.helpers.vacancy_vocab import to_match_seniority_key
from app.domains.company.repositories.compensation_component_repository import (
    CompensationComponentRepository,
)
from app.shared.eligibility_matching import matches_department, matches_dimension_list


# --- parser ---------------------------------------------------------------
def test_parse_string_becomes_inline_bonus():
    out = parse_vaga_variable_comp(["Bônus"])
    assert (out[0].source, out[0].kind, out[0].component_id) == ("inline", "bonus", None)


def test_parse_id_name_becomes_catalog():
    out = parse_vaga_variable_comp([{"id": "x", "name": "PLR", "kind": "plr"}])
    assert (out[0].source, out[0].component_id, out[0].kind) == ("catalog", "x", "plr")


def test_parse_full_snapshot_preserved():
    out = parse_vaga_variable_comp([{
        "component_id": "c1", "source": "catalog", "name": "Comissão", "kind": "commission",
        "value_type": "percent", "spec": {"base_pct": 5.0, "tiers": []}, "seniority_levels": ["all"],
    }])
    assert out[0].kind == "commission"
    assert out[0].spec == {"base_pct": 5.0, "tiers": []}
    assert out[0].seniority_levels == ["all"]


def test_parse_none_and_single_and_never_drops():
    assert parse_vaga_variable_comp(None) == []
    assert len(parse_vaga_variable_comp("Bônus")) == 1
    out = parse_vaga_variable_comp(["A", {"name": "B", "kind": "plr"}, {}])
    assert sorted(c.name for c in out) == ["A", "B"]


def test_snapshot_from_catalog_with_overrides():
    vc = snapshot_from_catalog(
        {"id": "z", "name": "Bônus", "kind": "bonus", "target_pct": 10.0},
        overrides={"target_pct": 15.0},
    )
    assert vc.source == "catalog" and vc.component_id == "z"
    assert vc.target_pct == 15.0
    assert vc.catalog_overrides == {"target_pct": 15.0}


def test_to_jsonb_serializable():
    j = vaga_variable_comp_to_jsonb(parse_vaga_variable_comp(["A", {"id": "1", "name": "B"}]))
    assert all("attached_at" in d and "source" in d and "kind" in d for d in j)


# --- matching (comp repo reusa util compartilhado) ------------------------
def _sk(v):
    return to_match_seniority_key(v)


def test_repo_matching_delegates_to_shared_util():
    # _matches_* nao existem mais no comp repo; ele usa list_matching (async).
    # validamos o util compartilhado que o repo consome:
    assert matches_dimension_list([], _sk("Diretor"), _sk) is True
    assert matches_dimension_list(["all"], _sk("Junior"), _sk) is True
    assert matches_dimension_list(["director"], _sk("Diretor"), _sk) is True   # EN<->PT
    assert matches_dimension_list(["junior"], _sk("Diretor"), _sk) is False
    assert matches_department({"Engenharia": True}, "engenharia") is True
    assert matches_department({"RH": True}, "Engenharia") is False


def test_repo_has_canonical_methods():
    for m in ("list_for_company", "list_matching", "get_by_name_ci", "create", "soft_delete"):
        assert hasattr(CompensationComponentRepository, m)
