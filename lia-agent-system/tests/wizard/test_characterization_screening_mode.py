"""
Characterization test — screening_mode coerce.

Observation from Fase 1 investigation:
  In _handle_suggest_competencies, `screening_mode = state.get("screening_mode") or "compact"`
  computes the coerce at line 70, but the computed value is NOT forwarded to
  suggest_competencies_canonical (not in the call at line 79-82). It is a dead variable
  in this handler — a separate latent bug tracked as part of bug 7.

What this test characterizes:
  The handler runs without error when screening_mode is absent or set.
  The VALUE of screening_mode (compact vs completo) does not affect the handler's output
  for this specific tool (since it's not forwarded). This guards against regressions
  where a future fix might accidentally break the handler when mode is None.

Phase 4 will add logger.warning to the coerce line and forward the value to canonical
  services that accept it. The RED test for the warning is in test_phase4_fail_loud_red.py.
"""
from __future__ import annotations
from unittest.mock import patch

from app.domains.job_creation.orchestrator.wizard_tools import ToolContext

CTX = ToolContext(company_id="comp-test", user_id="u1", workspace_id=1)


def _make_state(**overrides):
    return {
        "company_id": "comp-test",
        "parsed_title": "Especialista em Desenvolvimento Android",
        "parsed_seniority": "especialista",
        **overrides,
    }


_FAKE_SUGGESTION = {"technical": [], "behavioral": [], "is_estimate": False}


class TestScreeningModeCoerceDoesNotBreakHandler:
    """
    Documents: when screening_mode is absent or set, the handler runs without error.
    Phase 4 will add a warning on the coerce; this test must stay GREEN after that.
    """

    def test_handler_runs_cleanly_when_screening_mode_absent(self):
        """
        screening_mode=None is coerced to 'compact' internally, but does not crash
        the handler or return error=True.
        """
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_competencies,
        )

        state = _make_state(screening_mode=None)

        with patch(
            "app.domains.job_creation.orchestrator.wsi_canonical_adapter"
            ".suggest_competencies_canonical",
            return_value=_FAKE_SUGGESTION,
        ):
            result = _handle_suggest_competencies(state, {}, CTX)

        assert result is not None
        assert not result.error, (
            f"Handler returned error=True unexpectedly (mode=None). "
            f"Message: {result.llm_message!r}"
        )

    def test_handler_runs_cleanly_when_screening_mode_is_completo(self):
        """
        screening_mode='completo' does not crash the handler.
        """
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_competencies,
        )

        state = _make_state(screening_mode="completo")

        with patch(
            "app.domains.job_creation.orchestrator.wsi_canonical_adapter"
            ".suggest_competencies_canonical",
            return_value=_FAKE_SUGGESTION,
        ):
            result = _handle_suggest_competencies(state, {}, CTX)

        assert result is not None
        assert not result.error, (
            f"Handler returned error=True unexpectedly (mode='completo'). "
            f"Message: {result.llm_message!r}"
        )
