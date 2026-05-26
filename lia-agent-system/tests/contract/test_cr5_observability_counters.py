"""Sprint 2.2 CR-5 sensor (2026-05-26) — main_orchestrator_guard_fires_total
counter declarado em canary_metrics + wired em todos os 5 guard sites do
main_orchestrator.process(). Sensor estatico via source-grep (sem rodar
runtime do orchestrator)."""
from pathlib import Path


CANARY = Path("app/shared/observability/canary_metrics.py")
ORCH = Path("app/orchestrator/execution/main_orchestrator.py")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_counter_declared_in_canary_metrics():
    """main_orchestrator_guard_fires_total deve estar declarado no
    canary_metrics canonical module."""
    src = _read(CANARY)
    assert "main_orchestrator_guard_fires_total = _make_counter(" in src, (
        "main_orchestrator_guard_fires_total counter missing from canary_metrics.py. "
        "Sprint 2.2 CR-5 requires this canonical counter declared via _make_counter "
        "helper (fail-open, reuse-existing pattern)."
    )
    # Labels must include guard + outcome
    assert '("guard", "outcome")' in src or "'guard', 'outcome'" in src, (
        "Counter labels must be ('guard', 'outcome'). Required by CR-5 spec."
    )


def test_counter_wired_at_security_patterns_block():
    """SecurityPatterns block path must increment counter."""
    src = _read(ORCH)
    # Find the SecurityPatterns block site
    assert 'SecurityPatterns blocked input' in src, "SecurityPatterns site missing"
    # The increment block must be near (search within next 800 chars after the marker)
    idx = src.find('SecurityPatterns blocked input')
    window = src[idx:idx + 1200]
    assert 'guard="security_patterns_input"' in window or "guard='security_patterns_input'" in window, (
        "main_orchestrator_guard_fires_total not incremented at SecurityPatterns block site. "
        "CR-5 Sprint 2.2 requires this for observability."
    )


def test_counter_wired_at_fairness_input_block():
    """FairnessGuard input hard-block must increment counter."""
    src = _read(ORCH)
    idx = src.find('FairnessGuard blocked input')
    assert idx >= 0, "FairnessGuard input block site missing"
    window = src[idx:idx + 1200]
    assert 'guard="fairness_input"' in window or "guard='fairness_input'" in window


def test_counter_wired_at_fairness_implicit_soft_warn():
    """FairnessGuard implicit bias soft warning must increment counter."""
    src = _read(ORCH)
    idx = src.find('FairnessGuard soft warnings')
    assert idx >= 0, "FairnessGuard implicit site missing"
    window = src[idx:idx + 1200]
    assert 'guard="fairness_implicit"' in window or "guard='fairness_implicit'" in window


def test_counter_wired_at_ai_credit_exhausted():
    """AICreditGate exhausted must increment unified counter (complementa
    ai_credit_exhausted_total existente)."""
    src = _read(ORCH)
    idx = src.find('AI credit budget exhausted')
    assert idx >= 0, "AICreditGate site missing"
    window = src[idx:idx + 1200]
    assert 'guard="ai_credit_gate"' in window or "guard='ai_credit_gate'" in window


def test_counter_wired_at_policy_gate_violation():
    """PolicyGate soft enforcement violation must increment counter."""
    src = _read(ORCH)
    idx = src.find('P1-W4-11 soft-enforcement')
    assert idx >= 0, "PolicyGate site missing"
    window = src[idx:idx + 1500]
    assert 'guard="policy_gate"' in window or "guard='policy_gate'" in window


def test_all_increments_use_fail_open_try_except():
    """Cada increment do counter deve estar dentro de try/except fail-open
    pra nao quebrar o orchestrator se prometheus_client ausente ou hot-
    reload race condition."""
    src = _read(ORCH)
    # Count occurrences of the canonical pattern
    import re
    increment_blocks = re.findall(
        r"main_orchestrator_guard_fires_total\.labels\([^)]*\)\.inc\(\)",
        src,
    )
    assert len(increment_blocks) >= 5, (
        f"Expected >=5 increment sites (5 guards), got {len(increment_blocks)}"
    )
    # Each increment must be preceded by 'try:' within ~500 chars
    for inc in increment_blocks:
        idx = src.find(inc)
        prefix = src[max(0, idx - 500):idx]
        assert "try:" in prefix, (
            f"Increment {inc!r} not wrapped in try/except — must be fail-open per CR-5 spec."
        )
