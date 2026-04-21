"""Onda 3.1 G4 (2026-04-21) — LLM cost tracker.

Per-turn cost observability. Producer for [LIA-COST] structured log marker.

Model pricing (USD per 1M tokens, as of 2026-04):
- claude-haiku-4-5: $1.00 input / $5.00 output
- claude-sonnet-4-6: $3.00 input / $15.00 output
- claude-opus-4-5:   $15.00 input / $75.00 output

These prices MAY drift; update this table when Anthropic changes. Logs
include model + tokens so downstream cost reconciliation can recompute
with fresh pricing if needed.
"""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_COST_TRACKING_ENABLED = os.environ.get(
    "LIA_COST_TRACKING_ENABLED", "true"
).lower() == "true"


# Pricing: USD per 1M tokens. Update when Anthropic pricing changes.
# Fallback is haiku pricing (cheapest) to avoid over-inflating cost on
# unknown models.
_PRICING_PER_1M: dict[str, dict[str, float]] = {
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-6-20260104": {"input": 3.00, "output": 15.00},
    "claude-opus-4-5": {"input": 15.00, "output": 75.00},
    # Legacy aliases (pre-4.x)
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
}
_FALLBACK_PRICING = {"input": 1.00, "output": 5.00}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate call cost in USD. Fails soft to $0.00 if model unknown."""
    pricing = _PRICING_PER_1M.get(model, _FALLBACK_PRICING)
    cost_in = (input_tokens / 1_000_000) * pricing["input"]
    cost_out = (output_tokens / 1_000_000) * pricing["output"]
    return round(cost_in + cost_out, 6)


@dataclass
class TenantCostAccumulator:
    """Per-tenant running totals — in-memory. Upgrade to Redis for prod scale."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_usd: float = 0.0
    call_count: int = 0
    by_model: dict[str, int] = field(default_factory=lambda: defaultdict(int))


# Global in-memory store: {tenant_id: TenantCostAccumulator}
_TENANT_COSTS: dict[str, TenantCostAccumulator] = {}


def record_call(
    *,
    tenant_id: str | None,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float | None = None,
) -> dict[str, Any]:
    """Record a single LLM call's token usage + cost.

    Emits [LIA-COST] structured log (catalogued in G2 marker_catalog.yaml
    under category: cost).

    Returns the computed metrics dict for caller inspection.
    """
    if not _COST_TRACKING_ENABLED:
        return {}

    cost_usd = estimate_cost_usd(model, input_tokens, output_tokens)
    tenant_key = str(tenant_id) if tenant_id else "unknown"

    # In-memory accumulator
    acc = _TENANT_COSTS.setdefault(tenant_key, TenantCostAccumulator())
    acc.input_tokens += input_tokens
    acc.output_tokens += output_tokens
    acc.total_usd += cost_usd
    acc.call_count += 1
    acc.by_model[model] = acc.by_model.get(model, 0) + 1

    metrics = {
        "tenant_id": tenant_key,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "tenant_total_usd": round(acc.total_usd, 6),
        "tenant_call_count": acc.call_count,
    }

    logger.info(
        "[LIA-COST] tenant=%s model=%s in=%d out=%d usd=%.6f total=%.4f calls=%d",
        tenant_key, model, input_tokens, output_tokens, cost_usd,
        acc.total_usd, acc.call_count,
    )
    return metrics


def get_tenant_cost(tenant_id: str) -> TenantCostAccumulator | None:
    """Return running totals for a tenant, or None if never tracked."""
    return _TENANT_COSTS.get(str(tenant_id))


def reset_tenant_cost(tenant_id: str | None = None) -> None:
    """Reset in-memory accumulator (for tests or manual clear)."""
    global _TENANT_COSTS
    if tenant_id is None:
        _TENANT_COSTS = {}
    else:
        _TENANT_COSTS.pop(str(tenant_id), None)
