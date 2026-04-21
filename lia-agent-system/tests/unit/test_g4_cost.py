"""Onda 3.1 G4 — Cost tracker tests."""
from __future__ import annotations


def test_estimate_cost_known_models() -> None:
    """G4: cost computed from pricing table."""
    from app.shared.observability.cost_tracker import estimate_cost_usd

    # Haiku: $1/1M in, $5/1M out
    cost = estimate_cost_usd("claude-haiku-4-5", 1_000_000, 1_000_000)
    assert cost == 6.0, f"expected $6.00 per 1M+1M tokens on Haiku, got {cost}"

    # Sonnet: $3/1M in, $15/1M out
    cost_sonnet = estimate_cost_usd("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert cost_sonnet == 18.0


def test_estimate_cost_unknown_model_uses_fallback() -> None:
    """G4: unknown model doesn't crash — falls back to haiku pricing."""
    from app.shared.observability.cost_tracker import estimate_cost_usd

    cost = estimate_cost_usd("claude-experimental-xyz", 1000, 1000)
    # Fallback haiku: $1/$5 → (0.001 + 0.005) = $0.006
    assert cost > 0 and cost < 0.01


def test_record_call_accumulates_per_tenant() -> None:
    """G4: record_call sums into tenant accumulator."""
    from app.shared.observability.cost_tracker import record_call, get_tenant_cost, reset_tenant_cost

    reset_tenant_cost("tenant-A")

    record_call(tenant_id="tenant-A", model="claude-haiku-4-5", input_tokens=500, output_tokens=200)
    record_call(tenant_id="tenant-A", model="claude-haiku-4-5", input_tokens=300, output_tokens=100)

    acc = get_tenant_cost("tenant-A")
    assert acc is not None
    assert acc.input_tokens == 800
    assert acc.output_tokens == 300
    assert acc.call_count == 2
    assert acc.total_usd > 0


def test_record_call_multiple_models_tracked() -> None:
    """G4: by_model counter tracks mix."""
    from app.shared.observability.cost_tracker import record_call, get_tenant_cost, reset_tenant_cost

    reset_tenant_cost("tenant-B")
    record_call(tenant_id="tenant-B", model="claude-haiku-4-5", input_tokens=100, output_tokens=50)
    record_call(tenant_id="tenant-B", model="claude-sonnet-4-6", input_tokens=100, output_tokens=50)
    record_call(tenant_id="tenant-B", model="claude-haiku-4-5", input_tokens=100, output_tokens=50)

    acc = get_tenant_cost("tenant-B")
    assert acc.by_model["claude-haiku-4-5"] == 2
    assert acc.by_model["claude-sonnet-4-6"] == 1


def test_record_call_unknown_tenant_stored_as_unknown() -> None:
    """G4: None tenant_id → 'unknown' bucket (not dropped)."""
    from app.shared.observability.cost_tracker import record_call, get_tenant_cost, reset_tenant_cost

    reset_tenant_cost("unknown")
    record_call(tenant_id=None, model="claude-haiku-4-5", input_tokens=100, output_tokens=50)
    acc = get_tenant_cost("unknown")
    assert acc is not None
    assert acc.call_count == 1


def test_feature_flag_off_disables_recording() -> None:
    """G4: LIA_COST_TRACKING_ENABLED=false → no-op."""
    import app.shared.observability.cost_tracker as mod

    original = mod._COST_TRACKING_ENABLED
    try:
        mod._COST_TRACKING_ENABLED = False
        mod.reset_tenant_cost("tenant-C")
        result = mod.record_call(
            tenant_id="tenant-C", model="claude-haiku-4-5",
            input_tokens=100, output_tokens=50,
        )
        assert result == {}, "G4: record_call should be no-op when disabled"
        assert mod.get_tenant_cost("tenant-C") is None
    finally:
        mod._COST_TRACKING_ENABLED = original


def test_reset_tenant_cost_specific() -> None:
    """G4: reset_tenant_cost(X) removes only X, not other tenants."""
    from app.shared.observability.cost_tracker import (
        record_call, get_tenant_cost, reset_tenant_cost,
    )

    record_call(tenant_id="tenant-X", model="claude-haiku-4-5", input_tokens=10, output_tokens=5)
    record_call(tenant_id="tenant-Y", model="claude-haiku-4-5", input_tokens=10, output_tokens=5)

    reset_tenant_cost("tenant-X")
    assert get_tenant_cost("tenant-X") is None
    assert get_tenant_cost("tenant-Y") is not None


def test_marker_catalog_has_lia_cost() -> None:
    """G4: LIA-COST must be documented in marker_catalog.yaml."""
    from pathlib import Path

    import yaml

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "app/shared/observability/marker_catalog.yaml"
        if cand.exists():
            break
    else:
        raise RuntimeError("marker_catalog.yaml not found")

    data = yaml.safe_load(cand.read_text(encoding="utf-8"))
    assert "LIA-COST" in data["markers"], (
        "G4: LIA-COST entry must be added to marker_catalog.yaml "
        "(drift guard test_g2_marker_catalog also enforces this)"
    )
    entry = data["markers"]["LIA-COST"]
    assert entry["category"] == "cost"


def test_claude_provider_generate_accepts_prompt_cache_flag() -> None:
    """G4: ClaudeLLMProvider.generate must accept use_prompt_cache kwarg."""
    import inspect

    from app.shared.providers.llm_claude import ClaudeLLMProvider

    sig = inspect.signature(ClaudeLLMProvider.generate)
    assert "use_prompt_cache" in sig.parameters, (
        "G4: generate() must accept use_prompt_cache kwarg for Anthropic prompt cache"
    )


def test_g4_marker_in_cost_tracker() -> None:
    """G4 audit marker for traceability."""
    from pathlib import Path

    import app.shared.observability.cost_tracker as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "G4" in source, "G4: cost_tracker.py must contain G4 marker"
    assert "record_call" in source and "estimate_cost_usd" in source
