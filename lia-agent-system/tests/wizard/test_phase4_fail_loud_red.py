"""
RED tests for Phase 4 — fail-loud cluster (bugs 7, 12).
Tests marked xfail(strict=True) assert DESIRED behavior that currently FAILS.
strict=True forces CI to stay green; when the phase fix lands the marker must
be removed (XPASS with strict=True becomes FAILURE, forcing cleanup).

Bug 9 (9a + 9b) tests are now GREEN — fixes applied in commit that follows
the Fase 1 safety-net commit: import run_coro_in_threadpool + error=True.
Those tests have NO xfail marker and must PASS every run.

Expected output after Bug 9 fix, before Phase 4:
  PASSED  test_fallback_returns_exactly_count_questions[technical-1]  ← anchor
  XFAIL   test_fallback_returns_exactly_count_questions[technical-5]
  XFAIL   test_fallback_returns_exactly_count_questions[behavioral-3]
  XFAIL   test_fallback_returns_exactly_count_questions[behavioral-7]
  XFAIL   test_warning_emitted_when_coercing_screening_mode
  PASSED  test_benefits_handler_returns_error_true_on_service_failure   ← 9b
  PASSED  test_variable_comp_handler_returns_error_true_on_service_failure ← 9b
  PASSED  test_benefits_happy_path_returns_actual_catalog               ← 9a
  PASSED  test_variable_comp_happy_path_returns_actual_catalog          ← 9a

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
  for Phases 2-8 is inert in CI. Before relying on it as a backstop, a fixture
  that starts a test server (or a mock of the full orchestrator) must be wired.
  Tracked as tech debt; do not treat the 8 SKIPPED as 8 PASSED.

FINDING C — _fetch() UUID conversion (wizard_service_tools.py benefits handler)
  _fetch() inside _handle_suggest_benefits does UUID(str(company_id)) — a non-UUID
  string (e.g. "comp-test") silently returns [] → handler returns "nenhum catálogo".
  Happy-path tests therefore MUST use a UUID-format company_id to exercise the
  actual repository call path. Validated in test setup below.
"""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.domains.job_creation.orchestrator.wizard_tools import ToolContext

# Non-UUID company_id triggers ValueError in _fetch() → silently returns [].
# Use a valid UUID so the repo call path is actually exercised (Finding C above).
_VALID_UUID = "11111111-1111-1111-1111-111111111111"

CTX = ToolContext(company_id=_VALID_UUID, user_id="u1", workspace_id=1)


def _make_state(**overrides):
    base = {
        "company_id": _VALID_UUID,
        "parsed_title": "Especialista em Desenvolvimento Android",
        "parsed_seniority": "especialista",
    }
    base.update(overrides)
    return base


# Reusable fake async session (no real DB) — yields a plain AsyncMock.
# The repo is mocked at class level, so the db arg is irrelevant.
@asynccontextmanager
async def _fake_db_session():
    yield AsyncMock()


# ── Bug 12: _fallback_questions ignores count ────────────────────────────────

class TestFallbackQuestionsCount:
    """
    _fallback_questions(block, count=N) must return exactly N questions.
    Currently always returns 1. Phase 4 fixes this.

    Parametrize xfail is per-case: count=1 is the green anchor (passes today).
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
        Safe via __new__: confirmed by inspection of wsi_question_generator.py:628
        — method only uses `block` and `count` args + local weight. No self.* access.
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
    """

    @pytest.mark.xfail(
        reason=(
            "Bug 7 — no logger.warning on screening_mode coerce; Fase 4. "
            "See Finding A: site 70 is dead variable — Phase 4 must wire+warn."
        ),
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


# ── Bug 9 (fixed): benefits/variable_comp handlers ───────────────────────────

class TestBenefitsHandlerFixed:
    """
    Bug 9a+9b fixed: both handlers now import run_coro_in_threadpool locally
    (wizard_service_tools.py:2027 and :2127) and return error=True on failure.

    9b tests: call handlers with no DB → run_coro_in_threadpool raises →
    except → error=True. No mocks needed. No xfail.

    9a (happy-path) tests: mock at REPOSITORY level (not helper level) so
    run_coro_in_threadpool + _fetch() actually execute. Exercises:
      - run_coro_in_threadpool creates thread + event loop
      - _fetch() async function runs end-to-end
      - UUID conversion (Finding C) — uses _VALID_UUID
      - repo.list_active_for_company / repo.list_matching called with right args
    Patches (lazy imports inside _fetch() → patch at source module):
      app.shared.database.AsyncSessionLocal              (both handlers)
      app.domains.company.repositories.benefit_repository.BenefitRepository
      app.domains.company.repositories.compensation_component_repository.CompensationComponentRepository
      app.domains.job_creation.helpers.vaga_variable_comp.snapshot_from_catalog
    """

    # ── 9b: error=True on service failure (deterministic mock) ──────────────

    def test_benefits_handler_returns_error_true_on_service_failure(self):
        """
        Explicitly mock AsyncSessionLocal to raise so test is deterministic
        regardless of whether a DB is reachable in the test environment.
        After Bug 9c fix (app.core.database), _fetch() can actually connect and
        return [] if a DB is present — causing the handler to branch to 'no catalog'
        (error=False), which would make the naive 'no DB' test flap.
        Using an explicit failure mock locks in the error=True contract.
        """
        import app.core.database as _db_mod  # noqa: PLC0415
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_benefits,
        )

        def _raise_db_error():
            raise RuntimeError("Simulated DB failure for 9b deterministic test")

        with patch.object(_db_mod, "AsyncSessionLocal", _raise_db_error):
            result = _handle_suggest_benefits(_make_state(), {}, CTX)

        assert result.error is True, (
            "BUG 9b not fixed: _handle_suggest_benefits still returns error=False on failure. "
            "Expected error=True after wizard_service_tools.py:2036 fix."
        )

    def test_variable_comp_handler_returns_error_true_on_service_failure(self):
        """
        Same deterministic mock pattern for variable_comp handler.
        """
        import app.core.database as _db_mod  # noqa: PLC0415
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_variable_compensation,
        )

        def _raise_db_error():
            raise RuntimeError("Simulated DB failure for 9b deterministic test")

        with patch.object(_db_mod, "AsyncSessionLocal", _raise_db_error):
            result = _handle_suggest_variable_compensation(_make_state(), {}, CTX)

        assert result.error is True, (
            "BUG 9b not fixed: _handle_suggest_variable_compensation still returns error=False. "
            "Expected error=True after wizard_service_tools.py:2136 fix."
        )

    # ── 9a: happy path — exercises _fetch() via real run_coro_in_threadpool ──

    def test_benefits_happy_path_returns_actual_catalog(self):
        """
        Mocks AsyncSessionLocal + BenefitRepository at source module so _fetch()
        runs end-to-end (via real run_coro_in_threadpool) without hitting real DB.

        Uses patch.object (not string-path patch) to avoid pkgutil.resolve_name
        AttributeError when app.shared.database is not yet in sys.modules.
        Explicit module import inside method ensures sys.modules is populated first.

        See Finding C: state must have a UUID-format company_id so the UUID()
        conversion inside _fetch() succeeds and list_active_for_company is called.
        """
        # Lazy imports here ensure sys.modules is populated before patch.object runs
        import app.core.database as _db_mod  # noqa: PLC0415
        import app.domains.company.repositories.benefit_repository as _br_mod  # noqa: PLC0415
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_benefits,
        )

        fake_benefit = SimpleNamespace(
            name="Vale Refeição",
            category="alimentacao",
            icon=None,
            value="R$30/dia",
            value_type="daily",
            is_highlighted=True,
        )

        mock_repo_instance = MagicMock()
        mock_repo_instance.list_active_for_company = AsyncMock(return_value=[fake_benefit])
        mock_repo_class = MagicMock(return_value=mock_repo_instance)

        with patch.object(_db_mod, "AsyncSessionLocal", _fake_db_session), \
             patch.object(_br_mod, "BenefitRepository", mock_repo_class):
            result = _handle_suggest_benefits(_make_state(), {}, CTX)

        assert not result.error, (
            f"Happy path returned error=True unexpectedly: {result.llm_message}"
        )
        benefits = result.state_updates.get("benefits")
        assert benefits, (
            f"state_updates['benefits'] is empty or missing. "
            f"llm_message={result.llm_message!r}. "
            "If company_id UUID conversion failed, _fetch() returned [] — "
            "check _VALID_UUID in test. If DB mock not applied, run_coro raised."
        )
        assert benefits[0]["name"] == "Vale Refeição", (
            f"First benefit name mismatch: {benefits[0]}"
        )
        # Confirms _fetch() ran to completion (not short-circuited by NameError)
        mock_repo_instance.list_active_for_company.assert_called_once()

    def test_variable_comp_happy_path_returns_actual_catalog(self):
        """
        Mocks AsyncSessionLocal + CompensationComponentRepository at source module
        + snapshot_from_catalog (lazy import outside _fetch() in the handler body).
        run_coro_in_threadpool + _fetch() execute for real.

        Uses patch.object to avoid pkgutil.resolve_name sys.modules issue.
        """
        import app.core.database as _db_mod  # noqa: PLC0415
        import app.domains.company.repositories.compensation_component_repository as _cc_mod  # noqa: PLC0415
        import app.domains.job_creation.helpers.vaga_variable_comp as _vc_mod  # noqa: PLC0415
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_suggest_variable_compensation,
        )

        fake_comp = SimpleNamespace(name="PLR")
        fake_snap = MagicMock()
        fake_snap.model_dump.return_value = {"name": "PLR", "type": "plr", "amount": 5000}

        mock_repo_instance = MagicMock()
        mock_repo_instance.list_matching = AsyncMock(return_value=[(fake_comp, True)])
        mock_repo_class = MagicMock(return_value=mock_repo_instance)

        with patch.object(_db_mod, "AsyncSessionLocal", _fake_db_session), \
             patch.object(_cc_mod, "CompensationComponentRepository", mock_repo_class), \
             patch.object(_vc_mod, "snapshot_from_catalog", return_value=fake_snap):
            result = _handle_suggest_variable_compensation(_make_state(), {}, CTX)

        assert not result.error, (
            f"Happy path returned error=True unexpectedly: {result.llm_message}"
        )
        vc = result.state_updates.get("variable_compensation")
        assert vc, "state_updates['variable_compensation'] is empty or missing"
        assert vc[0]["name"] == "PLR", f"First comp name mismatch: {vc[0]}"
        assert vc[0]["matches_vaga"] is True, "matches_vaga flag missing"
        # Confirms _fetch() ran to completion
        mock_repo_instance.list_matching.assert_called_once()


# ── Bug 13: Calibração handlers ──────────────────────────────────────────────

class TestCalibrationHandlers:
    """
    _handle_calibration_action — fail-loud validation + signal semantics
    _handle_advance_calibration — sets calibration_complete=True

    Threshold decision (Paulo 2026-06-19):
      - like + dislike contam para signal_count; skip NÃO conta
      - can_advance = signal_count >= threshold
      - calibration_complete NUNCA setado por _handle_calibration_action
    """

    _CANDS = [
        {"id": "cand-1", "name": "Alice"},
        {"id": "cand-2", "name": "Bob"},
        {"id": "cand-3", "name": "Carol"},
    ]

    def _state(self, **extra):
        base = {
            "company_id": _VALID_UUID,
            "calibration_candidates": [dict(c) for c in self._CANDS],
            "calibration_threshold": 3,
        }
        base.update(extra)
        return base

    # ── Validation: fail-loud ────────────────────────────────────────────────

    def test_missing_candidate_id_returns_error(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_calibration_action,
        )
        result = _handle_calibration_action(self._state(), {"signal": "like"}, CTX)
        assert result.error is True, "candidate_id ausente deve retornar error=True"
        assert "obrigatório" in result.llm_message.lower()

    def test_invalid_signal_returns_error(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_calibration_action,
        )
        result = _handle_calibration_action(
            self._state(), {"candidate_id": "cand-1", "signal": "thumbsup"}, CTX
        )
        assert result.error is True, "signal inválido deve retornar error=True"
        assert "inválido" in result.llm_message.lower() or "invalid" in result.llm_message.lower()

    def test_candidate_not_found_returns_error(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_calibration_action,
        )
        result = _handle_calibration_action(
            self._state(), {"candidate_id": "cand-999", "signal": "like"}, CTX
        )
        assert result.error is True, "candidato não encontrado deve retornar error=True"
        assert "não encontrado" in result.llm_message or "not found" in result.llm_message.lower()

    # ── Signal semantics ─────────────────────────────────────────────────────

    def test_like_increments_signal_count(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_calibration_action,
        )
        result = _handle_calibration_action(
            self._state(), {"candidate_id": "cand-1", "signal": "like"}, CTX
        )
        assert not result.error
        cands = result.state_updates["calibration_candidates"]
        alice = next(c for c in cands if c["id"] == "cand-1")
        assert alice["decision"] == "approved"
        # 1 like → signal_count=1 < threshold=3 → can_advance=False
        assert result.state_updates["can_advance"] is False

    def test_dislike_increments_signal_count(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_calibration_action,
        )
        result = _handle_calibration_action(
            self._state(), {"candidate_id": "cand-2", "signal": "dislike"}, CTX
        )
        assert not result.error
        cands = result.state_updates["calibration_candidates"]
        bob = next(c for c in cands if c["id"] == "cand-2")
        assert bob["decision"] == "rejected"
        assert result.state_updates["can_advance"] is False

    def test_skip_does_not_count_toward_threshold(self):
        """Skip NÃO conta para signal_count — decisão Paulo 2026-06-19."""
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_calibration_action,
        )
        result = _handle_calibration_action(
            self._state(), {"candidate_id": "cand-3", "signal": "skip"}, CTX
        )
        assert not result.error
        cands = result.state_updates["calibration_candidates"]
        carol = next(c for c in cands if c["id"] == "cand-3")
        assert carol["decision"] == "skip"
        # skip → signal_count=0 → can_advance=False
        assert result.state_updates["can_advance"] is False

    def test_threshold_met_sets_can_advance_true_but_not_calibration_complete(self):
        """2 likes + 1 dislike = signal_count=3 = threshold → can_advance=True.
        calibration_complete NÃO deve aparecer em state_updates (nunca auto-eject).
        """
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_calibration_action,
        )
        state = self._state()
        # pre-populate 2 existing signals
        state["calibration_candidates"][0]["decision"] = "approved"  # cand-1 like
        state["calibration_candidates"][1]["decision"] = "rejected"  # cand-2 dislike
        # add 3rd signal (like for cand-3) → signal_count=3
        result = _handle_calibration_action(
            state, {"candidate_id": "cand-3", "signal": "like"}, CTX
        )
        assert not result.error
        assert result.state_updates["can_advance"] is True, (
            "signal_count=3 >= threshold=3 deve setar can_advance=True"
        )
        assert "calibration_complete" not in result.state_updates, (
            "_handle_calibration_action NUNCA seta calibration_complete "
            "(sem auto-eject — decisão Paulo 2026-06-19)"
        )

    def test_decision_is_idempotent_substitution(self):
        """Re-marcar um candidato substitui a decisão anterior (idempotente)."""
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_calibration_action,
        )
        state = self._state()
        # First mark: like
        r1 = _handle_calibration_action(
            state, {"candidate_id": "cand-1", "signal": "like"}, CTX
        )
        assert not r1.error
        cands_after_like = r1.state_updates["calibration_candidates"]
        # signal_count after like = 1
        sc1 = sum(1 for c in cands_after_like if c.get("decision") in ("approved", "rejected"))
        assert sc1 == 1

        # Second mark: dislike for same candidate
        state2 = dict(state)
        state2["calibration_candidates"] = cands_after_like
        r2 = _handle_calibration_action(
            state2, {"candidate_id": "cand-1", "signal": "dislike"}, CTX
        )
        assert not r2.error
        cands_after_dislike = r2.state_updates["calibration_candidates"]
        alice = next(c for c in cands_after_dislike if c["id"] == "cand-1")
        assert alice["decision"] == "rejected", "decisão deve ser substituída, não acumulada"
        # signal_count still = 1 (not 2)
        sc2 = sum(1 for c in cands_after_dislike if c.get("decision") in ("approved", "rejected"))
        assert sc2 == 1, f"signal_count deve ser 1 (substituição), não {sc2} (acumulação)"

    # ── advance_calibration ──────────────────────────────────────────────────

    def test_advance_calibration_sets_complete(self):
        """_handle_advance_calibration → calibration_complete=True."""
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_advance_calibration,
        )
        result = _handle_advance_calibration(self._state(), {}, CTX)
        assert not result.error
        assert result.state_updates.get("calibration_complete") is True, (
            "advance_calibration deve setar calibration_complete=True"
        )
