"""Sprint O.3 sensor — calibration_node fresh-publish message UX.

Reason: Pre-Sprint-O.3, calibration_node ran auto-transition after publish_node
in the same graph turn and emitted "Carreguei 0 candidato(s) para calibração...
Continue avaliando para liberar a publicação completa." This message:
- sounded like the vacancy publish had failed
- gave no confirmation that publishing succeeded
- had no celebratory tone or next-step CTA

Sprint O.3 added a fresh-publish branch that detects the publish->calibration
boundary (stage_history tail contains "publish", job_id present, no error,
zero candidates loaded yet) and emits a celebratory message instead.

Guards (R-Sprint-O.3):
1. Fresh-publish state -> message contains success keywords ("publicada",
   "sucesso") and does NOT contain failure keywords ("0 candidato",
   "Continue avaliando").
2. Steady-state calibration (no recent publish, candidates loaded) -> message
   keeps the canonical progress format.
3. Complete-calibration state -> message keeps the "Calibração concluída" form.
"""
from __future__ import annotations

import pytest

from app.domains.job_creation.graph import calibration_node


def _base_state(**overrides):
    """Build a JobCreationState-shaped dict with sensible defaults for tests."""
    state = {
        "job_id": "job-uid-test-123",
        "calibration_candidates": [],
        "calibration_threshold": 3,
        "stage_history": [],
        "wsi_questions": [],
        "share_link": "",
        "error": None,
    }
    state.update(overrides)
    return state


@pytest.mark.unit
def test_fresh_publish_emits_celebratory_message():
    """publish_node just ran (stage_history tail), job_id present, 0 candidates
    -> message must say "publicada com sucesso", NOT "0 candidato"."""
    state = _base_state(
        stage_history=["intake", "jd_enrichment", "review", "publish"],
        wsi_questions=[{"id": "q1"}, {"id": "q2"}, {"id": "q3"}, {"id": "q4"},
                       {"id": "q5"}, {"id": "q6"}, {"id": "q7"}],
        share_link="https://app.example/jobs/abc",
    )
    result = calibration_node(state)
    msg = result["ws_stage_payload"]["data"]["message"]

    # Success keywords
    assert "publicada" in msg.lower(), f"missing 'publicada' in: {msg!r}"
    assert "sucesso" in msg.lower(), f"missing 'sucesso' in: {msg!r}"

    # Forbidden failure keywords
    assert "0 candidato" not in msg, f"misleading '0 candidato' in: {msg!r}"
    assert "Continue avaliando" not in msg, (
        f"misleading 'Continue avaliando' in: {msg!r}"
    )

    # WSI count surfaced
    assert "7" in msg, f"WSI count (7) missing in: {msg!r}"
    # Share link surfaced
    assert "https://app.example/jobs/abc" in msg, f"share_link missing in: {msg!r}"
    # State flag set for downstream UI consumers
    assert result["ws_stage_payload"]["data"]["fresh_publish"] is True


@pytest.mark.unit
def test_fresh_publish_without_wsi_questions_still_celebrates():
    """If wsi_questions empty, fallback message still celebratory."""
    state = _base_state(
        stage_history=["intake", "review", "publish"],
        wsi_questions=[],
    )
    result = calibration_node(state)
    msg = result["ws_stage_payload"]["data"]["message"]
    assert "publicada" in msg.lower()
    assert "sucesso" in msg.lower()
    assert "0 candidato" not in msg


@pytest.mark.unit
def test_steady_state_calibration_keeps_canonical_progress_message():
    """Later turns (no recent 'publish' in tail, candidates loaded) -> use the
    canonical 'Carreguei N candidato(s)' progress message."""
    state = _base_state(
        stage_history=["calibration", "calibration"],  # publish NOT in last 3
        calibration_candidates=[
            {"id": "c1", "decision": "approved"},
            {"id": "c2", "decision": "pending"},
        ],
    )
    result = calibration_node(state)
    msg = result["ws_stage_payload"]["data"]["message"]
    assert "Carreguei 2 candidato" in msg, f"canonical progress msg missing: {msg!r}"
    assert "1/3 aprovados" in msg, f"approval ratio missing: {msg!r}"
    assert result["ws_stage_payload"]["data"]["fresh_publish"] is False


@pytest.mark.unit
def test_complete_calibration_emits_completion_message():
    """When approved_count >= threshold -> 'Calibração concluída' message."""
    state = _base_state(
        stage_history=["calibration"],
        calibration_candidates=[
            {"id": "c1", "decision": "approved"},
            {"id": "c2", "decision": "approved"},
            {"id": "c3", "decision": "approved"},
        ],
        calibration_threshold=3,
    )
    result = calibration_node(state)
    msg = result["ws_stage_payload"]["data"]["message"]
    assert "Calibração concluída" in msg or "concluida" in msg.lower()
    assert "3/3" in msg
    assert result["calibration_complete"] is True


@pytest.mark.unit
def test_fresh_publish_with_error_does_not_celebrate():
    """If publish step recorded an error, do NOT emit celebratory message
    even if stage_history tail contains 'publish'."""
    state = _base_state(
        stage_history=["review", "publish"],
        error="rails api 503",
    )
    result = calibration_node(state)
    msg = result["ws_stage_payload"]["data"]["message"]
    # Should fall back to canonical 0-candidate progress msg, not celebrate
    assert "publicada com sucesso" not in msg.lower()
    assert result["ws_stage_payload"]["data"]["fresh_publish"] is False


# ---------------------------------------------------------------------------
# C1: PIN calibration_threshold production default == 5
# ---------------------------------------------------------------------------

def test_calibration_threshold_default_is_5():
    """Sensor: _handle_advance_calibration must use default threshold == 5.

    The test fixture uses threshold=3 (via state fixture) so tests can pass
    with 3 decisions. But the production default must stay at 5.
    Changing `state.get("calibration_threshold", X)` where X != 5 breaks
    the harness intent and requires a conscious 3-party change:
      1. This test (C1 sensor)
      2. Both occurrences in _handle_advance_calibration source
      3. Production docs / CLAUDE.md calibration_threshold note

    If you legitimately need a different default, update all 3 together.
    """
    import ast
    import pathlib

    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/domains/job_creation/orchestrator/wizard_service_tools.py"
    ).read_text()
    tree = ast.parse(src)

    defaults_found = []
    for node in ast.walk(tree):
        # Find: state.get("calibration_threshold", <default>)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and len(node.args) == 2
        ):
            if (
                isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "calibration_threshold"
            ):
                default_node = node.args[1]
                if isinstance(default_node, ast.Constant):
                    defaults_found.append(default_node.value)

    assert defaults_found, (
        "No state.get('calibration_threshold', ...) call found in wizard_service_tools.py "
        "— the sensor anchor is broken, likely the handler was refactored."
    )
    non_five = [d for d in defaults_found if d != 5]
    assert not non_five, (
        f"calibration_threshold default(s) changed from 5 to {non_five}. "
        "Update this test + docs if the change is intentional."
    )
    assert len(defaults_found) >= 2, (
        f"Expected >=2 occurrences of state.get('calibration_threshold', 5), "
        f"found {len(defaults_found)}. Handler may have been refactored."
    )
