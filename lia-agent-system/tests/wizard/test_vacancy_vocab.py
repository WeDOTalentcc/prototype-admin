"""TDD — item #3: normalização de vocabulário wizard → cadastro de vaga.

Sensor: garante que os valores internos do wizard mapeiam para o vocabulário
canônico do cadastro (FE edit-job-modal.constants.tsx). Sem isso o dropdown do
cadastro não casa (vaga abre com campo vazio).
"""
from __future__ import annotations
import pytest

from app.domains.job_creation.helpers.vacancy_vocab import (
    to_canonical_work_model, to_canonical_seniority, to_canonical_employment_type,
)


@pytest.mark.easy
@pytest.mark.parametrize("inp,exp", [
    ("hybrid", "híbrido"), ("hibrido", "híbrido"), ("remote", "remoto"),
    ("onsite", "presencial"), ("presencial", "presencial"), ("home office", "remoto"),
])
def test_work_model(inp, exp):
    assert to_canonical_work_model(inp) == exp


@pytest.mark.easy
@pytest.mark.parametrize("inp,exp", [
    ("diretor", "Diretor"), ("Diretor", "Diretor"), ("pleno", "Pleno"),
    ("senior", "Sênior"), ("sênior", "Sênior"), ("junior", "Júnior"),
    ("estagiario", "Estágio"), ("lead", "Coordenador"), ("principal", "Especialista"),
    ("gerente", "Gerente"), ("CEO", "Diretor"),
])
def test_seniority(inp, exp):
    assert to_canonical_seniority(inp) == exp


@pytest.mark.easy
@pytest.mark.parametrize("inp,exp", [
    ("CLT", "CLT"), ("clt", "CLT"), ("pj", "PJ"), ("estagio", "Estágio"),
    ("temporario", "Temporário"), ("freelancer", "Freelancer"), ("freela", "Freelancer"),
])
def test_employment_type(inp, exp):
    assert to_canonical_employment_type(inp) == exp


@pytest.mark.easy
def test_unmapped_preserved_not_lost():
    # valor desconhecido é preservado (não perde dado), não vira None/erro
    assert to_canonical_seniority("Arquiteto Chefe") == "Arquiteto Chefe"
    assert to_canonical_work_model("") == ""
    assert to_canonical_employment_type(None) is None


@pytest.mark.medium
def test_publish_node_imports_vocab():
    # garante que o boundary (publish_node) importa o normalizador sem quebrar
    import importlib
    m = importlib.import_module("app.domains.job_creation.nodes.publish")
    assert hasattr(m, "to_canonical_work_model")
    assert hasattr(m, "to_canonical_seniority")
