"""
Testes unitários para as novas métricas Prometheus do Fase 3.

Cobertura:
- router_tier_hit_total (Counter com label "tier")
- router_latency_ms (Histogram com label "tier")
- router_confidence_histogram (Histogram com label "model")
- agent_tool_failures_total (Counter com labels "domain", "tool")
- llm_cost_usd_total (Counter com labels "model", "domain")
- Incremento sem erros
- CascadedRouter importa sem quebrar com métricas
"""
import pytest


def test_router_tier_hit_counter_exists():
    """Verifica que router_tier_hit_total existe e tem label 'tier'."""
    from app.observability.metrics import router_tier_hit_total

    assert router_tier_hit_total is not None
    # Verificar que aceita o label "tier" sem erro
    counter = router_tier_hit_total.labels(tier="memory")
    assert counter is not None


def test_router_latency_histogram_exists():
    """Verifica que router_latency_ms existe e tem label 'tier'."""
    from app.observability.metrics import router_latency_ms

    assert router_latency_ms is not None
    hist = router_latency_ms.labels(tier="fast_router")
    assert hist is not None


def test_router_confidence_histogram_exists():
    """Verifica que router_confidence_histogram existe e tem label 'model'."""
    from app.observability.metrics import router_confidence_histogram

    assert router_confidence_histogram is not None
    hist = router_confidence_histogram.labels(model="haiku")
    assert hist is not None


def test_agent_tool_failures_exists():
    """Verifica agent_tool_failures_total com labels domain e tool."""
    from app.observability.metrics import agent_tool_failures_total

    assert agent_tool_failures_total is not None
    counter = agent_tool_failures_total.labels(domain="cv_screening", tool="evaluate_candidate")
    assert counter is not None


def test_llm_cost_counter_exists():
    """Verifica llm_cost_usd_total com labels model e domain."""
    from app.observability.metrics import llm_cost_usd_total

    assert llm_cost_usd_total is not None
    counter = llm_cost_usd_total.labels(model="claude-haiku", domain="job_management")
    assert counter is not None


def test_metrics_can_be_incremented():
    """Incrementa cada counter e verifica que não lança exceções."""
    from app.observability.metrics import (
        router_tier_hit_total,
        router_latency_ms,
        router_confidence_histogram,
        agent_tool_failures_total,
        llm_cost_usd_total,
    )

    # Counters — inc()
    router_tier_hit_total.labels(tier="memory").inc()
    router_tier_hit_total.labels(tier="redis_hash").inc()
    router_tier_hit_total.labels(tier="vector").inc()
    router_tier_hit_total.labels(tier="fast_router").inc()
    router_tier_hit_total.labels(tier="llm_cascade").inc()
    router_tier_hit_total.labels(tier="clarification_needed").inc()

    agent_tool_failures_total.labels(domain="sourcing", tool="search_candidates").inc()
    llm_cost_usd_total.labels(model="claude-sonnet", domain="pipeline").inc(0.001)

    # Histograms — observe()
    router_latency_ms.labels(tier="memory").observe(0.5)
    router_latency_ms.labels(tier="fast_router").observe(2.3)
    router_latency_ms.labels(tier="llm_cascade").observe(250.0)

    router_confidence_histogram.labels(model="haiku").observe(0.85)
    router_confidence_histogram.labels(model="sonnet").observe(0.92)
    router_confidence_histogram.labels(model="fast_router").observe(0.95)
    router_confidence_histogram.labels(model="vector").observe(0.93)


def test_router_metrics_instrumented_in_cascaded_router():
    """
    Importa CascadedRouter e verifica que a instrumentação de métricas
    não causa erros na inicialização (lazy import funciona corretamente).
    """
    from app.orchestrator.cascaded_router import CascadedRouter, _get_metrics

    # _get_metrics deve retornar as 3 métricas ou (None, None, None) — nunca deve lançar
    hit_counter, latency_hist, conf_hist = _get_metrics()
    # Com métricas disponíveis, devem retornar objetos válidos
    assert hit_counter is not None
    assert latency_hist is not None
    assert conf_hist is not None

    # CascadedRouter deve instanciar sem erros
    router = CascadedRouter()
    assert router is not None
