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
    {"block": "technical", "question": "Q3", "bloom_level": 3, "dreyfus_level": 2},
    {"block": "technical", "question": "Q4", "bloom_level": 4, "dreyfus_level": 3},
    {"block": "technical", "question": "Q5", "bloom_level": 5, "dreyfus_level": 4},
    {"block": "behavioral", "question": "Q6", "trait_ocean": "conscientiousness"},
    {"block": "behavioral", "question": "Q7", "trait_ocean": "openness"},
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


def _fake_pkg_question(**over):
    from types import SimpleNamespace
    base = dict(
        id="q1", question_text="Conte sobre X", block="technical", framework="CBI",
        competency="Python", skill="Python", trait_ocean=None, ideal_answer="ideal",
        scoring_criteria={"score_5": "ideal"}, bloom_level=5, dreyfus_level=None,
        weight=0.9, expected_signals=["a"], needs_manual_review=False, fallback_used=False,
    )
    base.update(over)
    return SimpleNamespace(**base)


@pytest.mark.medium
def test_generate_wsi_happy_path_uses_canonical_package():
    """Fase 2.4b: gera via canônico WSIService.generate_wsi_package — perguntas
    mapeadas p/ shape do painel + bigfive_profile + trait_rankings no state."""
    from types import SimpleNamespace
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst

    q = _fake_pkg_question()
    captured = {}

    async def _fake_pkg(**kw):
        captured.update(kw)
        return {"questions": [q], "bigfive_profile": {"openness": 0.6},
                "trait_rankings": [{"trait": "openness", "rank": 1}], "dropped": []}
    fake_svc = SimpleNamespace(generate_wsi_package=_fake_pkg)

    state = {"jd_enriched": {"about_role": "Engenheiro", "responsabilidades": ["liderar"]},
             "parsed_seniority": "senior", "screening_mode": "full", "salary_confirmed": True,
             "confirmed_technical_competencies": [{"skill": "Python"}],
             "confirmed_behavioral_competencies": [{"competencia": "Comunicacao"}]}
    with patch("app.domains.cv_screening.services.wsi_service.service.get_wsi_service", lambda: fake_svc):
        res = wst._handle_generate_wsi_questions(state, {}, CTX)

    assert not res.error
    assert captured["skills"] == ["Python"]
    assert captured["behavioral"] == ["Comunicacao"]
    assert captured["seniority"] == "senior"
    assert captured["mode"] == "full"
    pq = res.state_updates["wsi_questions"][0]
    assert pq["question"] == "Conte sobre X"
    assert pq["block"] == "technical" and pq["bloom_level"] == 5
    assert res.state_updates["bigfive_profile"] == {"openness": 0.6}
    assert res.state_updates["trait_rankings"] == [{"trait": "openness", "rank": 1}]
    assert res.state_updates["questions_approved"] is None
    assert "CBI" in res.llm_message


@pytest.mark.medium
def test_generate_wsi_reports_dropped_equity():
    """L4 fairness no canônico: perguntas descartadas viram aviso + audit no state."""
    from types import SimpleNamespace
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst

    q = _fake_pkg_question(trait_ocean=None)

    async def _fake_pkg(**kw):
        if kw.get("collect_dropped") is not None:
            kw["collect_dropped"].append({"question": "viesada", "category": "gender"})
        return {"questions": [q], "bigfive_profile": None, "trait_rankings": [], "dropped": []}
    fake_svc = SimpleNamespace(generate_wsi_package=_fake_pkg)

    with patch("app.domains.cv_screening.services.wsi_service.service.get_wsi_service", lambda: fake_svc):
        res = wst._handle_generate_wsi_questions({"jd_enriched": {"about_role": "x"}, "salary_skipped": True, "screening_mode": "compact"}, {}, CTX)
    assert not res.error
    assert "equidade" in res.llm_message.lower()
    assert len(res.state_updates["wsi_dropped_questions"]) == 1
    assert res.state_updates["wsi_dropped_questions"][0]["category"] == "gender"


@pytest.mark.medium
def test_generate_wsi_fail_loud_on_package_error():
    """Erro no canônico → fail-loud (ToolResult.error), nunca silent fallback."""
    from types import SimpleNamespace
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst

    async def _boom(**kw):
        raise RuntimeError("LLM down")
    fake_svc = SimpleNamespace(generate_wsi_package=_boom)

    with patch("app.domains.cv_screening.services.wsi_service.service.get_wsi_service", lambda: fake_svc):
        res = wst._handle_generate_wsi_questions({"jd_enriched": {"about_role": "x"}, "salary_skipped": True, "screening_mode": "compact"}, {}, CTX)
    assert res.error
    assert "tente novamente" in res.llm_message.lower()


@pytest.mark.medium
def test_generate_wsi_empty_questions_fail_loud():
    from types import SimpleNamespace
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst

    async def _empty(**kw):
        return {"questions": [], "bigfive_profile": None, "trait_rankings": [], "dropped": []}
    fake_svc = SimpleNamespace(generate_wsi_package=_empty)

    with patch("app.domains.cv_screening.services.wsi_service.service.get_wsi_service", lambda: fake_svc):
        res = wst._handle_generate_wsi_questions({"jd_enriched": {"about_role": "x"}, "salary_skipped": True, "screening_mode": "compact"}, {}, CTX)
    assert res.error


@pytest.mark.medium
def test_approve_wsi_requires_questions():
    res = _handle_approve_wsi_questions({}, {}, CTX)
    assert res.error


@pytest.mark.medium
def test_approve_wsi_sets_flag():
    res = _handle_approve_wsi_questions({"wsi_questions": _QS, "screening_mode": "compact"}, {}, CTX)
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
def test_regenerate_uses_canonical_package():
    """Fase 2.4b: regenerate também delega ao canônico generate_wsi_package."""
    from types import SimpleNamespace
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst

    q = _fake_pkg_question(question_text="nova", competency="A", skill="A")

    async def _fake_pkg(**kw):
        return {"questions": [q], "bigfive_profile": None, "trait_rankings": [], "dropped": []}
    fake_svc = SimpleNamespace(generate_wsi_package=_fake_pkg)

    state = {"jd_enriched": {"about_role": "x"}, "wsi_questions": list(_QS5), "questions_approved": True, "salary_skipped": True, "screening_mode": "compact",
             "confirmed_technical_competencies": [{"skill": "A"}], "confirmed_behavioral_competencies": []}
    with patch("app.domains.cv_screening.services.wsi_service.service.get_wsi_service", lambda: fake_svc):
        res = wst._handle_regenerate_wsi_questions(state, {}, CTX)
    assert not res.error
    assert res.state_updates["wsi_questions"][0]["question"] == "nova"
    assert res.state_updates["questions_approved"] is None


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


# ── Sensores Bug 2 (salário não pode ser pulado antes da triagem) ─────────
@pytest.mark.medium
def test_generate_wsi_blocked_when_salary_not_addressed():
    """Gate computacional: sem salário tratado, a triagem NÃO é gerada."""
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst
    res = wst._handle_generate_wsi_questions({"jd_enriched": {"about_role": "z"}}, {}, CTX)
    assert res.error
    assert "salário" in res.llm_message.lower()


@pytest.mark.medium
def test_generate_wsi_passes_when_salary_skipped():
    """Skip explícito do recrutador conta como salário tratado → libera triagem."""
    from types import SimpleNamespace
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst
    q = _fake_pkg_question()

    async def _fake_pkg(**kw):
        return {"questions": [q], "bigfive_profile": None, "trait_rankings": [], "dropped": []}
    fake_svc = SimpleNamespace(generate_wsi_package=_fake_pkg)
    state = {"jd_enriched": {"about_role": "z"}, "salary_skipped": True, "screening_mode": "compact"}
    with patch("app.domains.cv_screening.services.wsi_service.service.get_wsi_service", lambda: fake_svc):
        res = wst._handle_generate_wsi_questions(state, {}, CTX)
    assert not res.error


@pytest.mark.medium
def test_generate_wsi_passes_when_salary_suggested():
    """Sugestão emitida (suggest_salary) já conta como salário tratado."""
    from types import SimpleNamespace
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst
    q = _fake_pkg_question()

    async def _fake_pkg(**kw):
        return {"questions": [q], "bigfive_profile": None, "trait_rankings": [], "dropped": []}
    fake_svc = SimpleNamespace(generate_wsi_package=_fake_pkg)
    state = {"jd_enriched": {"about_role": "z"}, "intake_salary_suggested": True, "screening_mode": "compact"}
    with patch("app.domains.cv_screening.services.wsi_service.service.get_wsi_service", lambda: fake_svc):
        res = wst._handle_generate_wsi_questions(state, {}, CTX)
    assert not res.error
