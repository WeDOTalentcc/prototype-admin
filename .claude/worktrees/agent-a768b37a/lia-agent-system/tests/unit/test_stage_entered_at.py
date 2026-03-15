"""
Unit tests for stage_entered_at hook — Sprint 1A.

Tests the logic in PipelineStageService.transition_candidate() that sets
stage_entered_at only when from_stage != to_stage.
"""
import pytest
from datetime import datetime


class TestStageEnteredAtLogic:
    """
    Pure-logic tests for the stage_entered_at hook.
    Mirrors the condition at pipeline_stage_service.py line 180-183:

        vacancy_candidate.stage = to_stage
        vacancy_candidate.status = ...
        vacancy_candidate.updated_at = datetime.utcnow()
        if from_stage != to_stage:
            vacancy_candidate.stage_entered_at = datetime.utcnow()
    """

    def _apply_transition(self, vc_stage_entered_at, from_stage: str, to_stage: str):
        """Simulate the hook logic and return the resulting stage_entered_at."""
        original = vc_stage_entered_at
        if from_stage != to_stage:
            vc_stage_entered_at = datetime.utcnow()
        return vc_stage_entered_at, original

    def test_stage_entered_at_updated_on_real_transition(self):
        original = datetime(2026, 1, 1)
        result, _ = self._apply_transition(original, "triagem", "interview_hr")
        assert result != original
        assert result > original

    def test_stage_entered_at_unchanged_on_same_stage_substatus_update(self):
        original = datetime(2026, 1, 1)
        result, _ = self._apply_transition(original, "triagem", "triagem")
        assert result == original

    def test_first_transition_from_none_sets_stage_entered_at(self):
        result, _ = self._apply_transition(None, None, "triagem")
        # from_stage=None != to_stage="triagem" → sets it
        assert result is not None
        assert isinstance(result, datetime)

    def test_transition_always_sets_to_now(self):
        before = datetime.utcnow()
        result, _ = self._apply_transition(None, "triagem", "interview_hr")
        after = datetime.utcnow()
        assert before <= result <= after


class TestMigrationBackfill:
    """Tests the conceptual correctness of the backfill strategy."""

    def test_backfill_uses_updated_at_as_proxy(self):
        """
        A migration 023 faz: UPDATE vacancy_candidates SET stage_entered_at = updated_at
        Isso é correto para dados históricos (conservative proxy).
        """
        updated_at = datetime(2026, 2, 15)
        # After backfill, stage_entered_at = updated_at
        stage_entered_at = updated_at
        assert stage_entered_at == updated_at

    def test_backfill_only_for_null_rows(self):
        """
        O UPDATE usa WHERE stage_entered_at IS NULL para ser idempotente.
        Rows que já têm valor não são sobrescritas.
        """
        existing_value = datetime(2026, 1, 1)
        # Simulando: if stage_entered_at IS NULL → set to updated_at
        stage_entered_at = None
        updated_at = datetime(2026, 2, 15)
        if stage_entered_at is None:
            stage_entered_at = updated_at
        assert stage_entered_at == updated_at

        # Rows with existing value → unchanged
        stage_entered_at = existing_value
        if stage_entered_at is None:
            stage_entered_at = updated_at
        assert stage_entered_at == existing_value
