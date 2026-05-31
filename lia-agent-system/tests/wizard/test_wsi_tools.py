"""TDD — generate_wsi_questions + approve_wsi_questions (metodologia WSI).

Mocka os nós canônicos (bigfive_node, wsi_questions_node) para testar a tool
sem LLM. Valida: prereq JD, derivação de distribution das competências
confirmadas, multi-tenancy, fail-loud, aprovação HITL #2.
"""
from __future__ import annotations
from unittest.mock import patch
import pytest

from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
from app.domains.job_creation.orchestrator.wizard_service_tools import (
    _handle_generate_wsi_questions, _handle_approve_wsi_questions,
)

CTX = ToolContext(company_id="c1")

_QS = [
    {"block": "technical", "question": "Q1", "bloom_level": 4, "dreyfus_level": 3},
    {"block": "technical", "question": "Q2", "bloom_level": 5, "dreyfus_level": 3},
    {"block": "behavioral", "question": "Q3", "trait_ocean": "conscientiousness"},
]


@pytest.mark.medium
def test_generate_wsi_requires_jd():
    res = _handle_generate_wsi_questions({}, {}, CTX)
    assert res.error
    assert "descrição" in res.llm_message.lower()


@pytest.mark.medium
def test_generate_wsi_rejects_tenant_keys():
    res = _handle_generate_wsi_questions({"jd_enriched": {"x": 1}}, {"company_id": "y"}, CTX)
    assert res.error and "tenant" in res.llm_message.lower()


@pytest.mark.medium
def test_generate_wsi_happy_path_derives_distribution_from_confirmed():
    captured = {}

    def _fake_bigfive(state):
        return {**state, "trait_rankings": [{"trait": "C", "rank": 1}], "bigfive_profile": {"openness": 0.5}}

    def _fake_wsi_node(state):
        captured["distribution"] = state.get("question_distribution")
        captured["seniority"] = state.get("seniority_resolved")
        captured["trait_rankings"] = state.get("trait_rankings")
        return {**state, "wsi_questions": _QS}

    state = {
        "jd_enriched": {"about_role": "x"}, "parsed_seniority": "senior",
        "screening_mode": "full",
        "confirmed_technical_competencies": [{"skill": f"T{i}"} for i in range(8)],
        "confirmed_behavioral_competencies": [{"competencia": f"B{i}"} for i in range(4)],
    }
    with patch("app.domains.job_creation.nodes.bigfive.bigfive_node", _fake_bigfive), \
         patch("app.domains.job_creation.nodes.wsi_questions.wsi_questions_node", _fake_wsi_node):
        res = _handle_generate_wsi_questions(state, {}, CTX)

    assert not res.error
    # distribution derivada das competências confirmadas (8 + 4)
    assert captured["distribution"] == {"technical": 8, "behavioral": 4}
    assert captured["seniority"] == "senior"
    # bigfive rodou (full methodology) → trait_rankings disponível
    assert captured["trait_rankings"] == [{"trait": "C", "rank": 1}]
    assert res.state_updates["wsi_questions"] == _QS
    assert res.state_updates["questions_approved"] is None
    assert "CBI" in res.llm_message


@pytest.mark.medium
def test_generate_wsi_uses_table_when_no_confirmed():
    captured = {}

    def _fake_bigfive(state):
        return {**state, "trait_rankings": []}

    def _fake_wsi_node(state):
        captured["distribution"] = state.get("question_distribution")
        return {**state, "wsi_questions": _QS}

    state = {"jd_enriched": {"about_role": "x"}, "parsed_seniority": "pleno", "screening_mode": "compact"}
    with patch("app.domains.job_creation.nodes.bigfive.bigfive_node", _fake_bigfive), \
         patch("app.domains.job_creation.nodes.wsi_questions.wsi_questions_node", _fake_wsi_node), \
         patch("app.domains.job_creation.graph._get_question_distribution", return_value={"technical": 5, "behavioral": 2}) as gd:
        res = _handle_generate_wsi_questions(state, {}, CTX)
    assert not res.error
    assert gd.called  # caiu na tabela canônica
    assert captured["distribution"] == {"technical": 5, "behavioral": 2}


@pytest.mark.medium
def test_generate_wsi_bigfive_failsoft():
    """Se bigfive falhar, segue sem trait weighting (não quebra)."""
    def _boom(state):
        raise RuntimeError("bigfive down")

    def _fake_wsi_node(state):
        return {**state, "wsi_questions": _QS}

    state = {"jd_enriched": {"about_role": "x"}, "parsed_seniority": "pleno",
             "confirmed_technical_competencies": [{"skill": "T"}], "confirmed_behavioral_competencies": []}
    with patch("app.domains.job_creation.nodes.bigfive.bigfive_node", _boom), \
         patch("app.domains.job_creation.nodes.wsi_questions.wsi_questions_node", _fake_wsi_node):
        res = _handle_generate_wsi_questions(state, {}, CTX)
    assert not res.error
    assert res.state_updates["trait_rankings"] == []


@pytest.mark.medium
def test_generate_wsi_node_error_fail_loud():
    def _fake_bigfive(state):
        return {**state, "trait_rankings": []}

    def _fake_wsi_node(state):
        return {**state, "error": "policy DENY", "wsi_questions": []}

    state = {"jd_enriched": {"about_role": "x"}}
    with patch("app.domains.job_creation.nodes.bigfive.bigfive_node", _fake_bigfive), \
         patch("app.domains.job_creation.nodes.wsi_questions.wsi_questions_node", _fake_wsi_node):
        res = _handle_generate_wsi_questions(state, {}, CTX)
    assert res.error
    assert "policy DENY" in res.llm_message


@pytest.mark.medium
def test_approve_wsi_requires_questions():
    res = _handle_approve_wsi_questions({}, {}, CTX)
    assert res.error


@pytest.mark.medium
def test_approve_wsi_sets_flag():
    res = _handle_approve_wsi_questions({"wsi_questions": _QS}, {}, CTX)
    assert not res.error
    assert res.state_updates["questions_approved"] is True
