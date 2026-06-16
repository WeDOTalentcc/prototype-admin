"""Sensor: seniority inference from title in wizard set_job_fields.

T4 — verifica que _handle_set_job_fields infere seniority deterministicamente
do titulo via _infer_from_title (regex, sem DB) quando seniority nao eh
fornecido explicitamente.
"""
from __future__ import annotations

import pytest

from app.domains.job_creation.orchestrator.wizard_tools import (
    _handle_set_job_fields,
    ToolContext,
)


def _ctx() -> ToolContext:
    return ToolContext(company_id="test-co")


def _call(fields: dict) -> tuple[dict, object]:
    state: dict = {}
    result = _handle_set_job_fields(state, fields, _ctx())
    if result.state_updates:
        state.update(result.state_updates)
    return state, result


class TestTitleSeniorityInference:
    """Seniority inference from title — deterministic regex."""

    def test_diretor_juridico_infers_diretor(self):
        state, result = _call({"title": "Diretor Jurídico"})
        assert state.get("parsed_seniority") == "diretor"
        assert not result.error
        assert "inferido" in result.llm_message.lower() or "inferid" in result.llm_message.lower()

    def test_analista_financeiro_no_seniority_inferred(self):
        """analista is NOT in TITLE_SENIORITY_PATTERNS — no inference."""
        state, result = _call({"title": "Analista Financeiro"})
        assert "parsed_seniority" not in state

    def test_explicit_seniority_not_overridden(self):
        """When both title and seniority provided, explicit seniority wins."""
        state, result = _call({"title": "Diretor Jurídico", "seniority": "senior"})
        assert state.get("parsed_seniority") == "senior"

    def test_tech_lead_infers_lead(self):
        state, result = _call({"title": "Tech Lead Backend"})
        assert state.get("parsed_seniority") == "lead"

    def test_estagiario_infers_estagiario(self):
        state, result = _call({"title": "Estagiário de Marketing"})
        assert state.get("parsed_seniority") == "estagiario"

    def test_senior_dev_infers_senior(self):
        state, result = _call({"title": "Desenvolvedor Sênior"})
        assert state.get("parsed_seniority") == "senior"

    def test_junior_analyst_infers_junior(self):
        state, result = _call({"title": "Analista Júnior de Dados"})
        assert state.get("parsed_seniority") == "junior"

    def test_no_title_no_inference(self):
        """Setting department alone does not trigger inference."""
        state, result = _call({"department": "Engenharia"})
        assert "parsed_seniority" not in state

    def test_inference_adds_provenance_note(self):
        """Result message includes provenance note for LLM."""
        state, result = _call({"title": "VP de Operações"})
        assert state.get("parsed_seniority") == "diretor"
        assert "confirme" in result.llm_message.lower() or "ajuste" in result.llm_message.lower()
