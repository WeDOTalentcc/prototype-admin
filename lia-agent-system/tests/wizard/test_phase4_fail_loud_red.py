"""
RED tests for Phase 4 — fail-loud cluster (bugs 7, 9, 12).
Tests marked xfail(strict=True) assert DESIRED behavior and currently FAIL.
strict=True forces CI to stay green; when Phase 4 fixes land, the marker must
be removed (xfail→pass becomes XPASS which strict=True treats as FAILURE).

Run to verify xfail state before Phase 4:
    pytest tests/wizard/test_phase4_fail_loud_red.py -v

Expected output before Phase 4:
  XFAIL  test_fallback_returns_exactly_count_questions[technical-5]
  XFAIL  test_fallback_returns_exactly_count_questions[behavioral-3]
  PASSED test_fallback_returns_exactly_count_questions[technical-1]   ← green anchor
  XFAIL  test_fallback_returns_exactly_count_questions[behavioral-7]
  XFAIL  test_warning_emitted_when_coercing_screening_mode
  XFAIL  test_benefits_handler_returns_error_true_on_service_failure
  XFAIL  test_variable_comp_handler_returns_error_true_on_service_failure
  XFAIL  test_benefits_happy_path_returns_actual_catalog  ← active bug 9b
  XFAIL  test_variable_comp_happy_path_returns_actual_catalog  ← active bug 9b

=== REGISTERED FINDINGS (do not remove — referenced by Phase plan) ===

FINDING A — Site 70: screening_mode dead variable (wizard_service_tools.py:70)
  `screening_mode = state.get("screening_mode") or "compact"` is computed but
  NOT forwarded to suggest_competencies_canonical (call at line 79-82 omits it).
  Phase 4 fix at site 70 must WIRE the variable to the call, not just add a warning.
  Adding a warning about a coerce that is then discarded is misleading.
  Decision before Phase 4: wire mode=screening_mode to suggest_competencies_canonical
  OR delete the variable. Reassess if the warning test should target site 70 or
  a site where mode IS actually forwarded (sites 548, 734, 976, 1247, 2354 — unverified).

FINDING B — E2E backstop is always SKIPPED (tests/e2e/test_wizard_job_creation.py)
  All 8 E2E tests skip in normal runs (require live server). The regression net
  for Phases 2–8 is inert in CI. Before relying on it as a backstop, a fixture
  that starts a test server (or a mock of the full orchestrator) must be wired.
  Tracked as tech debt; do not treat the 8 SKIPPED as 8 PASSED.
"""
from __future__ import annotations
import logging
from unittest.mock import patch, MagicMock
import pytest

from app.domains.job_creation.orchestrator.wizard_tools import ToolContext

CTX = ToolContext(company_id="comp-test", user_id="u1", workspace_id=1)


def _make_state(**overrides):
    return {
        "company_id": "comp-test",
        "parsed_title": "Especialista em Desenvolvimento Android",
        "parsed_seniority": "especialista",
        **overrides,
    }


# ── Bug 12: _fallback_questions ignores count ────────────────────────────────

class TestFallbackQuestionsCount:
    """
    _fallback_questions(block, count=N) must return exactly N questions.
    Currently always returns 1. Phase 4 fixes this.

    Parametrize xfail is per-case: count=1 is the green anchor (passes today).
    The other three are xfail(strict=True).
    """

    @pytest.mark.parametrize("block,count", [
        pytest.param("technical", 5,
                     marks=pytest.mark.xfail(reason="Bug 12 — _fallback_questions ignores count; Fase 4", strict=True)),
        pytest.param("behavioral", 3,
                     marks=pytest.mark.xfail(reason="Bug 12 — _fallback_questions ignores count; Fase 4", strict=True)),
        pytest.param("technical", 1),   # green anchor — retorna 1, count=1; SEM marker
        pytest.param("behavioral", 7,
                     marks=pytest.mark.xfail(reason="Bug 12 — _fallback_questions ignores count; Fase 4", strict=True)),
    ])
    def test_fallback_returns_exactly_count_questions(self, block, count):
        """
        Safe to instantiate via __new__: confirmed by inspection of
        wsi_question_generator.py:628 — method only uses `block` and `count` args
        plus local `weight = 1.0/max(count,1)`. No self.* attributes accessed.
        """
        from app.domains.job_creation.services.wsi_question_generator import (
            WSIQuestionGenerator,
        )
        gen = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        result = gen._fallback_questions(block=block, count=count)

        assert len(result) == count, (
            f"_fallback_questions(block={block!r}, count={count}) "
            f"returned {len(result)} questions, expected {count}. "
            "Phase 4 must fix: duplicate the single template to fill count."
        )


# ── Bug 7: screening_mode coerce without warning ─────────────────────────────

class TestScreeningModeWarning:
    """
    When screening_mode=None is coerced to 'compact', a logger.warning must be
    emitted. Currently no warning is emitted. Phase 4 adds it.

    SEE FINDING A above: site 70 is a dead variable — Phase 4 must also wire
    the mode to suggest_competencies_canonical, not only add the warning.
    Before Phase 4, reassess whether this test should target site 70 or a site
    where the mode is actually used.
    """

    @pytest.mark.xfail(
        reason="Bug 7 — no logger.warning on screening_mode coerce; Fase 4. "
               "See Finding A: site 70 is dead variable — Phase 4 must wire+warn.",
        strict=True,
    )
    def test_warning_emitted_when_coercing_screening_mode(self, caplog):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_competencies,
        )

        state = _make_state(screening_mode=None)

        with patch(
            "app.domains.job_creation.orchestrator.wsi_canonical_adapter"
            ".suggest_competencies_canonical",
            return_value={"technical": [], "behavioral": [], "is_estimate": False},
        ), caplog.at_level(
            logging.WARNING,
            logger="app.domains.job_creation.orchestrator.wizard_service_tools",
        ):
            _handle_suggest_competencies(state, {}, CTX)

        warning_msgs = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any("screening_mode" in m.lower() for m in warning_msgs), (
            "Phase 4 must add logger.warning when coercing screening_mode to 'compact'. "
            f"Warnings emitted: {warning_msgs or ['(none)']}"
        )


# ── Bugs 9 + 9b: benefits/variable_comp handlers broken ──────────────────────

class TestBenefitsHandlerFailLoud:
    """
    Both handlers exist at wizard_service_tools.py:1997 and :2093.

    === BUG 9 (active) — NameError on every call ===
    run_coro_in_threadpool is NOT imported at module level nor inside the
    function body (unlike every other handler in the file). It is called as
    the first statement inside `try:`. Since it is not in scope, Python raises
    NameError on EVERY call — before _fetch() ever runs. The except Exception
    catches NameError → returns fallback with error=False.

    VERDICT: Dispara em TODA chamada. Both features are COMPLETELY BROKEN
    in production today (stage benefits + variable_comp in wizard always show
    fallback, never the actual catalog). Not latent — active breakage.

    Priority: fix BEFORE Phase 4 error=False work (which is secondary).
    Fix: add `from app.domains.job_creation.helpers.async_audit import
    run_coro_in_threadpool` inside each handler (before the try block).

    === BUG 9b — error=False on failure ===
    After the NameError import fix is applied, the except block must return
    error=True, not error=False. This is the fail-silent bug proper.
    """

    @pytest.mark.xfail(
        reason="Bug 9b — _handle_suggest_benefits returns error=False on NameError "
               "(run_coro_in_threadpool not imported); Fase 4. "
               "See also test_benefits_happy_path_returns_actual_catalog for 9a.",
        strict=True,
    )
    def test_benefits_handler_returns_error_true_on_service_failure(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_benefits,
        )
        # No mock: handler raises NameError on run_coro_in_threadpool → caught silently
        result = _handle_suggest_benefits(_make_state(), {}, CTX)

        assert result.error is True, (
            "BUG 9b fail-silent (wizard_service_tools.py:2032-2035): "
            "_handle_suggest_benefits retorna error=False (via NameError silenciado). "
            "Phase 4: add explicit import + change error=False → error=True."
        )

    @pytest.mark.xfail(
        reason="Bug 9b — _handle_suggest_variable_compensation returns error=False "
               "on NameError (run_coro_in_threadpool not imported); Fase 4.",
        strict=True,
    )
    def test_variable_comp_handler_returns_error_true_on_service_failure(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_variable_compensation,
        )
        # No mock: same NameError path as benefits handler
        result = _handle_suggest_variable_compensation(_make_state(), {}, CTX)

        assert result.error is True, (
            "BUG 9b fail-silent (wizard_service_tools.py:2131-2135): "
            "_handle_suggest_variable_compensation retorna error=False (via NameError). "
            "Phase 4: add explicit import + change error=False → error=True."
        )

    @pytest.mark.xfail(
        reason="Bug 9a ACTIVE — _handle_suggest_benefits quebrado em TODA chamada: "
               "run_coro_in_threadpool não está importado no module scope nem dentro "
               "da função (wizard_service_tools.py:2030). NameError na primeira linha "
               "do try: → except → fallback sempre. _fetch() nunca é chamado. "
               "Feature completamente quebrada em prod. Fix: adicionar import explícito.",
        strict=True,
    )
    def test_benefits_happy_path_returns_actual_catalog(self):
        """
        When run_coro_in_threadpool is available (import fixed) and the DB returns
        benefits, the handler must populate state_updates['benefits'].
        Currently: NameError before _fetch() → fallback → state_updates empty.
        After Phase 4 import fix + DB mock: state_updates['benefits'] must be non-empty.
        """
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_benefits,
        )
        # No mock of run_coro_in_threadpool: triggers the NameError active bug
        result = _handle_suggest_benefits(_make_state(), {}, CTX)

        # After fix: state_updates must contain the catalog
        assert result.state_updates.get("benefits") is not None, (
            "Bug 9a ACTIVE: _handle_suggest_benefits never populates state_updates['benefits']. "
            "The handler always returns fallback because run_coro_in_threadpool is not imported "
            "at wizard_service_tools.py:2030. Fix: add explicit import before the try block."
        )

    @pytest.mark.xfail(
        reason="Bug 9a ACTIVE — _handle_suggest_variable_compensation quebrado em TODA "
               "chamada: run_coro_in_threadpool não importado (wizard_service_tools.py:2129). "
               "Feature completamente quebrada em prod. Fix: adicionar import explícito.",
        strict=True,
    )
    def test_variable_comp_happy_path_returns_actual_catalog(self):
        """
        When run_coro_in_threadpool is available and DB returns variable comp,
        the handler must populate state_updates['variable_compensation'].
        Currently: NameError → fallback → state_updates empty.
        """
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_variable_compensation,
        )
        result = _handle_suggest_variable_compensation(_make_state(), {}, CTX)

        assert result.state_updates.get("variable_compensation") is not None, (
            "Bug 9a ACTIVE: _handle_suggest_variable_compensation never populates "
            "state_updates['variable_compensation']. "
            "Fix: add `from app.domains.job_creation.helpers.async_audit import "
            "run_coro_in_threadpool` before the try block at wizard_service_tools.py:2129."
        )
