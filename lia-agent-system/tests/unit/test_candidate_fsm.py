"""Unit tests for candidate_fsm — GAP-05-001 Candidate Status FSM Validation."""
import pytest

from app.services.state_machines.candidate_fsm import (
    TERMINAL_STAGES,
    validate_stage_transition,
)
from app.shared.errors import LIAInvalidStateTransition


# ─── Terminal stage definitions ──────────────────────────────────────────────

def test_terminal_stages_not_empty():
    assert len(TERMINAL_STAGES) > 0


def test_terminal_stages_includes_canonical_values():
    assert "rejected" in TERMINAL_STAGES
    assert "hired" in TERMINAL_STAGES
    assert "cancelled" in TERMINAL_STAGES
    assert "not_selected" in TERMINAL_STAGES


# ─── FSM happy paths (no exception) ─────────────────────────────────────────

def test_allows_transition_from_none_from_stage():
    """Initial placement (no previous stage) is always allowed."""
    validate_stage_transition(None, "triagem_wsi")  # must not raise


def test_allows_transition_between_non_terminal_stages():
    validate_stage_transition("triagem_wsi", "entrevista_hr")
    validate_stage_transition("candidatura", "triagem_wsi")
    validate_stage_transition("applied", "awaiting_screening")


def test_allows_transition_to_terminal_from_non_terminal():
    """Moving INTO a terminal stage is allowed."""
    validate_stage_transition("entrevista_hr", "rejected")
    validate_stage_transition("entrevista_hr", "hired")
    validate_stage_transition("triagem_wsi", "cancelled")
    validate_stage_transition("candidatura", "not_selected")


# ─── FSM blocking paths ──────────────────────────────────────────────────────

@pytest.mark.parametrize("terminal_stage", sorted(TERMINAL_STAGES))
def test_blocks_transition_from_any_terminal_stage(terminal_stage):
    """All terminal stages must block further transitions."""
    with pytest.raises(LIAInvalidStateTransition) as exc_info:
        validate_stage_transition(terminal_stage, "entrevista_hr")
    err = exc_info.value
    assert err.code == "INVALID_STATE_TRANSITION"
    assert terminal_stage in err.details["from_stage"]
    assert err.details["terminal_stages"] == sorted(TERMINAL_STAGES)
    assert not err.recoverable


def test_blocked_exception_contains_from_and_to_stage():
    with pytest.raises(LIAInvalidStateTransition) as exc_info:
        validate_stage_transition("rejected", "triagem_wsi")
    err = exc_info.value
    assert err.details["from_stage"] == "rejected"
    assert err.details["to_stage"] == "triagem_wsi"


def test_blocks_terminal_to_terminal():
    """Even terminal → terminal is blocked (no re-adjudication)."""
    with pytest.raises(LIAInvalidStateTransition):
        validate_stage_transition("rejected", "hired")


# ─── force=True bypass ──────────────────────────────────────────────────────

@pytest.mark.parametrize("terminal_stage", sorted(TERMINAL_STAGES))
def test_force_bypasses_terminal_block(terminal_stage):
    """force=True allows admin correction of terminal states."""
    validate_stage_transition(terminal_stage, "entrevista_hr", force=True)  # no raise


def test_force_true_with_none_from_stage():
    validate_stage_transition(None, "rejected", force=True)  # no raise


# ─── LIAInvalidStateTransition error class ──────────────────────────────────

def test_lia_invalid_state_transition_is_conflict_subclass():
    from app.shared.errors import LIAConflictError
    err = LIAInvalidStateTransition()
    assert isinstance(err, LIAConflictError)


def test_lia_invalid_state_transition_http_status_409():
    err = LIAInvalidStateTransition()
    assert err.http_status == 409


def test_lia_invalid_state_transition_not_recoverable():
    err = LIAInvalidStateTransition()
    assert not err.recoverable


def test_lia_invalid_state_transition_default_code():
    err = LIAInvalidStateTransition()
    assert err.code == "INVALID_STATE_TRANSITION"
