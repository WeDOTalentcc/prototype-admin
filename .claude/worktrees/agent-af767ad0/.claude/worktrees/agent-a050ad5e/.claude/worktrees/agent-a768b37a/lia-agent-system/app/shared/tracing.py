"""
Distributed Tracing with OpenTelemetry.

Provides instrumentation helpers for tracing agent workflows,
domain routing, and LLM calls. Currently uses console exporter
for development; production would use OTLP exporters.

Note: Full OpenTelemetry SDK is optional. This module provides
lightweight span tracking that works without the SDK installed.

Usage:
    from app.shared.tracing import trace_span, get_tracer
    
    @trace_span("domain.execute", attributes={"domain": "job_management"})
    async def execute_action(...):
        ...
    
    # Or manual spans:
    tracer = get_tracer()
    async with tracer.start_span("custom.operation") as span:
        span.set_attribute("key", "value")
        ...
"""
import time
import uuid
import logging
import functools
from typing import Optional, Dict, Any, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    error: Optional[str] = None

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_error(self, error: Exception) -> None:
        self.status = "error"
        self.error = str(error)
        self.attributes["error.type"] = type(error).__name__

    def end(self) -> None:
        self.end_time = time.time()

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "error": self.error,
            "attributes": self.attributes,
        }


_active_spans: Dict[str, Span] = {}
_completed_spans: list = []
MAX_COMPLETED_SPANS = 1000


class LightweightTracer:
    def __init__(self, service_name: str = "lia-agent-system"):
        self.service_name = service_name
        self._current_trace_id: Optional[str] = None

    def create_span(
        self,
        name: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        trace_id = self._current_trace_id or uuid.uuid4().hex[:16]
        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=parent_span_id,
            attributes=attributes or {},
        )
        span.set_attribute("service.name", self.service_name)
        _active_spans[span.span_id] = span
        return span

    @asynccontextmanager
    async def start_span(
        self,
        name: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        span = self.create_span(name, parent_span_id, attributes)
        try:
            yield span
        except Exception as e:
            span.set_error(e)
            raise
        finally:
            span.end()
            _active_spans.pop(span.span_id, None)
            if len(_completed_spans) >= MAX_COMPLETED_SPANS:
                _completed_spans.pop(0)
            _completed_spans.append(span.to_dict())

            logger.debug(
                f"[TRACE] {span.name} completed in {span.duration_ms:.1f}ms "
                f"(trace={span.trace_id}, status={span.status})"
            )

    def set_trace_id(self, trace_id: str) -> None:
        self._current_trace_id = trace_id


_tracer: Optional[LightweightTracer] = None


def get_tracer(service_name: str = "lia-agent-system") -> LightweightTracer:
    global _tracer
    if _tracer is None:
        _tracer = LightweightTracer(service_name)
    return _tracer


def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            async with tracer.start_span(name, attributes=attributes) as span:
                for key, value in (attributes or {}).items():
                    span.set_attribute(key, value)
                result = await func(*args, **kwargs)
                return result
        return wrapper
    return decorator


def get_recent_traces(limit: int = 50) -> list:
    return _completed_spans[-limit:]


def get_trace_stats() -> Dict[str, Any]:
    if not _completed_spans:
        return {"total_spans": 0, "active_spans": len(_active_spans)}

    durations = [s["duration_ms"] for s in _completed_spans]
    errors = sum(1 for s in _completed_spans if s["status"] == "error")

    return {
        "total_spans": len(_completed_spans),
        "active_spans": len(_active_spans),
        "error_count": errors,
        "error_rate": round(errors / len(_completed_spans), 4),
        "avg_duration_ms": round(sum(durations) / len(durations), 2),
        "max_duration_ms": round(max(durations), 2),
        "min_duration_ms": round(min(durations), 2),
    }
