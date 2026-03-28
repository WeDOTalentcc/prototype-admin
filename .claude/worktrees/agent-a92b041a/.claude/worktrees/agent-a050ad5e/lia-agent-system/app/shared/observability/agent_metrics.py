"""
Métricas Prometheus por agente para a plataforma LIA.
Cobertura: latência, tokens, confidence, fairness blocks, HITL triggers.
"""
from __future__ import annotations
import time
import logging
from contextlib import asynccontextmanager
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary

    # ── Contadores ──────────────────────────────────────────────────────────
    AGENT_REQUEST_TOTAL = Counter(
        "lia_agent_request_total",
        "Total de requisições por agente",
        ["agent", "domain", "status"],
    )

    AGENT_FAIRNESS_BLOCKED_TOTAL = Counter(
        "lia_agent_fairness_blocked_total",
        "Requisições bloqueadas pelo FairnessGuard por agente",
        ["agent", "category"],
    )

    AGENT_HITL_TRIGGERED_TOTAL = Counter(
        "lia_agent_hitl_triggered_total",
        "Total de aprovações HITL disparadas por agente",
        ["agent", "action_type"],
    )

    AGENT_TOKENS_TOTAL = Counter(
        "lia_agent_tokens_total",
        "Total de tokens consumidos por agente",
        ["agent", "model", "token_type"],  # token_type: input|output
    )

    # ── Histogramas ─────────────────────────────────────────────────────────
    AGENT_LATENCY_SECONDS = Histogram(
        "lia_agent_latency_seconds",
        "Latência de resposta do agente em segundos",
        ["agent", "domain"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    AGENT_CONFIDENCE = Histogram(
        "lia_agent_confidence",
        "Distribuição de confidence scores por agente",
        ["agent", "domain"],
        buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    )

    _PROMETHEUS_AVAILABLE = True

except ImportError:
    _PROMETHEUS_AVAILABLE = False
    logger.info("[AgentMetrics] prometheus_client não disponível — métricas desabilitadas")


def record_agent_request(agent: str, domain: str, status: str = "success") -> None:
    if _PROMETHEUS_AVAILABLE:
        try:
            AGENT_REQUEST_TOTAL.labels(agent=agent, domain=domain, status=status).inc()
        except Exception:
            pass


def record_fairness_block(agent: str, category: str) -> None:
    if _PROMETHEUS_AVAILABLE:
        try:
            AGENT_FAIRNESS_BLOCKED_TOTAL.labels(agent=agent, category=category).inc()
        except Exception:
            pass


def record_hitl_trigger(agent: str, action_type: str) -> None:
    if _PROMETHEUS_AVAILABLE:
        try:
            AGENT_HITL_TRIGGERED_TOTAL.labels(agent=agent, action_type=action_type).inc()
        except Exception:
            pass


def record_tokens(agent: str, model: str, input_tokens: int, output_tokens: int) -> None:
    if _PROMETHEUS_AVAILABLE:
        try:
            AGENT_TOKENS_TOTAL.labels(agent=agent, model=model, token_type="input").inc(input_tokens)
            AGENT_TOKENS_TOTAL.labels(agent=agent, model=model, token_type="output").inc(output_tokens)
        except Exception:
            pass


def record_confidence(agent: str, domain: str, confidence: float) -> None:
    if _PROMETHEUS_AVAILABLE:
        try:
            AGENT_CONFIDENCE.labels(agent=agent, domain=domain).observe(confidence)
        except Exception:
            pass


@asynccontextmanager
async def agent_latency_timer(agent: str, domain: str):
    """Context manager para medir latência de chamadas de agente."""
    start = time.monotonic()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        elapsed = time.monotonic() - start
        if _PROMETHEUS_AVAILABLE:
            try:
                AGENT_LATENCY_SECONDS.labels(agent=agent, domain=domain).observe(elapsed)
            except Exception:
                pass
        record_agent_request(agent=agent, domain=domain, status=status)
