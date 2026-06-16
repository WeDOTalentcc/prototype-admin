"""B3 (fix 2026-05-31): painel de competências (add/remove) volta no orquestrador.

O orquestrador não tinha stage "competency" nem emitia competency_tree → o
CompetencyPanel nunca aparecia. Testes das funções puras.
"""
import pytest

from app.domains.job_creation.services.wizard_session_service import (
    _derive_wizard_stage,
    _competency_tree_for_panel,
)


@pytest.mark.medium
def test_stage_competency_when_suggested():
    st = {"suggested_competencies": {"technical": [{"skill": "Python"}], "behavioral": []}}
    assert _derive_wizard_stage(st) == "competency"


@pytest.mark.medium
def test_stage_competency_when_confirmed():
    st = {"confirmed_technical_competencies": [{"skill": "SQL"}]}
    assert _derive_wizard_stage(st) == "competency"


@pytest.mark.medium
def test_stage_jd_takes_priority_over_competency():
    st = {"confirmed_technical_competencies": [{"skill": "SQL"}], "jd_enriched": {"about_role": "x"}}
    assert _derive_wizard_stage(st) == "jd_enrichment"


@pytest.mark.medium
def test_stage_intake_when_nothing():
    assert _derive_wizard_stage({}) == "intake"


@pytest.mark.medium
def test_tree_from_confirmed_blocks_and_trait():
    st = {
        "confirmed_technical_competencies": [{"skill": "Python"}, {"skill": "SQL"}],
        "confirmed_behavioral_competencies": [{"competencia": "Liderança", "trait_big_five": "conscientiousness"}],
    }
    tree = _competency_tree_for_panel(st)
    tech = [t for t in tree if t["block"] == "technical"]
    behav = [t for t in tree if t["block"] == "behavioral"]
    assert {t["skill"] for t in tech} == {"Python", "SQL"}
    assert behav[0]["skill"] == "Liderança"
    assert behav[0]["trait"] == "conscientiousness"


@pytest.mark.medium
def test_tree_falls_back_to_suggested():
    st = {"suggested_competencies": {
        "technical": [{"skill": "Go"}],
        "behavioral": [{"competencia": "Comunicação", "trait_big_five": "extraversion"}],
    }}
    tree = _competency_tree_for_panel(st)
    assert any(t["skill"] == "Go" and t["block"] == "technical" for t in tree)
    assert any(t["skill"] == "Comunicação" and t["block"] == "behavioral" for t in tree)


@pytest.mark.medium
def test_tree_empty_when_no_competencies():
    assert _competency_tree_for_panel({}) == []
