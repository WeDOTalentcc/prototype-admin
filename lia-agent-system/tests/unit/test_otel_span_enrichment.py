"""UC-P1-07: OTEL span enrichment with LLM context attributes."""
from unittest.mock import MagicMock


def test_enrich_llm_span_sets_tenant_id():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(span, tenant_id="c123")
    span.set_attribute.assert_any_call("tenant.id", "c123")


def test_enrich_llm_span_sets_model():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(span, model="claude-3-5-sonnet")
    span.set_attribute.assert_any_call("llm.model", "claude-3-5-sonnet")


def test_enrich_llm_span_sets_tokens_used():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(span, tokens_used=500)
    span.set_attribute.assert_any_call("llm.tokens_used", 500)


def test_enrich_llm_span_sets_provider():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(span, provider="gemini")
    span.set_attribute.assert_any_call("llm.provider", "gemini")


def test_enrich_llm_span_sets_domain():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(span, domain="job_management")
    span.set_attribute.assert_any_call("llm.domain", "job_management")


def test_enrich_llm_span_sets_user_id():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(span, user_id="u456")
    span.set_attribute.assert_any_call("user.id", "u456")


def test_enrich_llm_span_ignores_none_tenant_id():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(span, tenant_id=None, model="gpt-4o")
    calls = [str(c) for c in span.set_attribute.call_args_list]
    assert not any("tenant.id" in c for c in calls), (
        "None values must NOT be written to span attributes"
    )


def test_enrich_llm_span_ignores_none_tokens():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(span, tokens_used=None, model="claude-3-5-sonnet")
    calls = [str(c) for c in span.set_attribute.call_args_list]
    assert not any("tokens_used" in c for c in calls)


def test_enrich_llm_span_never_raises_with_none_span():
    from app.shared.tracing import enrich_llm_span
    # Must not raise even when span is None
    enrich_llm_span(None, tenant_id="x", model="y", tokens_used=100)


def test_enrich_llm_span_never_raises_when_set_attribute_raises():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    span.set_attribute.side_effect = RuntimeError("span is closed")
    # Must not propagate the error
    enrich_llm_span(span, tenant_id="c123", model="gemini-pro")


def test_enrich_llm_span_all_attributes_at_once():
    from app.shared.tracing import enrich_llm_span
    span = MagicMock()
    enrich_llm_span(
        span,
        tenant_id="company_abc",
        user_id="user_xyz",
        model="claude-3-5-sonnet",
        tokens_used=1024,
        provider="claude",
        domain="recruitment",
    )
    assert span.set_attribute.call_count == 6


def test_llm_factory_imports_enrich_llm_span():
    """UC-P1-07: generate_with_fallback must import and use enrich_llm_span."""
    import pathlib
    source = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/shared/providers/llm_factory.py"
    ).read_text()
    assert "enrich_llm_span" in source, (
        "UC-P1-07: enrich_llm_span not found in llm_factory.py. "
        "Wire it into generate_with_fallback after successful LLM call."
    )
    assert "from app.shared.tracing import enrich_llm_span" in source, (
        "UC-P1-07: must import enrich_llm_span from app.shared.tracing"
    )
