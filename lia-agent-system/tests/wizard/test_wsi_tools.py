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


# ── HITL ops: regenerate / remove / edit / add (paridade fluxo antigo) ────

_QS5 = [
    {"block": "technical", "question": f"T{i}", "bloom_level": 4} for i in range(1, 4)
] + [
    {"block": "behavioral", "question": f"B{i}", "trait_ocean": "C"} for i in range(1, 3)
]


@pytest.mark.medium
def test_remove_wsi_question_splices_1based():
    from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_remove_wsi_question
    res = _handle_remove_wsi_question({"wsi_questions": list(_QS5)}, {"question_index": 2}, CTX)
    assert not res.error
    qs = res.state_updates["wsi_questions"]
    assert len(qs) == 4
    assert qs[0]["question"] == "T1" and qs[1]["question"] == "T3"  # T2 removida
    assert res.state_updates["questions_approved"] is None


@pytest.mark.medium
def test_remove_wsi_invalid_index():
    from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_remove_wsi_question
    res = _handle_remove_wsi_question({"wsi_questions": list(_QS5)}, {"question_index": 99}, CTX)
    assert res.error and "inválido" in res.llm_message.lower()


@pytest.mark.medium
def test_regenerate_forces_regen():
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst
    captured = {}

    def _fake_bigfive(state):
        return {**state, "trait_rankings": []}

    def _fake_wsi_node(state):
        captured["force"] = state.get("wsi_regenerate_pending")
        return {**state, "wsi_questions": list(_QS5)}

    state = {"jd_enriched": {"about_role": "x"}, "wsi_questions": list(_QS5), "questions_approved": True,
             "confirmed_technical_competencies": [{"skill": "A"}], "confirmed_behavioral_competencies": []}
    with patch("app.domains.job_creation.nodes.bigfive.bigfive_node", _fake_bigfive), \
         patch("app.domains.job_creation.nodes.wsi_questions.wsi_questions_node", _fake_wsi_node):
        res = wst._handle_regenerate_wsi_questions(state, {}, CTX)
    assert not res.error
    assert captured["force"] is True  # forçou regeneração


@pytest.mark.medium
def test_edit_wsi_question_surgical():
    """Fase 2.4: edit delega ao canônico WSIService.suggest_single_question
    (via _wsi_suggest_single) — não mais ao fork WSIQuestionGenerator."""
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst

    captured = {}

    def _fake_single(state, *, instruction, block):
        captured.update(instruction=instruction, block=block)
        return {"success": True, "question": "T2 reescrita", "skill_targeted": "A", "bloom_level": 5}

    with patch.object(wst, "_wsi_suggest_single", _fake_single):
        res = wst._handle_edit_wsi_question(
            {"wsi_questions": list(_QS5), "jd_enriched": {"x": 1}},
            {"question_index": 2, "instruction": "mais específica"}, CTX,
        )
    assert not res.error
    assert captured["instruction"] == "mais específica"
    q = res.state_updates["wsi_questions"][1]
    assert q["question"] == "T2 reescrita"
    assert q["framework"] == "CBI"  # mapeado p/ shape do painel
    assert q["bloom_level"] == 5


@pytest.mark.medium
def test_add_wsi_question_surgical():
    """Fase 2.4: add delega ao canônico WSIService.suggest_single_question
    (via _wsi_suggest_single). block é autoritativo do wizard."""
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst

    def _fake_single(state, *, instruction, block):
        assert block == "behavioral"
        return {"success": True, "question": "nova comportamental", "skill_targeted": "Resiliência"}

    with patch.object(wst, "_wsi_suggest_single", _fake_single):
        res = wst._handle_add_wsi_question(
            {"wsi_questions": list(_QS5), "jd_enriched": {"x": 1}},
            {"block": "behavioral", "instruction": "avalie resiliência"}, CTX,
        )
    assert not res.error
    assert len(res.state_updates["wsi_questions"]) == 6
    assert res.state_updates["wsi_questions"][-1]["question"] == "nova comportamental"
    assert res.state_updates["wsi_questions"][-1]["block"] == "behavioral"


@pytest.mark.medium
def test_add_wsi_requires_existing():
    from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_add_wsi_question
    res = _handle_add_wsi_question({}, {"block": "technical"}, CTX)
    assert res.error
