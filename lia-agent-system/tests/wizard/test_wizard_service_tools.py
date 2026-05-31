"""TDD — service-backed tools do orquestrador (suggest_competencies, enrich_jd).

Mocka os serviços canônicos (CompetencyBenchmarkService, JdEnrichmentService)
para testar a tool layer sem rede/DB. Valida: multi-tenancy invariant,
fail-loud (sem silent), guard de pré-requisitos, propagação de fallback.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
from app.domains.job_creation.orchestrator.wizard_service_tools import (
    _handle_suggest_competencies,
    _handle_enrich_job_description,
    _handle_suggest_salary,
    _handle_publish_job,
)

CTX = ToolContext(company_id="comp-xyz", user_id="u1", workspace_id=1)


# ── suggest_competencies ─────────────────────────────────────────────────


@pytest.mark.medium
def test_suggest_competencies_requires_title():
    res = _handle_suggest_competencies({}, {}, CTX)
    assert res.error
    assert "título" in res.llm_message.lower()


@pytest.mark.medium
def test_suggest_competencies_rejects_tenant_keys():
    res = _handle_suggest_competencies(
        {"parsed_title": "PM"}, {"company_id": "outra"}, CTX
    )
    assert res.error
    assert "tenant" in res.llm_message.lower()


@pytest.mark.medium
def test_suggest_competencies_happy_path_passes_company_from_ctx():
    captured = {}

    async def _fake_suggest(**kwargs):
        captured.update(kwargs)
        return {
            "technical": [{"skill": "Python"}, {"skill": "SQL"}],
            "behavioral": [{"competencia": "Comunicação"}],
            "is_estimate": False,
        }

    fake_svc = SimpleNamespace(suggest_competencies=_fake_suggest)

    with patch(
        "app.domains.analytics.services.competency_benchmark_service.get_competency_benchmark_service",
        return_value=fake_svc,
    ):
        res = _handle_suggest_competencies(
            {"parsed_title": "Eng", "parsed_seniority": "Sênior", "screening_mode": "full"},
            {},
            CTX,
        )

    assert not res.error
    # multi-tenancy: company_id veio do ctx, não do tool_input
    assert captured["company_id"] == "comp-xyz"
    assert captured["title"] == "Eng"
    assert captured["screening_mode"] == "full"
    # sugestões armazenadas (não confirmadas)
    assert res.state_updates["suggested_competencies"]["technical"][0]["skill"] == "Python"
    assert "Python" in res.llm_message


@pytest.mark.medium
def test_suggest_competencies_fail_loud_on_service_error():
    async def _boom(**kwargs):
        raise RuntimeError("LLM down")

    fake_svc = SimpleNamespace(suggest_competencies=_boom)
    with patch(
        "app.domains.analytics.services.competency_benchmark_service.get_competency_benchmark_service",
        return_value=fake_svc,
    ):
        res = _handle_suggest_competencies({"parsed_title": "Eng"}, {}, CTX)
    assert res.error
    # não silent: motivo explícito + caminho alternativo
    assert "confirm_competencies" in res.llm_message


# ── enrich_job_description ───────────────────────────────────────────────


@pytest.mark.medium
def test_enrich_requires_title():
    res = _handle_enrich_job_description({}, {}, CTX)
    assert res.error
    assert "título" in res.llm_message.lower()


@pytest.mark.medium
def test_enrich_happy_path_stores_jd_and_quality():
    class _Enriched:
        def model_dump(self):
            return {"title": "Eng", "summary": "..."}

    fake_service = SimpleNamespace(
        enrich=lambda **kw: (_Enriched(), 82.0, ["warn1"]),
    )

    with patch(
        "app.domains.job_creation.internal.services._get_jd_service",
        return_value=fake_service,
    ):
        res = _handle_enrich_job_description(
            {
                "parsed_title": "Engenheiro",
                "parsed_seniority": "Sênior",
                "confirmed_technical_competencies": [{"skill": "Python"}],
                "raw_input": "vaga de eng",
            },
            {},
            CTX,
        )

    assert not res.error
    assert res.state_updates["jd_enriched"]["title"] == "Eng"
    assert res.state_updates["jd_quality_score"] == 82.0
    assert res.state_updates["jd_approved"] is None
    assert res.state_updates["jd_enrichment_used_fallback"] is False


@pytest.mark.medium
def test_enrich_uses_fallback_and_flags_it():
    """Quando .enrich levanta, usa _fallback_enrichment e sinaliza (não silent)."""
    class _Enriched:
        def model_dump(self):
            return {"title": "Eng-fallback"}

    def _enrich_boom(**kw):
        raise RuntimeError("gemini 429")

    fake_service = SimpleNamespace(
        enrich=_enrich_boom,
        _fallback_enrichment=lambda *a, **kw: _Enriched(),
    )

    with patch(
        "app.domains.job_creation.internal.services._get_jd_service",
        return_value=fake_service,
    ), patch(
        "app.domains.job_creation.services.jd_enrichment.calculate_quality_score",
        return_value=(20.0, ["fallback"]),
    ):
        res = _handle_enrich_job_description(
            {"parsed_title": "Engenheiro", "raw_input": "x"}, {}, CTX
        )

    assert not res.error
    assert res.state_updates["jd_enrichment_used_fallback"] is True
    assert res.state_updates["jd_enrichment_fallback_reason"] == "RuntimeError"
    assert "reserva" in res.llm_message.lower()


# ── suggest_salary ───────────────────────────────────────────────────────


@pytest.mark.medium
def test_suggest_salary_requires_title():
    res = _handle_suggest_salary({}, {}, CTX)
    assert res.error
    assert "título" in res.llm_message.lower()


@pytest.mark.medium
def test_suggest_salary_extracts_range_from_node():
    def _fake_node(state):
        return {
            **state,
            "current_stage": "salary",  # NÃO deve vazar pro state_updates
            "salary_min": 8000,
            "salary_max": 14000,
            "salary_currency": "BRL",
            "salary_benchmark": {"source": "market"},
            "ws_stage_payload": {"x": 1},
        }

    with patch(
        "app.domains.job_creation.nodes.salary.salary_node", _fake_node
    ):
        res = _handle_suggest_salary({"parsed_title": "Eng"}, {}, CTX)

    assert not res.error
    assert res.state_updates["salary_min"] == 8000
    assert res.state_updates["salary_max"] == 14000
    # não vaza campos do nó (stage/payload)
    assert "current_stage" not in res.state_updates
    assert "ws_stage_payload" not in res.state_updates


@pytest.mark.medium
def test_suggest_salary_no_market_data_graceful():
    def _fake_node(state):
        return {**state, "salary_min": None, "salary_max": None}

    with patch("app.domains.job_creation.nodes.salary.salary_node", _fake_node):
        res = _handle_suggest_salary({"parsed_title": "Cargo Raro"}, {}, CTX)
    assert not res.error
    assert "recrutador" in res.llm_message.lower()


# ── publish_job ──────────────────────────────────────────────────────────


@pytest.mark.medium
def test_publish_requires_jd():
    res = _handle_publish_job({}, {"confirm": True}, CTX)
    assert res.error
    assert "descrição" in res.llm_message.lower()


@pytest.mark.medium
def test_publish_requires_jd_approved():
    res = _handle_publish_job(
        {"jd_enriched": {"x": 1}, "jd_approved": None}, {"confirm": True}, CTX
    )
    assert res.error
    assert "aprovada" in res.llm_message.lower()


@pytest.mark.medium
def test_publish_without_confirm_asks_for_it():
    """Sem confirm=true, NÃO publica — orienta obter confirmação (não é erro)."""
    state = {"jd_enriched": {"x": 1}, "jd_approved": True, "parsed_title": "PM"}
    res = _handle_publish_job(state, {}, CTX)
    assert not res.error
    assert "irreversível" in res.llm_message.lower()
    assert not res.state_updates  # nada publicado


@pytest.mark.medium
def test_publish_confirmed_calls_node_and_returns_job_id():
    captured = {}

    def _fake_publish(state):
        captured["policy_confirmed"] = state.get("policy_confirmed_publish")
        captured["company_id"] = state.get("company_id")
        return {**state, "job_id": 4242, "job_uid": "uid-42", "share_link": "http://x/y", "error": None}

    state = {"jd_enriched": {"x": 1}, "jd_approved": True, "parsed_title": "PM"}
    with patch("app.domains.job_creation.nodes.publish.publish_node", _fake_publish):
        res = _handle_publish_job(state, {"confirm": True}, CTX)

    assert not res.error
    # PolicyGate destravado + company_id do ctx
    assert captured["policy_confirmed"] is True
    assert captured["company_id"] == "comp-xyz"
    assert res.state_updates["job_id"] == 4242
    assert res.state_updates["current_stage"] == "done"
    assert "4242" in res.llm_message


@pytest.mark.medium
def test_publish_node_error_is_fail_loud():
    def _fake_publish(state):
        return {**state, "job_id": None, "error": "rails 500"}

    state = {"jd_enriched": {"x": 1}, "jd_approved": True}
    with patch("app.domains.job_creation.nodes.publish.publish_node", _fake_publish):
        res = _handle_publish_job(state, {"confirm": True}, CTX)
    assert res.error
    assert "rails 500" in res.llm_message


@pytest.mark.medium
def test_publish_rejects_tenant_keys():
    state = {"jd_enriched": {"x": 1}, "jd_approved": True}
    res = _handle_publish_job(state, {"confirm": True, "company_id": "outra"}, CTX)
    assert res.error
    assert "tenant" in res.llm_message.lower()
