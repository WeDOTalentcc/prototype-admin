"""
Unit tests for RecruitmentTemplateService — Onda 5 (Frente C.2).

Cobre:
- suggest_template_type: 5 template types (technical, executive, operational, mass_hiring, intern)
- get_default_template: retorna template com stages
- Casos ambíguos: título genérico retorna fallback canônico
- SUPPORTED_TEMPLATE_TYPES: 5 tipos presentes
- suggest_template_type é puro (sem efeitos colaterais, sem DB)
- Aliases PT-BR: "engenheiro" → technical, "estagio" → intern, etc.
"""
from __future__ import annotations

import pytest

from app.domains.job_management.services.recruitment_template_service import (
    SUPPORTED_TEMPLATE_TYPES,
    get_default_template,
    suggest_template_type,
)


# ---------------------------------------------------------------------------
# T.2.1 — SUPPORTED_TEMPLATE_TYPES tem os 5 tipos canônicos
# ---------------------------------------------------------------------------

def test_supported_template_types_has_five():
    assert len(SUPPORTED_TEMPLATE_TYPES) == 5
    for expected in ("technical", "executive", "operational", "mass_hiring", "intern"):
        assert expected in SUPPORTED_TEMPLATE_TYPES


# ---------------------------------------------------------------------------
# T.2.2 — suggest_template_type: títulos técnicos → "technical"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title", [
    "Engenheiro de Software",
    "Desenvolvedor Python",
    "Dev Backend",
    "Data Scientist",
    "SRE",
    "Arquiteto de Soluções",
    "Product Manager",
    "QA Engineer",
    "Designer UX",
])
def test_suggest_technical_for_tech_roles(title: str):
    result = suggest_template_type(title)
    assert result == "technical", f"Expected 'technical' for '{title}', got '{result}'"


# ---------------------------------------------------------------------------
# T.2.3 — suggest_template_type: títulos executivos → "executive"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title", [
    "CEO",
    "CTO",
    "CFO",
    "Diretor de Tecnologia",
    "VP de Engenharia",
    "Head of Product",
    "C-level",
])
def test_suggest_executive_for_executive_roles(title: str):
    result = suggest_template_type(title)
    assert result == "executive", f"Expected 'executive' for '{title}', got '{result}'"


# ---------------------------------------------------------------------------
# T.2.4 — suggest_template_type: estágio → "intern"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title", [
    "Estágio em TI",
    "Estagiário de Marketing",
    "Programa de Estágio",
    "Trainee de Gestão",
    "Aprendiz",
])
def test_suggest_intern_for_intern_roles(title: str):
    result = suggest_template_type(title)
    assert result == "intern", f"Expected 'intern' for '{title}', got '{result}'"


# ---------------------------------------------------------------------------
# T.2.5 — suggest_template_type: operacional → "operational"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title", [
    "Atendente",
    "Operador de Caixa",
    "Auxiliar Administrativo",
    "Suporte ao Cliente",
    "Técnico de Suporte",
])
def test_suggest_operational_for_ops_roles(title: str):
    result = suggest_template_type(title)
    assert result == "operational", f"Expected 'operational' for '{title}', got '{result}'"


# ---------------------------------------------------------------------------
# T.2.6 — suggest_template_type: volume → "mass_hiring"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title, job_type", [
    ("Atendente", "mass_hiring"),
    ("Operador", "mass_hiring"),
])
def test_suggest_mass_hiring_via_job_type(title: str, job_type: str):
    result = suggest_template_type(title, job_type=job_type)
    assert result == "mass_hiring"


# ---------------------------------------------------------------------------
# T.2.7 — suggest_template_type: título ambíguo retorna valor válido
# ---------------------------------------------------------------------------

def test_ambiguous_title_returns_valid_type():
    result = suggest_template_type("Analista")
    assert result in SUPPORTED_TEMPLATE_TYPES


# ---------------------------------------------------------------------------
# T.2.8 — suggest_template_type: título vazio retorna válido
# ---------------------------------------------------------------------------

def test_empty_title_returns_valid_type():
    result = suggest_template_type("")
    assert result in SUPPORTED_TEMPLATE_TYPES


# ---------------------------------------------------------------------------
# T.2.9 — suggest_template_type: None retorna válido (sem crash)
# ---------------------------------------------------------------------------

def test_none_title_safe():
    result = suggest_template_type(None)
    assert result in SUPPORTED_TEMPLATE_TYPES


# ---------------------------------------------------------------------------
# T.2.10 — get_default_template: retorna estrutura canonical
# ---------------------------------------------------------------------------

def test_get_default_template_technical():
    template = get_default_template("technical")
    assert template is not None
    assert "stages" in template or "name" in template


def test_get_default_template_intern():
    template = get_default_template("intern")
    assert template is not None


def test_get_default_template_all_types():
    for ttype in SUPPORTED_TEMPLATE_TYPES:
        template = get_default_template(ttype)
        assert template is not None, f"get_default_template('{ttype}') returned None"


# ---------------------------------------------------------------------------
# T.2.11 — suggest_template_type é puro (idempotente para mesma entrada)
# ---------------------------------------------------------------------------

def test_suggest_template_type_is_idempotent():
    title = "Engenheiro de Software Sênior"
    r1 = suggest_template_type(title)
    r2 = suggest_template_type(title)
    assert r1 == r2
