"""
FASE 3 — State leak between vacancies (Fase 3 fix).

Regression guard: when a completed wizard session is reused for a NEW wizard
in the same browser session (same session_id), the LangGraph checkpoint MUST
be wiped before the new graph run begins, so intake_node does NOT inherit
job_id / calibration_candidates / jd_enriched from the previous vacancy.

Root cause (confirmed A3): thread_id = wiz-{company_token}-{session_id} is
NOT per-vacancy. Service only reset prior_state = {} (local Python dict),
without calling graph.update_state() to wipe the checkpoint. LangGraph loaded
old checkpoint → intake_node short-circuited with old vacancy data.

Fix: _wipe_terminal_checkpoint() calls graph.update_state(config, _WIZARD_FRESH_FIELDS)
before graph.invoke() whenever terminal stage is detected.
"""
from unittest.mock import MagicMock
import pytest


def _make_terminal_state():
    return {
        "job_id": 999,
        "parsed_title": "Engenheiro de Software Backend",
        "jd_enriched": {"titulo_padronizado": "Engenheiro Backend"},
        "jd_enriched_present": True,
        "calibration_candidates": [{"id": "c1"}, {"id": "c2"}],
        "calibration_complete": False,
        "intake_approved": True,
        "current_stage": "completed",
        "conversation_messages": [{"role": "user", "content": "cria vaga"}],
    }


# ---------------------------------------------------------------------------
# Test 1: _WIZARD_FRESH_FIELDS constant exists with required keys
# ---------------------------------------------------------------------------

def test_wizard_fresh_fields_constant_exists():
    """_WIZARD_FRESH_FIELDS must contain all critical per-vacancy keys.

    V1 audit 2026-06-21 expanded the set from 15 to 19 fields by detecting
    4 critical orphans: wsi_questions, questions_approved, eligibility_questions,
    stage_history. Also corrected parsed_work_model -> parsed_model.
    """
    from app.domains.job_creation.services.wizard_session_service import _WIZARD_FRESH_FIELDS

    required_keys = {
        # original 15 (minus parsed_work_model which was wrong name)
        "job_id",
        "parsed_title",
        "parsed_seniority",
        "parsed_department",
        "parsed_location",
        "parsed_model",            # corrected: was parsed_work_model
        "jd_enriched",
        "jd_enriched_present",
        "intake_approved",
        "intake_salary_suggested",
        "gate_resume_message",
        "calibration_candidates",
        "calibration_complete",
        "conversation_messages",
        "current_stage",
        # V1 audit additions (4 critical orphans)
        "wsi_questions",
        "questions_approved",
        "eligibility_questions",
        "stage_history",
    }
    missing = required_keys - set(_WIZARD_FRESH_FIELDS.keys())
    assert not missing, f"_WIZARD_FRESH_FIELDS missing keys: {missing}"

    # parsed_work_model must NOT be in the constant (wrong field name)
    assert "parsed_work_model" not in _WIZARD_FRESH_FIELDS, (
        "parsed_work_model is not a field in JobCreationState — use parsed_model"
    )

    # Values must be falsy/empty — no stale data in the constant itself
    assert _WIZARD_FRESH_FIELDS["job_id"] is None
    assert _WIZARD_FRESH_FIELDS["parsed_title"] == ""
    assert _WIZARD_FRESH_FIELDS["jd_enriched"] is None
    assert _WIZARD_FRESH_FIELDS["calibration_candidates"] == []
    assert _WIZARD_FRESH_FIELDS["conversation_messages"] == []
    assert _WIZARD_FRESH_FIELDS["wsi_questions"] == []
    assert _WIZARD_FRESH_FIELDS["eligibility_questions"] == []
    assert _WIZARD_FRESH_FIELDS["questions_approved"] is None
    assert _WIZARD_FRESH_FIELDS["stage_history"] == []


# ---------------------------------------------------------------------------
# Test 2: _wipe_terminal_checkpoint calls update_state with fresh fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wipe_terminal_checkpoint_calls_update_state():
    """_wipe_terminal_checkpoint must call graph.update_state with _WIZARD_FRESH_FIELDS."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
        _WIZARD_FRESH_FIELDS,
    )

    mock_graph = MagicMock()
    mock_graph._graph = MagicMock()
    mock_graph._graph.update_state = MagicMock(return_value=None)

    thread_id = "wiz-abc123-session-42"
    await WizardSessionService._wipe_terminal_checkpoint(thread_id, mock_graph)

    mock_graph._graph.update_state.assert_called_once()
    call_args = mock_graph._graph.update_state.call_args[0]
    assert call_args[0] == {"configurable": {"thread_id": thread_id}}, (
        f"Wrong config passed to update_state: {call_args[0]}"
    )
    actual_values = call_args[1]
    for key, val in _WIZARD_FRESH_FIELDS.items():
        assert key in actual_values, f"update_state missing key: {key}"
        assert actual_values[key] == val, f"Wrong value for {key}: {actual_values[key]!r}"


# ---------------------------------------------------------------------------
# Test 3: _wipe_terminal_checkpoint is a classmethod accessible from class
# ---------------------------------------------------------------------------

def test_wipe_terminal_checkpoint_is_classmethod():
    """_wipe_terminal_checkpoint must be a classmethod on WizardSessionService."""
    from app.domains.job_creation.services.wizard_session_service import WizardSessionService
    import inspect

    assert hasattr(WizardSessionService, "_wipe_terminal_checkpoint"), (
        "WizardSessionService missing _wipe_terminal_checkpoint"
    )
    method = WizardSessionService.__dict__.get("_wipe_terminal_checkpoint")
    assert isinstance(method, classmethod), (
        "_wipe_terminal_checkpoint must be a classmethod"
    )


# ---------------------------------------------------------------------------
# Test 4: Terminal guard in process_message calls _wipe (code-level check)
# ---------------------------------------------------------------------------

def test_terminal_guard_calls_wipe_in_source():
    """process_message source must call _wipe_terminal_checkpoint on terminal stage."""
    import inspect
    from app.domains.job_creation.services.wizard_session_service import WizardSessionService

    source = inspect.getsource(WizardSessionService.process_message)
    assert "_wipe_terminal_checkpoint" in source, (
        "process_message does not call _wipe_terminal_checkpoint on terminal stage. "
        "Fase 3 fix missing from process_message (graph path)."
    )


# ---------------------------------------------------------------------------
# Test 5: intake_node does NOT short-circuit after fresh fields applied
# ---------------------------------------------------------------------------

def test_intake_shortcircuit_broken_after_fresh_fields():
    """After _WIZARD_FRESH_FIELDS is applied, intake_node's short-circuit must not fire."""
    from app.domains.job_creation.services.wizard_session_service import _WIZARD_FRESH_FIELDS

    # Merged state: old terminal checkpoint overwritten by fresh fields
    state_after_wipe = {**_make_terminal_state(), **_WIZARD_FRESH_FIELDS}

    parsed_title = state_after_wipe.get("parsed_title")
    jd_enriched = state_after_wipe.get("jd_enriched")
    gate_resume = state_after_wipe.get("gate_resume_message")
    intake_salary = state_after_wipe.get("intake_salary_suggested")
    intake_approved = state_after_wipe.get("intake_approved")

    # Replicate intake_node short-circuit condition (nodes/intake.py ~L215):
    would_shortcircuit = bool(
        parsed_title and (jd_enriched or gate_resume or intake_salary or intake_approved is True)
    )
    assert not would_shortcircuit, (
        f"intake_node STILL short-circuits after wipe! "
        f"parsed_title={parsed_title!r}, jd_enriched={bool(jd_enriched)}, "
        f"intake_approved={intake_approved!r}"
    )


# ---------------------------------------------------------------------------
# Test 6: A3 REGRESSION — full A3 scenario: B is clean after A terminal
# ---------------------------------------------------------------------------

def test_a3_regression_b_is_clean_after_a_terminal():
    """V5 gap: actual A3 scenario regression test.

    Simulates vacancy A completing (current_stage='completed') with ALL
    per-vacancy fields populated across all stages. Then applies
    _WIZARD_FRESH_FIELDS (simulating update_state). Asserts that Vacancy B
    inherits NONE of the 19 critical fields from A.
    """
    from app.domains.job_creation.services.wizard_session_service import _WIZARD_FRESH_FIELDS

    # Full vacancy A final state — all stages populated
    vacancy_a = {
        "job_id": 42,
        "parsed_title": "Engenheiro de Software Backend Senior",
        "parsed_seniority": "senior",
        "parsed_department": "Engenharia de Produto",
        "parsed_location": {"city": "Sao Paulo"},
        "parsed_model": "hibrido",
        "jd_enriched": {"titulo_padronizado": "Engenheiro Backend Senior"},
        "jd_enriched_present": True,
        "intake_approved": True,
        "intake_salary_suggested": True,
        "gate_resume_message": "Retomando criacao da vaga.",
        "wsi_questions": [
            {"id": "q1", "question": "Descreva experiencia com Python.", "block": "technical"},
        ],
        "questions_approved": True,
        "eligibility_questions": [{"id": "e1", "question": "Possui CNH?"}],
        "stage_history": ["intake", "jd_enrichment", "wsi_questions", "calibration"],
        "calibration_candidates": [
            {"id": "c1", "name": "Joao", "decision": "approved"},
            {"id": "c2", "name": "Maria", "decision": "rejected"},
        ],
        "calibration_complete": True,
        "conversation_messages": [
            {"role": "user", "content": "cria vaga de engenheiro senior"},
        ],
        "current_stage": "completed",
        # Additional fields not in wipe (LOW/MEDIUM severity)
        "salary_min": 12000,
        "salary_max": 18000,
        "screening_mode": "standard",
    }

    # Apply wipe: simulate update_state(config, _WIZARD_FRESH_FIELDS)
    # LangGraph last-value reducer: FRESH_FIELDS keys REPLACE A's values
    state_b = {**vacancy_a, **_WIZARD_FRESH_FIELDS}

    # Assert ALL 19 fields are clean in B
    assert state_b["job_id"] is None, "LEAK: job_id from A survived → B would overwrite A's vacancy"
    assert state_b["parsed_title"] == "", "LEAK: parsed_title → intake_node would short-circuit"
    assert state_b["parsed_seniority"] == ""
    assert state_b["parsed_department"] == ""
    assert state_b["parsed_location"] is None
    assert state_b["parsed_model"] == ""
    assert state_b["jd_enriched"] is None, "LEAK: jd_enriched → intake_node would short-circuit"
    assert state_b["jd_enriched_present"] is False
    assert state_b["intake_approved"] is None, "LEAK: intake_approved → intake stage skipped"
    assert state_b["intake_salary_suggested"] is False
    assert state_b["gate_resume_message"] == ""
    assert state_b["wsi_questions"] == [], "LEAK: wsi_questions from A → B shows wrong questions"
    assert state_b["questions_approved"] is None, "LEAK: questions_approved=True → question gen skipped"
    assert state_b["eligibility_questions"] == [], "LEAK: eligibility_questions from A → B shows wrong questions"
    assert state_b["stage_history"] == [], "LEAK: stage_history from A → supervisor routing confused"
    assert state_b["calibration_candidates"] == [], "LEAK: calibration_candidates from A → B shows old candidates"
    assert state_b["calibration_complete"] is False, "LEAK: calibration_complete=True → calibration skipped"
    assert state_b["conversation_messages"] == [], "LEAK: conversation_messages → B sees A's chat history"
    assert state_b["current_stage"] is None, "LEAK: current_stage from A → routing starts at wrong stage"

    # Also verify intake short-circuit is broken (the original Fase 3 bug)
    would_shortcircuit = bool(
        state_b.get("parsed_title") and (
            state_b.get("jd_enriched")
            or state_b.get("gate_resume_message")
            or state_b.get("intake_salary_suggested")
            or state_b.get("intake_approved") is True
        )
    )
    assert not would_shortcircuit, (
        "intake_node STILL short-circuits after wipe — Fase 3 fix is broken"
    )
