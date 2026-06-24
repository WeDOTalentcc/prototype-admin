"""Tests for GAP-12-004: OTEL distributed tracing bootstrap.

Verifies:
- tracing module initializes without OTLP endpoint (LightweightTracer)
- _try_init_otlp returns False when no endpoint set
- trace_span decorator works (async)
- trace_span_sync decorator works (sync)
- get_tracer returns LightweightTracer
- SSE chat span creation code exists
- main.py lifespan has OTEL bootstrap
- FastAPIInstrumentor is conditionally wired
"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestTracingModuleBasics:
    """Core tracing module works without OTLP endpoint."""

    def test_get_tracer_returns_lightweight(self):
        from app.shared.observability.tracing import get_tracer, LightweightTracer
        tracer = get_tracer()
        assert isinstance(tracer, LightweightTracer)

    def test_traces_enabled_flag(self):
        from app.shared.observability.tracing import _TRACES_ENABLED
        assert isinstance(_TRACES_ENABLED, bool)

    def test_is_otlp_active_returns_bool(self):
        from app.shared.observability.tracing import is_otlp_active
        assert isinstance(is_otlp_active(), bool)

    def test_try_init_otlp_no_endpoint_returns_false(self):
        from app.shared.observability.tracing import _try_init_otlp
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": ""}):
            result = _try_init_otlp()
            assert result is False

    def test_try_init_otlp_with_endpoint_returns_true(self):
        from app.shared.observability.tracing import _try_init_otlp
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318"}):
            result = _try_init_otlp()
            assert result is True


class TestTraceSpanDecorators:
    """trace_span and trace_span_sync work correctly."""

    @pytest.mark.asyncio
    async def test_trace_span_async(self):
        from app.shared.observability.tracing import trace_span

        @trace_span("test.async_op")
        async def my_async_fn():
            return 42

        result = await my_async_fn()
        assert result == 42

    def test_trace_span_sync(self):
        from app.shared.observability.tracing import trace_span_sync

        @trace_span_sync("test.sync_op")
        def my_sync_fn():
            return "hello"

        result = my_sync_fn()
        assert result == "hello"


class TestSpanCreation:
    """LightweightTracer creates and finishes spans."""

    def test_create_span(self):
        from app.shared.observability.tracing import get_tracer
        tracer = get_tracer()
        span = tracer.create_span("test.span", attributes={"key": "val"})
        assert span.name == "test.span"
        assert span.attributes["key"] == "val"
        assert span.end_time is None
        span.end()
        assert span.end_time is not None

    def test_finish_span(self):
        from app.shared.observability.tracing import get_tracer, finish_span
        tracer = get_tracer()
        span = tracer.create_span("test.finish")
        finish_span(span, status="ok")
        assert span.end_time is not None
        assert span.status == "ok"

    def test_finish_span_with_error(self):
        from app.shared.observability.tracing import get_tracer, finish_span
        tracer = get_tracer()
        span = tracer.create_span("test.error")
        finish_span(span, status="error", error=ValueError("test"))
        assert span.status == "error"
        assert "ValueError" in span.attributes.get("error.type", "")


class TestOTELCodePresence:
    """Verify OTEL code is wired in the right places."""

    def test_main_py_has_otel_bootstrap(self):
        with open("app/main.py") as f:
            content = f.read()
        assert "GAP-12-004" in content
        assert "_try_init_otlp" in content
        assert "FastAPIInstrumentor" in content

    def test_sse_has_chat_span(self):
        with open("app/api/v1/agent_chat_sse.py") as f:
            content = f.read()
        assert "sse_chat.process" in content
        assert "finish_span" in content
        assert "_chat_span" in content

    def test_requirements_has_fastapi_instrumentation(self):
        with open("requirements.txt") as f:
            content = f.read()
        assert "opentelemetry-instrumentation-fastapi" in content

    def test_env_has_otel_vars(self):
        with open(".env") as f:
            content = f.read()
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" in content
        assert "OTEL_SERVICE_NAME" in content
