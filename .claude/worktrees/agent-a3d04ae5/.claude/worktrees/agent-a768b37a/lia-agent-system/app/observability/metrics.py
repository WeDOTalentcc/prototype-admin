"""
Prometheus metrics for LIA Agent System.

8 strategic metrics covering:
- LLM calls (provider, status, latency)
- ReAct agent iterations
- Compliance (FairnessGuard blocks)
- Circuit breaker state
- HTTP request duration
- Pipeline transitions
- Candidates evaluated

Usage:
    from app.observability.metrics import llm_requests_total, llm_latency_seconds

    llm_requests_total.labels(provider="claude", status="success").inc()
    with llm_latency_seconds.labels(provider="claude").time():
        result = await llm_provider.generate(...)
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional

# --- LLM Metrics ---

llm_requests_total = Counter(
    "lia_llm_requests_total",
    "Total number of LLM API calls",
    ["provider", "status"],  # status: success | error | circuit_open
)

llm_latency_seconds = Histogram(
    "lia_llm_latency_seconds",
    "LLM API call latency in seconds",
    ["provider"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

# --- Agent Metrics ---

agent_iterations_total = Counter(
    "lia_agent_iterations_total",
    "Total ReAct loop iterations",
    ["domain", "action_type"],  # action_type: call_tool | respond | ask_clarification | error
)

# --- Compliance Metrics ---

fairness_blocks_total = Counter(
    "lia_fairness_blocks_total",
    "Total FairnessGuard blocked queries",
    ["category"],  # genero | raca_etnia | idade | religiao | etc.
)

# --- Resilience Metrics ---

circuit_breaker_state = Gauge(
    "lia_circuit_breaker_state",
    "Circuit breaker state (0=closed/normal, 1=half_open, 2=open/failing)",
    ["service"],  # anthropic | openai | gemini | pearch | workos | merge
)

# --- HTTP Metrics ---

http_request_duration_seconds = Histogram(
    "lia_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# --- Business Metrics ---

pipeline_transitions_total = Counter(
    "lia_pipeline_transitions_total",
    "Total pipeline stage transitions",
    ["from_stage", "to_stage"],
)

candidates_evaluated_total = Counter(
    "lia_candidates_evaluated_total",
    "Total candidates evaluated by AI",
    ["job_id", "evaluation_type"],  # evaluation_type: cv_screening | rubric | wsi
)


# --- Orchestrator Router Metrics ---

router_tier_hit_total = Counter(
    "lia_router_tier_hit_total",
    "Hits por tier do CascadedRouter",
    ["tier"],  # tier: "memory", "redis_hash", "vector", "fast_router", "llm_cascade", "clarification_needed"
)

router_latency_ms = Histogram(
    "lia_router_latency_ms",
    "Latência do roteamento por tier (ms)",
    ["tier"],
    buckets=[0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000, 5000],
)

router_confidence_histogram = Histogram(
    "lia_router_confidence",
    "Distribuição de confiança do roteador",
    ["model"],  # model: "haiku" | "sonnet" | "opus" | "fast_router" | "vector"
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0],
)

# --- Agent Tool Metrics ---

agent_tool_failures_total = Counter(
    "lia_agent_tool_failures_total",
    "Total de falhas em tool calls dos agentes",
    ["domain", "tool"],
)

# --- Cost Metrics ---

llm_cost_usd_total = Counter(
    "lia_llm_cost_usd_total",
    "Custo estimado de chamadas LLM em USD",
    ["model", "domain"],
)


def generate_latest_metrics() -> bytes:
    """Generate Prometheus metrics in text format."""
    return generate_latest()


PROMETHEUS_CONTENT_TYPE = CONTENT_TYPE_LATEST
