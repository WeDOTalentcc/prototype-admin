"""
prompt_experiment.py — A/B testing framework for LIA agent prompts.

Sprint 2, Task P03: PromptExperiment A/B Runner.

Provides deterministic variant selection (by session_id hash), async result
recording (Redis-backed with in-memory fallback), and per-variant statistics.

Compliance note:
    EU AI Act Art. 13 — rastreabilidade de decisões do sistema de IA.
    All experiment results are persisted with timestamp and variant metadata
    to support auditability and decision traceability.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from statistics import mean, quantiles

try:
    import redis.asyncio as aioredis  # type: ignore[union-attr]
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

try:
    import yaml  # type: ignore[union-attr]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level experiment registry (P03)
# ---------------------------------------------------------------------------
_experiments: dict[str, PromptExperiment] = {}


def get_experiment(experiment_id: str) -> PromptExperiment | None:
    """Return a registered PromptExperiment by its ID, or None if not found.

    Args:
        experiment_id: Unique identifier for the experiment.

    Returns:
        The PromptExperiment instance, or None.
    """
    return _experiments.get(experiment_id)


def register_experiment(experiment: PromptExperiment) -> None:
    """Register a PromptExperiment in the module-level registry.

    Args:
        experiment: The PromptExperiment instance to register.
    """
    _experiments[experiment.experiment_id] = experiment
    logger.info("[P03] Registered experiment '%s' with %d variants",
                experiment.experiment_id, len(experiment.variants))


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PromptVariant:
    """A single prompt variant in an A/B experiment.

    Attributes:
        variant_id:   Unique identifier for this variant (e.g. "control", "v2").
        prompt_text:  The actual prompt text to be used.
        weight:       Relative selection weight in [0, 1]. Variants are
                      normalised so weights need not sum to 1. Default 0.5.
    """
    variant_id: str
    prompt_text: str
    weight: float = 0.5


@dataclass
class ExperimentResult:
    """Recorded outcome of a single prompt inference call.

    Attributes:
        variant_id:     Which variant was used.
        response_text:  The model's response.
        latency_ms:     Wall-clock inference latency in milliseconds.
        tokens_used:    Total tokens consumed (prompt + completion).
        quality_score:  Optional human/automated quality rating in [0, 1].
        timestamp:      UTC datetime of the inference call.

    Compliance note:
        EU AI Act Art. 13 — rastreabilidade de decisões do sistema de IA.
    """
    variant_id: str
    response_text: str
    latency_ms: float
    tokens_used: int
    quality_score: float | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    # Task #1144: company_id is required for tenant-namespaced Redis keys.
    # Default ``""`` triggers a namespace-violation log/Prometheus increment
    # (sentinel S9) but does not break legacy callers.
    company_id: str = ""


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------

class PromptExperiment:
    """A/B testing experiment for prompt variants.

    Deterministically assigns sessions to variants via hash-based weighted
    selection.  Results are stored in Redis (if available) with an in-memory
    dict fallback.

    Compliance note:
        EU AI Act Art. 13 — rastreabilidade de decisões do sistema de IA.

    Args:
        experiment_id:      Unique name for the experiment.
        variants:           List of PromptVariant objects.
        metrics_ttl_seconds: TTL for Redis keys storing daily metrics.
                             Defaults to 86 400 (24 h).
    """

    def __init__(
        self,
        experiment_id: str,
        variants: list[PromptVariant],
        metrics_ttl_seconds: int = 86_400,
    ) -> None:
        if not variants:
            raise ValueError("PromptExperiment requires at least one variant.")
        self.experiment_id = experiment_id
        self.variants = variants
        self.metrics_ttl_seconds = metrics_ttl_seconds

        # Normalise weights so they sum to 1.0
        total_weight = sum(v.weight for v in variants)
        if total_weight <= 0:
            raise ValueError("Sum of variant weights must be > 0.")
        self._normalised_weights: list[float] = [
            v.weight / total_weight for v in variants
        ]
        # Cumulative breakpoints for deterministic selection
        self._cumulative: list[float] = []
        cumsum = 0.0
        for w in self._normalised_weights:
            cumsum += w
            self._cumulative.append(cumsum)

        # In-memory fallback storage: key -> list of result dicts
        self._memory_store: dict[str, list[dict]] = {}

        # Optional Redis client (lazy-initialised)
        self._redis: object | None = None
        self._redis_checked = False

        logger.info(
            "[P03] PromptExperiment '%s' initialised with variants: %s",
            experiment_id,
            [v.variant_id for v in variants],
        )

    # ------------------------------------------------------------------
    # Variant selection
    # ------------------------------------------------------------------

    def select_variant(self, session_id: str) -> PromptVariant:
        """Deterministically select a variant for the given session.

        The same session_id will always receive the same variant, ensuring
        consistent UX within a session.  Selection is weighted by
        ``PromptVariant.weight``.

        Args:
            session_id: Unique identifier for the user session.

        Returns:
            The selected PromptVariant.
        """
        digest = hashlib.sha256(
            f"{self.experiment_id}:{session_id}".encode()
        ).hexdigest()
        # Map first 8 hex chars → float in [0, 1)
        bucket = int(digest[:8], 16) / 0xFFFFFFFF

        for i, threshold in enumerate(self._cumulative):
            if bucket < threshold:
                variant = self.variants[i]
                logger.debug(
                    "[P03] session='%s' → variant='%s' (bucket=%.4f)",
                    session_id, variant.variant_id, bucket,
                )
                return variant

        # Fallback: return last variant (handles floating-point edge)
        return self.variants[-1]

    # ------------------------------------------------------------------
    # Redis helpers
    # ------------------------------------------------------------------

    async def _get_redis(self) -> object | None:
        """Return a Redis client if available, else None."""
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        if not _REDIS_AVAILABLE:
            logger.debug("[P03] redis package not installed; using in-memory store.")
            return None
        try:
            import os
            _redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
            try:
                from lia_config.config import settings as _cfg
                _redis_url = getattr(_cfg, "REDIS_URL", _redis_url) or _redis_url
            except Exception:
                pass
            client = aioredis.from_url(_redis_url, decode_responses=True)
            await client.ping()
            self._redis = client
            logger.info("[P03] Redis connection established for experiment '%s'.", self.experiment_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[P03] Redis unavailable (%s); using in-memory fallback.", exc)
            self._redis = None
        return self._redis

    def _redis_key(self, variant_id: str, day: date, company_id: str = "") -> str:
        """Build tenant-namespaced Redis key (Task #1144).

        Shape: ``prompt_exp:<company_id>:<experiment_id>:<variant_id>:<day>``.
        Empty ``company_id`` falls back to ``__unknown__`` and records a
        namespace violation (sentinel S9 surfaces it via Prometheus).
        """
        from app.shared.security.tenant_redis_namespace import (
            record_namespace_violation,
            tenant_namespaced_key,
        )
        suffix = f"{self.experiment_id}:{variant_id}:{day}"
        if not company_id:
            # Fail-loud in prod (raises). In dev/test the violation is logged
            # and we return a clearly-marked unknown bucket so unit tests can
            # observe the violation. No broad except wrapping the helper.
            record_namespace_violation("prompt_experiment")
            return f"prompt_exp:__unknown__:{suffix}"
        return tenant_namespaced_key("prompt_exp", company_id, suffix)

    # ------------------------------------------------------------------
    # Result recording
    # ------------------------------------------------------------------

    async def record_result(self, result: ExperimentResult) -> None:
        """Persist an ExperimentResult.

        Stores to Redis (as a JSON-like hash) when available, falling back to
        an in-memory dict keyed by
        ``prompt_exp:{experiment_id}:{variant_id}:{date}``.

        Args:
            result: The ExperimentResult to record.

        Compliance note:
            EU AI Act Art. 13 — rastreabilidade de decisões do sistema de IA.
        """
        key = self._redis_key(result.variant_id, result.timestamp.date(), result.company_id)
        entry = {
            "latency_ms": result.latency_ms,
            "tokens_used": result.tokens_used,
            "quality_score": result.quality_score,
            "timestamp": result.timestamp.isoformat(),
        }

        redis_client = await self._get_redis()
        if redis_client is not None:
            try:
                import json
                pipe = redis_client.pipeline()
                pipe.rpush(key, json.dumps(entry))
                pipe.expire(key, self.metrics_ttl_seconds)
                await pipe.execute()
                logger.debug("[P03] Result recorded to Redis key='%s'.", key)
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("[P03] Redis write failed (%s); falling back to memory.", exc)

        # In-memory fallback
        if key not in self._memory_store:
            self._memory_store[key] = []
        self._memory_store[key].append(entry)
        logger.debug("[P03] Result recorded in-memory key='%s'.", key)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict[str, dict]:
        """Compute per-variant statistics across all recorded results.

        Returns:
            A dict keyed by variant_id, each containing:
                - ``n_calls`` (int)
                - ``avg_latency_ms`` (float | None)
                - ``avg_quality_score`` (float | None)
                - ``p95_latency_ms`` (float | None)
        """
        import json

        stats: dict[str, dict] = {}
        for variant in self.variants:
            latencies: list[float] = []
            qualities: list[float] = []

            redis_client = await self._get_redis()

            # Collect from Redis (all matching keys for this variant)
            if redis_client is not None:
                try:
                    # Scan for all daily keys for this variant
                    # Task #1144: tenant-namespaced layout
                    # ``prompt_exp:<company_id>:<experiment_id>:<variant_id>:*``.
                    # The leading ``*`` is intentional — stats are
                    # per-experiment, aggregated across tenants for the admin
                    # plane. Tenant-scoped stats should pass a company_id
                    # filter in a future PR (Task #1129 follow-up).
                    pattern = f"prompt_exp:*:{self.experiment_id}:{variant.variant_id}:*"
                    keys = []
                    async for key in redis_client.scan_iter(pattern):
                        keys.append(key)
                    for key in keys:
                        raw_entries = await redis_client.lrange(key, 0, -1)
                        for raw in raw_entries:
                            entry = json.loads(raw)
                            latencies.append(float(entry["latency_ms"]))
                            if entry.get("quality_score") is not None:
                                qualities.append(float(entry["quality_score"]))
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[P03] Redis read failed for stats (%s).", exc)

            # Also collect from in-memory store (may have entries after Redis failure)
            # Task #1144: keys now embed company_id between the prefix and
            # the experiment_id. Match any tenant for aggregate stats.
            mem_substr = f":{self.experiment_id}:{variant.variant_id}:"
            for key, entries in self._memory_store.items():
                if key.startswith("prompt_exp:") and mem_substr in key:
                    for entry in entries:
                        latencies.append(float(entry["latency_ms"]))
                        if entry.get("quality_score") is not None:
                            qualities.append(float(entry["quality_score"]))

            n = len(latencies)
            avg_latency = mean(latencies) if n > 0 else None
            avg_quality = mean(qualities) if qualities else None
            p95_latency: float | None = None
            if n >= 2:
                # quantiles() needs at least 2 data points; n=1 → use the value itself
                p95_latency = quantiles(latencies, n=20)[18]  # 95th percentile
            elif n == 1:
                p95_latency = latencies[0]

            stats[variant.variant_id] = {
                "n_calls": n,
                "avg_latency_ms": avg_latency,
                "avg_quality_score": avg_quality,
                "p95_latency_ms": p95_latency,
            }

        return stats

    # ------------------------------------------------------------------
    # YAML loader
    # ------------------------------------------------------------------

    @classmethod
    async def from_yaml(
        cls, experiment_id: str, yaml_path: str
    ) -> PromptExperiment:
        """Load a PromptExperiment from a YAML configuration file.

        Expected YAML structure::

            metrics_ttl_seconds: 86400   # optional
            variants:
              - variant_id: control
                prompt_text: "You are a helpful assistant."
                weight: 0.5
              - variant_id: v2
                prompt_text: "You are an expert recruiter assistant."
                weight: 0.5

        Args:
            experiment_id: Unique identifier for the experiment.
            yaml_path:     Absolute or relative path to the YAML file.

        Returns:
            A fully-initialised PromptExperiment instance.

        Raises:
            ImportError: If the ``pyyaml`` package is not installed.
            FileNotFoundError: If yaml_path does not exist.
            ValueError: If the YAML is missing required fields.
        """
        if not _YAML_AVAILABLE:
            raise ImportError(
                "pyyaml is required for PromptExperiment.from_yaml(). "
                "Install it with: pip install pyyaml"
            )

        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, _read_file, yaml_path)
        data = yaml.safe_load(raw)

        ttl = int(data.get("metrics_ttl_seconds", 86_400))
        raw_variants = data.get("variants")
        if not raw_variants:
            raise ValueError(f"YAML at '{yaml_path}' must contain a 'variants' list.")

        variants = [
            PromptVariant(
                variant_id=v["variant_id"],
                prompt_text=v["prompt_text"],
                weight=float(v.get("weight", 0.5)),
            )
            for v in raw_variants
        ]

        instance = cls(
            experiment_id=experiment_id,
            variants=variants,
            metrics_ttl_seconds=ttl,
        )
        logger.info(
            "[P03] Loaded PromptExperiment '%s' from '%s' (%d variants).",
            experiment_id, yaml_path, len(variants),
        )
        return instance


def _read_file(path: str) -> str:
    """Synchronous helper to read a file (run in executor)."""
    with open(path, encoding="utf-8") as fh:
        return fh.read()
