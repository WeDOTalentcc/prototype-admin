"""TDD — item #3 sub-item: idiomas (confirm_languages + normalizador + persist)."""
from __future__ import annotations
import pytest
from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext, _handle_confirm_languages, build_tool_registry,
)
from app.domains.job_creation.helpers.vacancy_vocab import to_canonical_language_level

CTX = ToolContext(company_id="c1")


@pytest.mark.easy
@pytest.mark.parametrize("inp,exp", [
    ("avancado", "Avançado"), ("Avançado", "Avançado"), ("basico", "Básico"),
    ("fluente", "Fluente"), ("nativo", "Nativo"), ("intermediario", "Intermediário"),
    (None, "Intermediário"), ("xpto", "Intermediário"),
])
def test_language_level_norm(inp, exp):
    assert to_canonical_language_level(inp) == exp


@pytest.mark.easy
def test_confirm_languages_basic():
    res = _handle_confirm_languages({}, {"languages": [{"language": "Inglês", "level": "avançado"}]}, CTX)
    assert not res.error
    out = res.state_updates["confirmed_languages"]
    assert out == [{"language": "Inglês", "level": "Avançado", "required": False}]


@pytest.mark.easy
def test_confirm_languages_string_items():
    res = _handle_confirm_languages({}, {"languages": ["Espanhol"]}, CTX)
    assert not res.error
    assert res.state_updates["confirmed_languages"][0]["language"] == "Espanhol"
    assert res.state_updates["confirmed_languages"][0]["level"] == "Intermediário"  # default


@pytest.mark.easy
def test_confirm_languages_requires_list():
    assert _handle_confirm_languages({}, {}, CTX).error


@pytest.mark.easy
def test_confirm_languages_rejects_tenant():
    assert _handle_confirm_languages({}, {"languages": ["x"], "company_id": "y"}, CTX).error


@pytest.mark.easy
def test_registry_has_confirm_languages():
    assert "confirm_languages" in build_tool_registry()
