"""
Distributed Tracing with OpenTelemetry.

Provides instrumentation helpers for tracing agent workflows,
domain routing, and LLM calls.

Exporters (em ordem de preferência):
  1. OpenTelemetry SDK com OTLP exporter (quando SDK instalado e OTEL_EXPORTER_OTLP_ENDPOINT configurado)
  2. LightweightTracer interno — compatível, zero dependências

Configuração via env vars:
  OTEL_SERVICE_NAME              — nome do serviço (padrão: lia-agent-system)
  OTEL_EXPORTER_OTLP_ENDPOINT   — ex: http://jaeger:4318 (ativa OTLP export)
  OTEL_TRACES_ENABLED            — true/false (padrão: true)

Cobertura de traces (Z6-02):
  - CascadedRouter.route() → span "router.route"
  - DLQService.push_failure() → span "dlq.push_failure"
  - LearningLoopService.process_unprocessed_feedback() → span "learning.process_feedback"
  - AgentChatWS handle → span "ws.agent_chat"
  - ReAct loop _act() → span "react.act"

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
import functools
import logging
import os
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    error: str | None = None

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

    def to_dict(self) -> dict[str, Any]:
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


_active_spans: dict[str, Span] = {}
_completed_spans: list = []
MAX_COMPLETED_SPANS = 1000


class LightweightTracer:
    def __init__(self, service_name: str = "lia-agent-system"):
        self.service_name = service_name
        self._current_trace_id: str | None = None

    def create_span(
        self,
        name: str,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
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
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
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


_tracer: LightweightTracer | None = None

# Z6-02: flag global para desabilitar tracing (ex: testes)
_TRACES_ENABLED = os.environ.get("OTEL_TRACES_ENABLED", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Z6-02: OTLP Exporter — tentativa de integração com OpenTelemetry SDK real
# ---------------------------------------------------------------------------

_otel_tracer_provider = None  # OTel TracerProvider quando SDK disponível


def _try_init_otlp() -> bool:
    """Tenta inicializar OTLP exporter com o OpenTelemetry SDK.

    Retorna True se inicializado com sucesso, False caso contrário.
    Falha graciosamente — nunca propaga exceção.
    """
    global _otel_tracer_provider
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return False
    try:
        from opentelemetry import trace as otel_trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = os.environ.get("OTEL_SERVICE_NAME", "lia-agent-system")
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
        otel_trace.set_tracer_provider(provider)
        _otel_tracer_provider = provider
        logger.info("[TRACING] OTLP exporter ativado: endpoint=%s service=%s", endpoint, service_name)
        return True
    except ImportError:
        logger.debug("[TRACING] opentelemetry-sdk não instalado — usando LightweightTracer")
        return False
    except Exception as exc:
        logger.debug("[TRACING] OTLP init falhou (gracioso): %s", exc)
        return False


# Tenta inicializar OTLP na importação do módulo
_otlp_active = _try_init_otlp()


def _get_otel_tracer(name: str = "lia-agent-system"):
    """Retorna tracer OpenTelemetry real se SDK disponível, None caso contrário."""
    if not _otlp_active or _otel_tracer_provider is None:
        return None
    try:
        from opentelemetry import trace as otel_trace
        return otel_trace.get_tracer(name)
    except Exception:
        return None


def get_tracer(service_name: str = "lia-agent-system") -> LightweightTracer:
    global _tracer
    if _tracer is None:
        _tracer = LightweightTracer(service_name)
    return _tracer


def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
):
    """Decorador que cria um span para a função async decorada.

    Usa OTLP/OTel SDK se disponível, LightweightTracer como fallback.
    Noop quando OTEL_TRACES_ENABLED=false.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not _TRACES_ENABLED:
                return await func(*args, **kwargs)
            # Tenta OTel SDK primeiro
            otel = _get_otel_tracer()
            if otel is not None:
                try:
                    with otel.start_as_current_span(name) as span:
                        for k, v in (attributes or {}).items():
                            span.set_attribute(k, str(v))
                        return await func(*args, **kwargs)
                except Exception:
                    pass  # fall through to lightweight tracer
            # Fallback: LightweightTracer
            tracer = get_tracer()
            async with tracer.start_span(name, attributes=attributes) as span:
                for key, value in (attributes or {}).items():
                    span.set_attribute(key, value)
                result = await func(*args, **kwargs)
                return result
        return wrapper
    return decorator


def is_otlp_active() -> bool:
    """Retorna True se OTLP exporter está ativo (OpenTelemetry SDK disponível)."""
    return _otlp_active


def get_recent_traces(limit: int = 50) -> list:
    return _completed_spans[-limit:]


def get_trace_stats() -> dict[str, Any]:
    if not _completed_spans:
        return {
            "total_spans": 0,
            "active_spans": len(_active_spans),
            "otlp_active": _otlp_active,
            "traces_enabled": _TRACES_ENABLED,
        }

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
        "otlp_active": _otlp_active,
        "traces_enabled": _TRACES_ENABLED,
    }
