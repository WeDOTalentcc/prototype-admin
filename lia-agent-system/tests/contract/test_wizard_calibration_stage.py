"""
Contract tests — wizard calibration stage fix (2026-06-20).
T-a: calibration start → handle_calibration passes current_stage=calibration to graph.resume
T-b: first calibration turn works WITHOUT relying on previous ws_stage_payload (breaks circular fix)
T-c: fresh session does NOT derive calibration prematurely
T-d: non-regression — session legitimately in calibration renders correctly
"""
import pytest
from unittest.mock import MagicMock, patch


def _load_derive():
    """Load _derive_wizard_stage from wherever it lives."""
    import importlib
    for mod_path in [
        "app.domains.job_creation.services.wizard_session_service",
        "app.domains.job_creation.wizard_session_service",
    ]:
        try:
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, "_derive_wizard_stage", None)
            if fn:
                return fn
        except (ImportError, ModuleNotFoundError):
            continue
    raise ImportError("Cannot find _derive_wizard_stage")


MOCK_CANDIDATES = [
    {"id": "cand-1", "name": "Alice", "title": "Eng Senior", "score": 0.92, "decision": None},
    {"id": "cand-2", "name": "Bob", "title": "Arquiteto", "score": 0.87, "decision": None},
    {"id": "cand-3", "name": "Carol", "title": "Tech Lead", "score": 0.83, "decision": None},
]


def _fresh_state(job_id="test-job-123"):
    """Fresh wizard session as initialized by domain.py _start_wizard."""
    return {
        "job_id": job_id,
        "current_stage": "intake",
        "calibration_candidates": [],
        "calibration_threshold": 3,
        "calibration_complete": False,
        "calibration_approved_count": 0,
        "stage_history": ["intake"],
        "completeness": 0,
    }


def _calibration_active_state(candidates, job_id="test-job-123"):
    """State AFTER calibration begins — producer has set current_stage=calibration."""
    return {
        "job_id": job_id,
        "current_stage": "calibration",
        "calibration_candidates": candidates,
        "calibration_threshold": 3,
        "calibration_complete": False,
        "calibration_approved_count": 0,
        "stage_history": ["intake", "jd_enrichment", "wsi_questions", "calibration"],
        "completeness": 75,
        # NO ws_stage_payload — simulates first turn
    }


def test_tc_fresh_session_does_not_derive_calibration():
    """T-c: fresh session must NOT derive calibration (baseline guard)."""
    _derive = _load_derive()
    state = _fresh_state()
    result = _derive(state)
    cs = state.get("current_stage")
    cc = state.get("calibration_candidates")
    assert result != "calibration", (
        f"Fresh session derived calibration prematurely: got {result!r}. "
        f"current_stage={cs!r}, calibration_candidates={cc}"
    )


def test_tb_first_calibration_turn_no_ws_stage_payload():
    """T-b: first calibration turn — current_stage=calibration set by producer,
    NO ws_stage_payload yet. Must derive calibration.
    Breaks the circular fix that required ws_stage_payload.stage=calibration
    from a PREVIOUS turn that does not exist on first entry.
    Fix: _derive_wizard_stage reads current_stage directly (non-circular).
    """
    _derive = _load_derive()
    state = _calibration_active_state(MOCK_CANDIDATES)
    state.pop("ws_stage_payload", None)  # explicitly no prior payload

    result = _derive(state)
    cs = state.get("current_stage")

    assert result == "calibration", (
        f"First calibration turn failed to derive calibration: got {result!r}. "
        f"current_stage={cs!r}. "
        f"Bug B: _derive_wizard_stage must read current_stage, not ws_stage_payload."
    )


def test_td_non_regression_calibration_state():
    """T-d: non-regression — current_stage=calibration with candidates."""
    _derive = _load_derive()
    state = _calibration_active_state(MOCK_CANDIDATES)
    result = _derive(state)
    assert result == "calibration", (
        f"Non-regression FAILED: {len(MOCK_CANDIDATES)} candidates, "
        f"current_stage=calibration should derive calibration, got {result!r}"
    )


def test_ta_handle_calibration_sets_current_stage_calibration():
    """T-a: _handle_calibration (FastAPI producer) must set current_stage=calibration
    in the state passed to graph.resume(), so that _derive_wizard_stage has a
    non-circular signal on the first calibration turn.
    """
    import importlib
    domain_mod = None
    for mod_path in [
        "app.domains.job_creation.domain",
        "app.domains.job_creation.job_creation_domain",
    ]:
        try:
            domain_mod = importlib.import_module(mod_path)
            break
        except (ImportError, ModuleNotFoundError):
            continue

    if domain_mod is None:
        pytest.skip("Cannot import domain module")

    JobCreationDomain = getattr(domain_mod, "JobCreationDomain", None)
    if JobCreationDomain is None:
        pytest.skip("JobCreationDomain not found")

    # Mock graph.resume to capture what state was passed
    captured_state = {}
    mock_resume_result = {
        "job_id": "job-test-123",
        "current_stage": "calibration",
        "calibration_candidates": MOCK_CANDIDATES,
        "calibration_complete": False,
        "calibration_threshold": 3,
        "ws_stage_payload": {},
        "response": "Aqui estao os candidatos para calibracao.",
    }

    def _capture_resume(thread_id, state, updates=None):
        captured_state.update(state)
        return mock_resume_result

    mock_graph = MagicMock()
    mock_graph.resume.side_effect = _capture_resume

    # Build domain instance without full init
    domain = object.__new__(JobCreationDomain)
    domain._graph = mock_graph  # bypass property — set internal attr directly

    # Build minimal context (prior state is wsi_questions, transitioning to calibration)
    prior_state = {
        "job_id": "job-test-123",
        "current_stage": "wsi_questions",
        "calibration_candidates": [],
        "calibration_complete": False,
        "calibration_threshold": 3,
        "stage_history": ["intake", "jd_enrichment", "wsi_questions"],
        "completeness": 60,
    }

    context = MagicMock()
    context.metadata = {"wizard_state": prior_state}
    context.user_id = "recruiter-1"
    context.company_id = "company-test"
    context.session_id = "session-test"

    params = {"user_query": "vamos calibrar", "candidates": []}

    try:
        result = domain._handle_calibration(params, context, thread_id="thread-test")
    except Exception as e:
        pytest.fail(f"_handle_calibration raised: {e}")

    # After fix: state passed to graph.resume must have current_stage=calibration
    assert captured_state.get("current_stage") == "calibration", (
        f"Bug A/B prereq: _handle_calibration must set current_stage=calibration "
        "before calling graph.resume(). Got: " + repr(captured_state.get("current_stage")) + ". "
        f"Full captured state keys: {list(captured_state.keys())}"
    )
