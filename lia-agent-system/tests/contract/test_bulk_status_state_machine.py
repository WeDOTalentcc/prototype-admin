"""
TDD sensor for N8: status transition state machine in bulk_update_candidate_status.
Computacional sensor (deterministic) per harness-engineering taxonomy.
"""
import pytest


def test_state_machine_import():
    """Smoke: STATUS_TRANSITIONS and _check_status_transition must be importable."""
    from app.api.v1.bulk_actions import STATUS_TRANSITIONS, _check_status_transition
    assert isinstance(STATUS_TRANSITIONS, dict)
    assert callable(_check_status_transition)


def test_hired_can_only_go_to_rejected():
    """hired -> anything except rejected must be blocked."""
    from app.api.v1.bulk_actions import _check_status_transition
    assert _check_status_transition("hired", "rejected") is None
    for bad in ("new", "screening", "interview", "offer"):
        err = _check_status_transition("hired", bad)
        assert err is not None, f"hired->{bad} should be blocked"
        assert "hired" in err and bad in err


def test_rejected_can_go_to_reconsideration():
    """rejected -> new and rejected -> screening allowed (reconsideration)."""
    from app.api.v1.bulk_actions import _check_status_transition
    assert _check_status_transition("rejected", "new") is None
    assert _check_status_transition("rejected", "screening") is None


def test_rejected_cannot_go_directly_to_hired():
    """rejected -> hired is not a valid reconsideration step."""
    from app.api.v1.bulk_actions import _check_status_transition
    err = _check_status_transition("rejected", "hired")
    assert err is not None


def test_forward_flow_is_allowed():
    """Standard recruiting forward flow must all be allowed."""
    from app.api.v1.bulk_actions import _check_status_transition
    flow = [("new", "screening"), ("screening", "interview"), ("interview", "offer"), ("offer", "hired")]
    for from_s, to_s in flow:
        assert _check_status_transition(from_s, to_s) is None, f"{from_s}->{to_s} should be allowed"


def test_unknown_current_status_fails_open():
    """None or empty current_status is fail-open (legacy data)."""
    from app.api.v1.bulk_actions import _check_status_transition
    assert _check_status_transition(None, "hired") is None
    assert _check_status_transition("", "screening") is None


def test_error_message_is_llm_friendly():
    """Error message must include current, target, and allowed statuses for LLM consumption."""
    from app.api.v1.bulk_actions import _check_status_transition
    err = _check_status_transition("hired", "new")
    assert err is not None
    assert "hired" in err
    assert "new" in err
    assert "rejected" in err  # the allowed option must be mentioned
    assert "Para corrigir" in err  # must include fix instruction
