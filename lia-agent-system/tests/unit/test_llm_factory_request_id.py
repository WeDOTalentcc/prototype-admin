"""Tests for request_id propagation (UC-P2-28)."""
import inspect


def test_generate_with_fallback_accepts_request_id():
    from app.shared.providers.llm_factory import ProviderContainer
    sig = inspect.signature(ProviderContainer.generate_with_fallback)
    assert "request_id" in sig.parameters, "generate_with_fallback must have request_id param"


def test_enrich_llm_span_accepts_request_id():
    from app.shared.tracing import enrich_llm_span
    sig = inspect.signature(enrich_llm_span)
    assert "request_id" in sig.parameters, "enrich_llm_span must have request_id param"
