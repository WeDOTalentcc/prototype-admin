"""
Tests for candidate_fsm — GAP-05-001 (LOTE-002).

TDD: Red → Green → Refactor.
"""
import pytest

from app.services.state_machines.candidate_fsm import (
    TERMINAL_STAGES,
    validate_stage_transition,
)
from app.shared.errors import LIAInvalidStateTransition


class TestTerminalStages:
    def test_hired_is_terminal(self):
        assert "hired" in TERMINAL_STAGES

    def test_rejected_is_terminal(self):
        assert "rejected" in TERMINAL_STAGES

    def test_not_selected_is_terminal(self):
        assert "not_selected" in TERMINAL_STAGES

    def test_cancelled_is_terminal(self):
        assert "cancelled" in TERMINAL_STAGES

    def test_active_statuses_not_terminal(self):
        for status in ("sourced", "screening", "interview", "offer", "pending", "approved"):
            assert status not in TERMINAL_STAGES, f"{status} should not be terminal"


class TestValidateStageTransition:
    def test_non_terminal_to_any_allowed(self):
        for from_s in ("sourced", "screening", "interview", "offer", "pending"):
            for to_s in ("screening", "interview", "approved", "rejected"):
                validate_stage_transition(from_s, to_s)  # must not raise

    def test_none_from_always_allowed(self):
        for to_s in ("sourced", "hired", "rejected"):
            validate_stage_transition(None, to_s)  # initial placement, never raises

    def test_terminal_from_raises(self):
        for terminal in TERMINAL_STAGES:
            with pytest.raises(LIAInvalidStateTransition) as exc_info:
                validate_stage_transition(terminal, "screening")
            assert exc_info.value.http_status == 409
            assert terminal in exc_info.value.message

    def test_terminal_to_terminal_raises(self):
        with pytest.raises(LIAInvalidStateTransition):
            validate_stage_transition("rejected", "hired")

    def test_force_bypasses_terminal_block(self):
        for terminal in TERMINAL_STAGES:
            validate_stage_transition(terminal, "screening", force=True)  # must not raise

    def test_error_has_correct_details(self):
        with pytest.raises(LIAInvalidStateTransition) as exc_info:
            validate_stage_transition("hired", "offer")
        exc = exc_info.value
        assert exc.details["from_stage"] == "hired"
        assert exc.details["to_stage"] == "offer"
        assert "terminal_stages" in exc.details
        assert exc.recoverable is False

    def test_error_code(self):
        with pytest.raises(LIAInvalidStateTransition) as exc_info:
            validate_stage_transition("rejected", "pending")
        assert exc_info.value.code == "INVALID_STATE_TRANSITION"
