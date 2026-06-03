"""
Contract Test: update_competencies delta tool (orchestrator pure layer)
========================================================================
Pins the delta semantics of ``_handle_update_competencies`` on the live
wizard orchestrator path (LIA_WIZARD_ORCHESTRATOR=1):

  - add into empty list → canonical {"skill": ...} / {"competencia": ...}
  - remove existing (case-insensitive) → drops the item
  - add + remove in one call → both applied
  - fallback to suggested_competencies when confirmed_* absent
  - all deltas empty → error=True
  - tenant identity key in tool_input → error=True (multi-tenancy fail-closed)
  - duplicate add (case-insensitive) → no duplicate

Pure handler — no DB, no I/O. Imported directly.
"""
from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext,
    _handle_update_competencies,
)

CTX = ToolContext(company_id="company-123", user_id="user-1")


def _names(items, key):
    return [i[key] for i in items]


def test_add_technical_into_empty_list():
    state: dict = {}
    res = _handle_update_competencies(
        state, {"add_technical": ["Python"]}, CTX
    )
    assert res.error is False
    tech = res.state_updates["confirmed_technical_competencies"]
    assert tech == [{"skill": "Python", "contexto": ""}]
    assert res.state_updates["intake_competencies_suggested"] is True


def test_remove_behavioral_case_insensitive():
    state = {
        "confirmed_behavioral_competencies": [
            {"competencia": "Liderança", "contexto": "x", "trait_big_five": "C"},
            {"competencia": "Comunicação"},
        ]
    }
    res = _handle_update_competencies(
        state, {"remove_behavioral": ["liderança"]}, CTX
    )
    assert res.error is False
    behav = res.state_updates["confirmed_behavioral_competencies"]
    assert _names(behav, "competencia") == ["Comunicação"]


def test_add_and_remove_same_call():
    state = {
        "confirmed_technical_competencies": [{"skill": "Java"}],
    }
    res = _handle_update_competencies(
        state,
        {"add_technical": ["Go"], "remove_technical": ["java"]},
        CTX,
    )
    assert res.error is False
    tech = res.state_updates["confirmed_technical_competencies"]
    names = _names(tech, "skill")
    assert "Java" not in names
    assert "Go" in names


def test_fallback_to_suggested_when_confirmed_absent():
    state = {
        "suggested_competencies": {
            "technical": [{"skill": "SQL"}],
            "behavioral": [{"competencia": "Empatia"}],
        }
    }
    res = _handle_update_competencies(
        state, {"add_technical": ["NoSQL"]}, CTX
    )
    assert res.error is False
    tech = res.state_updates["confirmed_technical_competencies"]
    names = _names(tech, "skill")
    # operated on suggested as base → SQL preserved, NoSQL appended
    assert "SQL" in names
    assert "NoSQL" in names
    # behavioral suggested preserved untouched
    behav = res.state_updates["confirmed_behavioral_competencies"]
    assert _names(behav, "competencia") == ["Empatia"]


def test_all_deltas_empty_is_error():
    res = _handle_update_competencies({}, {}, CTX)
    assert res.error is True
    assert "adicionar ou remover" in res.llm_message.lower()


def test_tenant_key_rejected():
    res = _handle_update_competencies(
        {}, {"company_id": "other-co", "add_technical": ["Python"]}, CTX
    )
    assert res.error is True
    assert "tenant" in res.llm_message.lower()


def test_duplicate_add_does_not_duplicate():
    state = {"confirmed_technical_competencies": [{"skill": "Python"}]}
    res = _handle_update_competencies(
        state, {"add_technical": ["python", "PYTHON"]}, CTX
    )
    assert res.error is False
    tech = res.state_updates["confirmed_technical_competencies"]
    names = [t["skill"].lower() for t in tech]
    assert names.count("python") == 1


def test_confirmed_empty_list_does_not_fall_back_to_suggested():
    """Regressão: lista confirmada explicitamente vazia (recrutador removeu
    tudo) NÃO deve cair para ``suggested_competencies``. A base do delta
    permanece vazia, então um add não ressuscita as sugeridas."""
    state = {
        "confirmed_technical_competencies": [],
        "confirmed_behavioral_competencies": [],
        "suggested_competencies": {
            "technical": [{"skill": "SQL"}],
            "behavioral": [{"competencia": "Empatia"}],
        },
    }
    res = _handle_update_competencies(
        state, {"add_technical": ["Go"]}, CTX
    )
    assert res.error is False
    tech = res.state_updates["confirmed_technical_competencies"]
    names = _names(tech, "skill")
    # base vazia preservada → só o item adicionado, sem ressuscitar SQL
    assert names == ["Go"]
    # comportamentais confirmadas vazias continuam vazias (não voltam sugeridas)
    behav = res.state_updates["confirmed_behavioral_competencies"]
    assert behav == []


def test_remove_all_then_add_does_not_resurrect_removed_items():
    """Regressão (delta entre turnos): remover tudo e depois adicionar um item
    não deve trazer de volta os itens removidos via fallback de sugeridas."""
    # Turno 1: estado com confirmadas + sugeridas; remove a única confirmada.
    state = {
        "confirmed_technical_competencies": [{"skill": "Java"}],
        "suggested_competencies": {"technical": [{"skill": "Java"}, {"skill": "SQL"}]},
    }
    res1 = _handle_update_competencies(
        state, {"remove_technical": ["java"]}, CTX
    )
    assert res1.error is False
    assert res1.state_updates["confirmed_technical_competencies"] == []

    # Turno 2: aplica o state_updates (confirmadas agora == []) e adiciona Python.
    state2 = {
        **state,
        "confirmed_technical_competencies": res1.state_updates[
            "confirmed_technical_competencies"
        ],
    }
    res2 = _handle_update_competencies(
        state2, {"add_technical": ["Python"]}, CTX
    )
    assert res2.error is False
    names = _names(res2.state_updates["confirmed_technical_competencies"], "skill")
    # Java (removido) NÃO ressuscita; SQL (sugerida) NÃO aparece; só Python.
    assert names == ["Python"]
