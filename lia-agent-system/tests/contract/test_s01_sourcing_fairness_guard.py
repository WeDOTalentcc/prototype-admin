"""
S01 -- Sourcing FairnessGuard fail-soft elimination (P-GUARD).

T-a: guard raises unexpected exception -> logger.error emitted, NOT silent debug.
T-b: returns (False, None) when guard raises (not verified, not blocked).
T-c: circuit-breaker opens after CIRCUIT_OPEN_THRESHOLD consecutive failures.
T-d: non-regression -- guard succeeds, query clean -> (False, None).
T-e: non-regression -- guard succeeds, query blocked -> (True, message).
T-f: fail_closed=True raises FairnessGuardUnavailableError when guard fails.
T-g: circuit-open state -> immediately returns (False, None) without calling guard.
T-h: circuit-open -> logger.error emitted.
T-i: after success, consecutive_failures resets to 0.
T-j: sourcing tool registries do NOT have bare except swallowing FairnessGuard silently.
"""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch

from app.domains.sourcing.fairness.fairness_guard_wrapper import (
    run_sourcing_fairness_check,
    FairnessGuardUnavailableError,
    get_failure_stats,
    reset_for_testing,
    CIRCUIT_OPEN_THRESHOLD,
)


@pytest.fixture(autouse=True)
def reset_circuit():
    reset_for_testing()
    yield
    reset_for_testing()


# --- Mock FairnessCheckResult ---
def _blocked_result(msg="Discriminatory query blocked."):
    r = MagicMock()
    r.is_blocked = True
    r.educational_message = msg
    return r

def _clean_result():
    r = MagicMock()
    r.is_blocked = False
    r.educational_message = None
    return r


def test_ta_guard_exception_logs_error_not_debug():
    """Guard raises -> logger.error emitted (not debug/swallowed)."""
    failing_guard = MagicMock(side_effect=RuntimeError("service unavailable"))

    with patch("app.domains.sourcing.fairness.fairness_guard_wrapper.logger") as mock_log:
        is_blocked, msg = run_sourcing_fairness_check(
            failing_guard, "arg1", registry_name="test_registry"
        )

    mock_log.error.assert_called()
    error_call_str = str(mock_log.error.call_args_list)
    # Must mention the registry name in one of the error calls
    assert "test_registry" in error_call_str or "FairnessGuard" in error_call_str


def test_tb_returns_not_blocked_when_guard_raises():
    """Guard raises -> returns (False, None) -- caller knows guard was not run."""
    failing_guard = MagicMock(side_effect=ConnectionError("guard service down"))
    is_blocked, msg = run_sourcing_fairness_check(failing_guard, registry_name="github")
    assert is_blocked is False
    assert msg is None


def test_tc_circuit_opens_after_n_failures():
    """After CIRCUIT_OPEN_THRESHOLD consecutive failures, circuit opens."""
    failing_guard = MagicMock(side_effect=RuntimeError("boom"))

    for _ in range(CIRCUIT_OPEN_THRESHOLD):
        run_sourcing_fairness_check(failing_guard, registry_name="test")

    stats = get_failure_stats()
    assert stats["circuit_open"] is True, (
        f"Circuit must be open after {CIRCUIT_OPEN_THRESHOLD} consecutive failures. "
        f"Stats: {stats}"
    )


def test_td_non_regression_guard_succeeds_clean():
    """Guard succeeds, query clean -> (False, None)."""
    good_guard = MagicMock(return_value=_clean_result())
    is_blocked, msg = run_sourcing_fairness_check(good_guard, "python developer", registry_name="so")
    assert is_blocked is False
    assert msg is None


def test_te_non_regression_guard_blocks():
    """Guard succeeds, query blocked -> (True, educational_message)."""
    good_guard = MagicMock(return_value=_blocked_result("Por favor use criterios objetivos."))
    is_blocked, msg = run_sourcing_fairness_check(good_guard, "boa aparencia", registry_name="diversity")
    assert is_blocked is True
    assert msg == "Por favor use criterios objetivos."


def test_tf_fail_closed_raises_on_guard_failure():
    """fail_closed=True -> FairnessGuardUnavailableError when guard fails."""
    failing_guard = MagicMock(side_effect=RuntimeError("guard down"))
    with pytest.raises(FairnessGuardUnavailableError):
        run_sourcing_fairness_check(failing_guard, fail_closed=True, registry_name="pipeline")


def test_tg_circuit_open_skips_guard_immediately():
    """Circuit open -> guard not called, returns (False, None)."""
    failing = MagicMock(side_effect=RuntimeError("x"))
    for _ in range(CIRCUIT_OPEN_THRESHOLD):
        run_sourcing_fairness_check(failing, registry_name="test")

    new_guard = MagicMock(return_value=_clean_result())
    is_blocked, msg = run_sourcing_fairness_check(new_guard, registry_name="test2")

    new_guard.assert_not_called()
    assert is_blocked is False


def test_th_circuit_open_logs_error():
    """Circuit open -> logger.error emitted (not silent)."""
    failing = MagicMock(side_effect=RuntimeError("x"))
    for _ in range(CIRCUIT_OPEN_THRESHOLD):
        run_sourcing_fairness_check(failing, registry_name="test")

    new_guard = MagicMock(return_value=_clean_result())
    with patch("app.domains.sourcing.fairness.fairness_guard_wrapper.logger") as mock_log:
        run_sourcing_fairness_check(new_guard, registry_name="test2")

    mock_log.error.assert_called()


def test_ti_success_resets_failure_counter():
    """After guard succeeds, consecutive_failures resets to 0."""
    failing = MagicMock(side_effect=RuntimeError("x"))
    # Fail a few times (but not enough to open circuit)
    for _ in range(CIRCUIT_OPEN_THRESHOLD - 1):
        run_sourcing_fairness_check(failing, registry_name="test")

    stats_before = get_failure_stats()
    assert stats_before["consecutive_failures"] == CIRCUIT_OPEN_THRESHOLD - 1

    # Now succeed
    good_guard = MagicMock(return_value=_clean_result())
    run_sourcing_fairness_check(good_guard, registry_name="test")

    stats_after = get_failure_stats()
    assert stats_after["consecutive_failures"] == 0
    assert stats_after["circuit_open"] is False


def test_tj_tool_registries_no_bare_debug_swallow():
    """
    All simple tool registries must NOT have bare except that swallows
    FairnessGuard with only logger.debug (no logger.error).
    After S01 migration, all should use run_sourcing_fairness_check.
    """
    import ast
    from pathlib import Path

    SOURCING_AGENTS = Path(
        "/home/runner/workspace/lia-agent-system/app/domains/sourcing/agents"
    )
    REGISTRIES = [
        "github_tool_registry.py",
        "stackoverflow_tool_registry.py",
        "diversity_tool_registry.py",
        "passive_pipeline_tool_registry.py",
        "referral_tool_registry.py",
        "nurture_sequence_tool_registry.py",
    ]

    violations = []
    for reg_name in REGISTRIES:
        fpath = SOURCING_AGENTS / reg_name
        if not fpath.exists():
            continue
        src = fpath.read_text()
        tree = ast.parse(src)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            body_nodes = list(ast.walk(node))
            calls = [n for n in body_nodes if isinstance(n, ast.Call)]
            call_attrs = [
                c.func.attr
                for c in calls
                if isinstance(c.func, ast.Attribute) and hasattr(c.func, "attr")
            ]
            # debug-only (no error) in this except handler
            debug_only = "debug" in call_attrs and "error" not in call_attrs
            # mentions fairness in a string literal
            strings = [
                n.value
                for n in ast.walk(node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            ]
            fairness_mention = any(
                "fairness" in s.lower() or "FairnessGuard" in s
                for s in strings
            )
            if debug_only and fairness_mention:
                violations.append(f"{reg_name}:{node.lineno}")

    assert not violations, (
        f"These files still have silent FairnessGuard swallow (logger.debug only): "
        f"{violations}. Migrate to run_sourcing_fairness_check()."
    )
