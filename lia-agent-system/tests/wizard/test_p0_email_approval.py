"""TDD — P0 fixes (Paulo 2026-05-31): email determinístico + aprovação + masked guard."""
from __future__ import annotations

import pytest

from app.domains.job_creation.services.wizard_session_service import (
    _extract_manager_email,
)
from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext, _handle_set_job_fields, _handle_approve_job_description,
    build_tool_registry,
)

CTX = ToolContext(company_id="c1")


# ── email determinístico (servidor, bypass LLM) ──────────────────────────


@pytest.mark.easy
@pytest.mark.parametrize("text,expected", [
    ("gestor é paulo paulo.moraes@wedotalent.cc", "paulo.moraes@wedotalent.cc"),
    ("email: ana@empresa.com.br por favor", "ana@empresa.com.br"),
    ("sem email aqui", None),
    ("", None),
    ("dois a@x.com e b@y.com", "a@x.com"),  # primeiro
])
def test_extract_manager_email(text, expected):
    assert _extract_manager_email(text) == expected


# ── set_job_fields ignora email mascarado (não entra em loop) ────────────


@pytest.mark.easy
def test_set_job_fields_skips_masked_email_no_error():
    res = _handle_set_job_fields(
        {}, {"manager_email": "[EMAIL REMOVIDO]", "department": "Tec"}, CTX
    )
    assert not res.error  # NÃO erra (evita loop)
    assert "parsed_manager_email" not in res.state_updates  # não grava o placeholder
    assert res.state_updates["parsed_department"] == "Tec"
    assert "automaticamente" in res.llm_message.lower()


@pytest.mark.easy
def test_set_job_fields_only_masked_email_is_soft_note():
    res = _handle_set_job_fields({}, {"manager_email": "[EMAIL REMOVIDO]"}, CTX)
    assert not res.error
    assert not res.state_updates
    assert "automaticamente" in res.llm_message.lower()


@pytest.mark.easy
def test_set_job_fields_real_email_still_works():
    res = _handle_set_job_fields({}, {"manager_email": "ana@x.com"}, CTX)
    assert not res.error
    assert res.state_updates["parsed_manager_email"] == "ana@x.com"


# ── approve_job_description tool ─────────────────────────────────────────


@pytest.mark.easy
def test_approve_requires_jd():
    res = _handle_approve_job_description({}, {}, CTX)
    assert res.error
    assert "gere a jd" in res.llm_message.lower() or "descrição gerada" in res.llm_message.lower()


@pytest.mark.easy
def test_approve_sets_jd_approved():
    res = _handle_approve_job_description({"jd_enriched": {"x": 1}}, {}, CTX)
    assert not res.error
    assert res.state_updates["jd_approved"] is True


@pytest.mark.easy
def test_registry_includes_approve_tool():
    reg = build_tool_registry()
    assert "approve_job_description" in reg
