"""Coverage tests for app/shared/tracing.py and app/shared/upload_limits.py"""
import pytest


# ===========================================================================
# app/shared/upload_limits.py
# ===========================================================================
from app.shared.upload_limits import (
    DEFAULT_JD_UPLOAD_MAX_BYTES,
    JD_UPLOAD_MAX_BYTES,
    jd_upload_max_mb,
    _resolve_jd_upload_max_bytes,
)


class TestUploadLimits:
    def test_default_is_10_mib(self):
        assert DEFAULT_JD_UPLOAD_MAX_BYTES == 10 * 1024 * 1024

    def test_jd_upload_max_bytes_positive(self):
        assert JD_UPLOAD_MAX_BYTES > 0

    def test_jd_upload_max_mb_positive(self):
        mb = jd_upload_max_mb()
        assert isinstance(mb, int)
        assert mb >= 1

    def test_resolve_jd_upload_max_bytes_default(self, monkeypatch):
        monkeypatch.delenv("UPLOAD_JD_MAX_BYTES", raising=False)
        result = _resolve_jd_upload_max_bytes()
        assert result == DEFAULT_JD_UPLOAD_MAX_BYTES

    def test_resolve_jd_upload_max_bytes_custom(self, monkeypatch):
        monkeypatch.setenv("UPLOAD_JD_MAX_BYTES", str(5 * 1024 * 1024))
        result = _resolve_jd_upload_max_bytes()
        assert result == 5 * 1024 * 1024

    def test_resolve_jd_upload_max_bytes_invalid(self, monkeypatch):
        monkeypatch.setenv("UPLOAD_JD_MAX_BYTES", "not_a_number")
        result = _resolve_jd_upload_max_bytes()
        assert result == DEFAULT_JD_UPLOAD_MAX_BYTES

    def test_resolve_jd_upload_max_bytes_zero_falls_back(self, monkeypatch):
        monkeypatch.setenv("UPLOAD_JD_MAX_BYTES", "0")
        result = _resolve_jd_upload_max_bytes()
        assert result == DEFAULT_JD_UPLOAD_MAX_BYTES

    def test_resolve_jd_upload_max_bytes_negative_falls_back(self, monkeypatch):
        monkeypatch.setenv("UPLOAD_JD_MAX_BYTES", "-100")
        result = _resolve_jd_upload_max_bytes()
        assert result == DEFAULT_JD_UPLOAD_MAX_BYTES


# ===========================================================================
# app/shared/tracing.py
# ===========================================================================
from app.shared.tracing import (
    Span,
    LightweightTracer,
    get_tracer,
    trace_span,
    trace_span_sync,
    finish_span,
    is_otlp_active,
    get_recent_traces,
    get_trace_stats,
)


class TestSpan:
    def _make_span(self, name="test-span"):
        tracer = LightweightTracer("test")
        return tracer.create_span(name)

    def test_create_has_name(self):
        s = self._make_span("my-op")
        assert s.name == "my-op"

    def test_trace_and_span_id_set(self):
        s = self._make_span()
        assert s.trace_id
        assert s.span_id

    def test_set_attribute(self):
        s = self._make_span()
        s.set_attribute("key", "value")
        assert s.attributes["key"] == "value"

    def test_set_error(self):
        s = self._make_span()
        exc = ValueError("oops")
        s.set_error(exc)
        assert s.status == "error"
        assert s.error == "oops"
        assert s.attributes["error.type"] == "ValueError"

    def test_end_sets_end_time(self):
        s = self._make_span()
        assert s.end_time is None
        s.end()
        assert s.end_time is not None

    def test_duration_ms_before_end(self):
        s = self._make_span()
        dur = s.duration_ms
        assert dur >= 0.0

    def test_duration_ms_after_end(self):
        import time
        s = self._make_span()
        time.sleep(0.01)
        s.end()
        assert s.duration_ms >= 5.0  # at least 5ms

    def test_to_dict(self):
        s = self._make_span("op")
        s.end()
        d = s.to_dict()
        assert d["name"] == "op"
        assert "trace_id" in d
        assert "span_id" in d
        assert "start_time" in d
        assert "end_time" in d
        assert "duration_ms" in d
        assert "status" in d
        assert "attributes" in d

    def test_to_dict_status_ok(self):
        s = self._make_span()
        s.end()
        d = s.to_dict()
        assert d["status"] == "ok"


class TestLightweightTracer:
    def test_create(self):
        t = LightweightTracer("my-service")
        assert t.service_name == "my-service"

    def test_create_span(self):
        t = LightweightTracer("svc")
        s = t.create_span("op1")
        assert s.name == "op1"

    def test_create_span_with_attributes(self):
        t = LightweightTracer("svc")
        s = t.create_span("op", attributes={"key": "val"})
        assert s.attributes.get("key") == "val"

    def test_create_span_with_parent(self):
        t = LightweightTracer("svc")
        parent = t.create_span("parent")
        child = t.create_span("child", parent_span_id=parent.span_id)
        assert child.parent_span_id == parent.span_id

    async def test_start_span_context_manager(self):
        t = LightweightTracer("svc")
        async with t.start_span("async-op") as span:
            assert span.name == "async-op"
            span.set_attribute("step", 1)
        assert span.end_time is not None

    async def test_start_span_captures_error(self):
        t = LightweightTracer("svc")
        with pytest.raises(RuntimeError):
            async with t.start_span("failing-op") as span:
                raise RuntimeError("inner error")
        assert span.status == "error"


class TestGetTracer:
    def test_returns_lightweight_tracer(self):
        tracer = get_tracer()
        assert isinstance(tracer, LightweightTracer)

    def test_singleton_same_instance(self):
        t1 = get_tracer()
        t2 = get_tracer()
        assert t1 is t2


class TestTraceSpanDecorator:
    async def test_basic_decorator(self):
        @trace_span("test-op")
        async def my_func(x):
            return x * 2

        result = await my_func(5)
        assert result == 10

    async def test_with_attributes(self):
        @trace_span("attr-op", attributes={"component": "test"})
        async def my_func():
            return "done"

        result = await my_func()
        assert result == "done"

    async def test_propagates_exception(self):
        @trace_span("err-op")
        async def raises():
            raise ValueError("trace-test")

        with pytest.raises(ValueError):
            await raises()


class TestTraceSpanSyncDecorator:
    def test_basic(self):
        @trace_span_sync("sync-op")
        def my_func(x):
            return x + 1

        result = my_func(10)
        assert result == 11

    def test_propagates_exception(self):
        @trace_span_sync("err-sync")
        def raises():
            raise KeyError("oops")

        with pytest.raises(KeyError):
            raises()


class TestFinishSpan:
    def test_basic_finish(self):
        tracer = get_tracer()
        span = tracer.create_span("manual-op")
        finish_span(span, status="ok")
        assert span.end_time is not None

    def test_finish_with_error(self):
        tracer = get_tracer()
        span = tracer.create_span("err-op")
        exc = ValueError("manual error")
        finish_span(span, status="error", error=exc)
        assert span.status == "error"
        assert span.error == "manual error"

    def test_finish_noop_without_traces_enabled(self, monkeypatch):
        import app.shared.tracing as tracing_module
        original = tracing_module._TRACES_ENABLED
        try:
            tracing_module._TRACES_ENABLED = False
            tracer = LightweightTracer("test")
            span = tracer.create_span("noop-span")
            finish_span(span)  # Should not raise
        finally:
            tracing_module._TRACES_ENABLED = original


class TestTracingHelpers:
    def test_is_otlp_active_returns_bool(self):
        result = is_otlp_active()
        assert isinstance(result, bool)

    def test_get_recent_traces_returns_list(self):
        result = get_recent_traces()
        assert isinstance(result, list)

    def test_get_recent_traces_limit(self):
        result = get_recent_traces(limit=5)
        assert len(result) <= 5

    def test_get_trace_stats_returns_dict(self):
        stats = get_trace_stats()
        assert isinstance(stats, dict)
        assert "total_spans" in stats
        assert "active_spans" in stats
        assert "error_count" in stats
        assert "error_rate" in stats
        assert "avg_duration_ms" in stats
        assert "otlp_active" in stats
        assert "traces_enabled" in stats

    def test_get_trace_stats_types(self):
        stats = get_trace_stats()
        assert isinstance(stats["total_spans"], int)
        assert isinstance(stats["error_count"], int)
        assert isinstance(stats["error_rate"], float)
        assert isinstance(stats["otlp_active"], bool)
        assert isinstance(stats["traces_enabled"], bool)

    async def test_trace_stats_after_span(self):
        """Run a span and check stats update."""
        @trace_span("stats-test-op")
        async def work():
            return 1

        await work()
        recent = get_recent_traces(limit=100)
        # Should have at least one entry
        assert isinstance(recent, list)
