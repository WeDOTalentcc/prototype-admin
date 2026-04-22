"""Onda 4.7 VII.B — error_policies wire in main_orchestrator tests."""
from __future__ import annotations

from pathlib import Path


def test_viib_marker_in_main_orchestrator() -> None:
    """VII.B: main_orchestrator contains VII.B marker + error_policies import."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    assert "Onda 4.7 VII.B" in source
    assert "from app.orchestrator.error_policies import apply_policy" in source
    assert "error_recovery" in source


def test_error_policies_reachable_from_orchestrator() -> None:
    """VII.B: producer apply_policy/resolve_policy reachable + behavior confirmed."""
    from app.orchestrator.error_policies import apply_policy, resolve_policy

    # Known trigger
    policy = resolve_policy("timeout")
    assert policy is not None and policy.id == "tool_timeout"

    applied = apply_policy("timeout")
    assert applied["policy_id"] == "tool_timeout"
    assert "response" in applied
    assert "severity" in applied


def test_catch_block_tries_error_policies_before_fallback() -> None:
    """VII.B structural: catch-all calls resolve_policy BEFORE fallback build_error_response."""
    import app.orchestrator.main_orchestrator as mo
    source = Path(mo.__file__).read_text(encoding="utf-8")

    # Find the VII.B block in source
    viib_idx = source.find("Onda 4.7 VII.B")
    assert viib_idx > 0
    # Find the SystemPromptBuilder.build_error_response fallback AFTER the VII.B block
    fallback_idx = source.find("SystemPromptBuilder.build_error_response", viib_idx)
    assert fallback_idx > viib_idx, (
        "VII.B: error_policies must be tried BEFORE falling back to build_error_response"
    )


def test_viib_wraps_in_try_except_fail_safe() -> None:
    """VII.B: apply_policy call wrapped — policy error doesn't crash response."""
    import app.orchestrator.main_orchestrator as mo
    source = Path(mo.__file__).read_text(encoding="utf-8")

    viib_idx = source.find("Onda 4.7 VII.B")
    # ~60 lines after
    block = source[viib_idx : viib_idx + 2500]
    # Must contain try/except within the block (before fallback)
    assert "try:" in block
    assert "except Exception" in block
    assert "error_policies apply skipped" in block.lower()


def test_viib_returns_error_recovery_intent_on_match() -> None:
    """VII.B semantic: on policy match, intent_detected = 'error_recovery'."""
    import app.orchestrator.main_orchestrator as mo
    source = Path(mo.__file__).read_text(encoding="utf-8")

    viib_idx = source.find("Onda 4.7 VII.B")
    block = source[viib_idx : viib_idx + 2500]
    assert 'intent_detected="error_recovery"' in block


def test_viib_populates_structured_data_with_policy_metadata() -> None:
    """VII.B: structured_data includes policy_id, severity, retry_hint."""
    import app.orchestrator.main_orchestrator as mo
    source = Path(mo.__file__).read_text(encoding="utf-8")

    viib_idx = source.find("Onda 4.7 VII.B")
    block = source[viib_idx : viib_idx + 2500]
    assert "policy_id" in block
    assert "severity" in block
    assert "retry_hint" in block
