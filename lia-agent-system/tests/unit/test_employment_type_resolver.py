"""Unit tests da funcao pura resolve_default_employment_type (FASE 1 E3).

Pina a precedencia da cadeia de heranca: parsed > departamento > empresa.
Sem DB — pura.
"""
from app.domains.job_creation.helpers.employment_type_resolver import (
    resolve_default_employment_type,
)


def test_parsed_wins_over_everything():
    assert resolve_default_employment_type(
        "PJ", {"primary_employment_type": "CLT"}, "Estagio", ["Temporario"]
    ) == "PJ"


def test_dept_primary_beats_company():
    assert resolve_default_employment_type(
        None, {"primary_employment_type": "PJ"}, "CLT", ["CLT", "Estagio"]
    ) == "PJ"


def test_dept_list_first_when_no_dept_primary():
    assert resolve_default_employment_type(
        None, {"employment_types": ["Freelancer", "PJ"]}, "CLT", ["CLT"]
    ) == "Freelancer"


def test_company_primary_when_no_dept():
    assert resolve_default_employment_type(None, None, "CLT", ["CLT", "PJ"]) == "CLT"


def test_company_list_first_when_no_primary():
    assert resolve_default_employment_type(None, {}, None, ["Estagio", "CLT"]) == "Estagio"


def test_none_when_nothing_available():
    assert resolve_default_employment_type(None, None, None, None) is None
    assert resolve_default_employment_type(None, {}, None, []) is None


def test_empty_strings_ignored():
    # parsed vazio nao conta; cai pro company primary
    assert resolve_default_employment_type("", None, "CLT", []) == "CLT"
