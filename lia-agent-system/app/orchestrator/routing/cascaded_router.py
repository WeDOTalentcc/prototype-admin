"""
Cascaded Router - 8-tier routing: memory → redis → vector → fast → LLM → autonomous → studio → clarification.

Hierarquia de resolução (custo crescente):
  Tier 0: MemoryResolver       — pronomes/referências de contexto
  Tier 1: LRU in-process       — hash MD5 em memória local (O(1))
  Tier 2: Redis hash cache      — distribuído, exato, compartilhado entre workers
  Tier 3: VectorSemanticCache   — pgvector, cosine similarity >= 0.85
  Tier 4: FastRouter            — regex/keyword (O(n) patterns)
  Tier 5: LLM Cascade           — Haiku→Sonnet→Opus (caro)
  Tier 6: REMOVED Sprint 12.3-B (was AutonomousReActAgent cross-domain fallback; env never set in prod)
  Fallback: clarification_needed — pergunta ao usuário quando tudo falha
"""
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.orchestrator.routing.domain_mappings import AGENT_TYPE_TO_DOMAIN, resolve_domain
from app.orchestrator.routing.fast_router import FastRouter
from app.orchestrator.memory.semantic_cache import SemanticCache
from app.shared.tracing import get_tracer, trace_span
from app.orchestrator.context.intent_types import OrchestratorIntentResult

logger = logging.getLogger(__name__)

AB_EXPERIMENT_ID = "cascade_router_system_prompt"
_ab_experiment_initialized = False


def _get_metrics():
    """Metrics stub — Prometheus removed (Task #138). Returns None.

    T-04 Tipo D: try/except is deliberately empty here. This stub
    replaced a real Prometheus integration (Task #138) and is kept
    as a no-op shim so call sites don't have to be rewritten. The
    except branch is unreachable (literal returns can't fail), but
    is kept to preserve the original signature contract for the
    eventual restoration of metrics.
    """
    try:
        return None, None, None
    except Exception:
        # Branch inalcancavel (literal return): mantida para preservar signature contract
        # ate restauracao do Prometheus stack (Task #138 followup)
        return None, None, None


@dataclass
class RouteResult:
    domain_id: str
    confidence: float
    source: str
    matched_pattern: str | None = None
    intent_details: OrchestratorIntentResult | None = None
    cached: bool = False
    resolved_at: datetime = field(default_factory=datetime.utcnow)
    # Campos de clarificação (Fase 2 — Gap #2)
    needs_clarification: bool = False
    clarification_question: str | None = None
    clarification_options: list[str] | None = None



from app.shared.prompts.system_prompt_builder import SystemPromptBuilder


def _build_clarification_question(
    message: str,
    partial_matches: list[dict] | None = None,
    user_name: str = "",
) -> tuple[str, list[str]]:
    """Gera clarificação contextual baseada nos matches parciais do roteamento."""
    question, options = SystemPromptBuilder.build_clarification(
        message=message,
        partial_matches=partial_matches,
        user_name=user_name,
    )
    return question, options


def _init_ab_experiment() -> None:
    global _ab_experiment_initialized
    if _ab_experiment_initialized:
        return
    _ab_experiment_initialized = True
    try:
        from app.shared.prompt_experiment import (
            PromptExperiment,
            PromptVariant as PEVariant,
            register_experiment,
        )
        yaml_path = (
            Path(__file__).parent.parent / "prompts" / "experiments" / "cascade_router_system_prompt.yaml"
        )
        if yaml_path.exists():
            import yaml
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            variants = [
                PEVariant(
                    variant_id=v["variant_id"],
                    prompt_text=v["prompt_text"],
                    weight=float(v.get("weight", 0.5)),
                )
                for v in data.get("variants", [])
            ]
            if variants:
                exp = PromptExperiment(
                    experiment_id=AB_EXPERIMENT_ID,
                    variants=variants,
                    metrics_ttl_seconds=int(data.get("metrics_ttl_seconds", 604800)),
                )
                register_experiment(exp)
                try:
                    from app.domains.ai.services.prompt_version_registry import prompt_version_registry
                    for v in variants:
                        prompt_version_registry.register(
                            name=f"{AB_EXPERIMENT_ID}:{v.variant_id}",
                            version="1.0.0",
                            template=v.prompt_text,
                        )
                except Exception:
                    pass
                logger.info("[A/B] CascadeRouter experiment '%s' registered with %d variants", AB_EXPERIMENT_ID, len(variants))
        else:
            logger.debug("[A/B] CascadeRouter experiment YAML not found at %s", yaml_path)
    except Exception as exc:
        logger.warning("[A/B] Failed to init CascadeRouter experiment: %s", exc)


class CascadedRouter:
    def __init__(
        self,
        fast_router: FastRouter | None = None,
        domain_registry: Any | None = None,
        cache_max_size: int = settings.ROUTER_CACHE_MAX_SIZE,
    ):
        self.fast = fast_router or FastRouter()
        self.registry = domain_registry
        self._memory_cache: dict[str, RouteResult] = {}
        self._cache_max_size = cache_max_size
        self._redis_cache = SemanticCache(ttl=settings.ROUTER_CACHE_TTL)
        self._vector_cache = self._init_vector_cache()
        self._stats = {
            "memory_hits": 0,
            "redis_hits": 0,
            "vector_hits": 0,
            "fast_hits": 0,
            "llm_hits": 0,
            "autonomous_hits": 0,
            "studio_agent_hits": 0,
            "clarification_issued": 0,
            "total": 0,
        }
        _init_ab_experiment()

    def _init_vector_cache(self):
        """Inicializa VectorSemanticCache (gracioso — nunca falha na init).

        Z5-03: respeita ROUTER_VECTOR_CACHE_ENABLED para A/B testing.
        Threshold injetado via settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD.
        """
        try:
            if not settings.ROUTER_VECTOR_CACHE_ENABLED:
                logger.debug("[CascadedRouter] Tier 3 (vector cache) desabilitado via ROUTER_VECTOR_CACHE_ENABLED=false")
                return None
            from app.orchestrator.memory.vector_semantic_cache import VectorSemanticCache
            return VectorSemanticCache(
                similarity_threshold=settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD,
            )
        except Exception as exc:
            logger.debug("[CascadedRouter] VectorSemanticCache não disponível: %s", exc)
            return None

    def _cache_key(self, message: str, company_id: str | None = None) -> str:
        """Tier-1 LRU key — Task #1144: must include company_id.

        Two tenants sending the same message MUST NOT collide on the
        in-process memory cache. ``company_id=None`` is preserved only for
        legacy call sites in tests; the live router path always passes a
        concrete value (or ``"__unknown__"`` if the request had none, which
        is logged via ``record_namespace_violation``).
        """
        normalized = message.lower().strip()
        digest = hashlib.md5(normalized.encode()).hexdigest()
        cid = company_id or "__unknown__"
        return f"{cid}:{digest}"

    def _wizard_domain_override(self, message: str, cached_domain: str) -> bool:
        """Return True if fast router strongly identifies wizard domain for this message,
        while the cache holds a different (stale) non-wizard entry.

        harness-engineering [sensor computacional] — guards LRU/Redis Tier 1/2 against
        returning stale job_management entries for wizard-patterned messages.
        Fail-open: any exception returns False (trust cache).

        Post-mortem 2026-04-30: without this, Tier 1/2 could return stale job_management
        entries for "criar uma vaga", bypassing the Tier 2.5 wizard guard entirely.
        """
        if cached_domain == "wizard":
            return False  # already wizard — no override needed

        try:
            result = self.fast.match(message)
            if result is None:
                return False
            threshold = settings.ROUTER_FAST_CONFIDENCE_THRESHOLD
            return result.domain_id == "wizard" and result.confidence >= threshold
        except Exception:
            # T-04 Tipo B: fail-open is intentional (trust the cache decision),
            # but the matcher failure itself must be visible so operators can
            # diagnose router regressions.
            logger.warning(
                "[CascadedRouter] _should_override_to_wizard matcher failed, fail-open=False",
                exc_info=True,
            )
            return False  # fail-open: trust cache on error

    @trace_span("router.route", attributes={"component": "cascaded_router"})
    async def route(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> RouteResult:
        self._stats["total"] += 1
        _hit_counter, _latency_hist, _conf_hist = _get_metrics()

        _tracer = get_tracer()

        # PR-A Tier 0.0 — Rail A hint override (FE-H03 do audit enterprise).
        # Cobre TODOS os transports: WS via MainOrchestrator + SSE/REST que
        # chamam CascadedRouter direto. Curto-circuita os tiers 0-4 quando
        # FE forneceu metadata estruturada com domain_hint válido.
        # Skill canônica: harness-engineering [guide computacional].
        if context:
            try:
                from app.orchestrator.services.rail_a_hint_override import try_hint_route
                _hint_route = try_hint_route(context)
                if _hint_route is not None:
                    logger.info(
                        "[CascadedRouter] rail_a_hint override: card=%s → domain=%s intent=%s",
                        (context.get("metadata") or {}).get("card_id", "?"),
                        _hint_route.domain_id,
                        ((_hint_route.intent_details.to_dict() if hasattr(_hint_route.intent_details, "to_dict") else (_hint_route.intent_details or {})) or {}).get("raw_intent", "?"),
                    )
                    if _hit_counter:
                        _hit_counter.labels(tier="rail_a_hint").inc()
                    return _hint_route
            except Exception as _hint_exc:
                logger.debug("[CascadedRouter] rail_a_hint check skipped: %s", _hint_exc)

        # ── Wizard session-pin REMOVED (Task #1080 canonical refactor) ────
        # Originally Tier 0.5 of this router checked for an open wizard
        # checkpoint and short-circuited with ``domain_id="wizard"``. That
        # was the wrong layer: the router should be domain-agnostic, and
        # placing transport-specific session bookkeeping here forced 5
        # concurrent sources of truth ("this conversation is the wizard")
        # to stay in sync. The canonical pin now lives in the WS / SSE
        # handlers, immediately before they invoke this router (see
        # ``app.api.v1.agent_chat_ws`` and ``agent_chat_sse``). The
        # ``main_orchestrator`` REST path uses the same canonical helper
        # ``app.shared.sessions.is_wizard_session_active`` directly.

        # Tier 0 — Resolver pronomes/referências via WorkingMemory antes de rotear
        if session_id:
            async with _tracer.start_span("router.tier0_memory_resolve", attributes={
                "tier_name": "tier0_memory_resolve", "service": "cascaded_router",
            }) as _t0_span:
                try:
                    from app.orchestrator.memory.memory_resolver import memory_resolver
                    resolved_message, was_resolved = await memory_resolver.resolve(
                        message=message,
                        session_id=session_id,
                        domain=(context or {}).get("domain"),
                    )
                    if was_resolved:
                        logger.debug(
                            "CascadedRouter: memory resolution applied for session=%s", session_id
                        )
                        message = resolved_message
                    _t0_span.set_attribute("was_resolved", str(was_resolved))
                except Exception as _mem_exc:
                    logger.debug("CascadedRouter: memory resolver skipped: %s", _mem_exc)
                    _t0_span.set_attribute("skipped", str(_mem_exc))

        # Task #1144: Redis cache must be tenant-namespaced. Extract company_id
        # from context once and pass it to every ``self._redis_cache.*`` call
        # below. Falls back to ``"__unknown__"`` only for the local LRU cache
        # key (which already lives in-process per worker); Redis layer will
        # reject empty company_id via ``CompanyId.parse``.
        _company_id_for_cache = (context or {}).get("company_id") or "__unknown__"
        # Task #1144: SemanticCache delegates to CompanyId.parse, which
        # rejects ``"__unknown__"`` (and all forbidden literals). When the
        # caller did not inject a company_id we MUST NOT call into the
        # Redis layer at all — instead we skip it (Tier-1 LRU still works
        # in-process) and record the violation for sentinel S9.
        _redis_cache_enabled = _company_id_for_cache != "__unknown__"
        if not _redis_cache_enabled:
            try:
                from app.shared.security.tenant_redis_namespace import (
                    record_namespace_violation,
                )
                record_namespace_violation("cascaded_router.unknown_company")
            except RuntimeError:
                # Production fail-loud: re-raise so the request fails cleanly
                # instead of leaking into the cross-tenant "__unknown__" bucket.
                raise
            except Exception:
                # T-04 Tipo B: namespace_violation metric is observability
                # for multi-tenancy invariant breach. Importing/recording
                # may fail in dev/test (no redis), but we must not silently
                # swallow in case it's a production regression.
                logger.warning(
                    "[CascadedRouter] record_namespace_violation failed",
                    exc_info=True,
                )
        cache_key = self._cache_key(message, _company_id_for_cache)

        # Tier 1 — LRU in-process (hash MD5, O(1))
        async with _tracer.start_span("router.tier1_lru_cache", attributes={
            "tier_name": "tier1_lru_cache", "service": "cascaded_router", "match_type": "exact_hash",
        }) as _t1_span:
            _t0 = time.perf_counter()
            cached = self._memory_cache.get(cache_key)
            if cached:
                _elapsed_ms = (time.perf_counter() - _t0) * 1000
                self._stats["memory_hits"] += 1
                if _hit_counter:
                    _hit_counter.labels(tier="memory").inc()
                if _latency_hist:
                    _latency_hist.labels(tier="memory").observe(_elapsed_ms)
                _t1_span.set_attribute("hit", "true")
                _t1_span.set_attribute("confidence_score", str(cached.confidence))
                _t1_span.set_attribute("domain_id", cached.domain_id)
                _t1_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")
                logger.debug("CascadedRouter: memory hit for '%s...' → %s", message[:40], cached.domain_id)
                return RouteResult(
                    domain_id=cached.domain_id,
                    confidence=cached.confidence,
                    source="memory",
                    matched_pattern=cached.matched_pattern,
                    cached=True,
                )
            _t1_span.set_attribute("hit", "false")
            _t1_span.set_attribute("confidence_score", "0.0")
            _t1_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")

        # Tier 2 — Redis hash cache (distribuído, exato)
        async with _tracer.start_span("router.tier2_redis_cache", attributes={
            "tier_name": "tier2_redis_cache", "service": "cascaded_router", "match_type": "exact_hash",
        }) as _t2_span:
            _t0 = time.perf_counter()
            redis_hit = (
                await self._redis_cache.get(_company_id_for_cache, message)
                if _redis_cache_enabled
                else None
            )
            if redis_hit:
                _elapsed_ms = (time.perf_counter() - _t0) * 1000
                self._stats["redis_hits"] += 1
                if _hit_counter:
                    _hit_counter.labels(tier="redis_hash").inc()
                if _latency_hist:
                    _latency_hist.labels(tier="redis_hash").observe(_elapsed_ms)
                _t2_span.set_attribute("hit", "true")
                _t2_span.set_attribute("confidence_score", str(redis_hit.get("confidence", 0.7)))
                _t2_span.set_attribute("domain_id", redis_hit.get("domain_id", ""))
                _t2_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")
                logger.debug("CascadedRouter: redis hit for '%s...' → %s", message[:40], redis_hit.get("domain_id"))
                return RouteResult(
                    domain_id=redis_hit.get("domain_id", "recruiter_assistant"),
                    confidence=redis_hit.get("confidence", 0.7),
                    source="redis_cache",
                    matched_pattern=redis_hit.get("matched_pattern"),
                    cached=True,
                )
            _t2_span.set_attribute("hit", "false")
            _t2_span.set_attribute("confidence_score", "0.0")
            _t2_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")

        # Tier 2.5 — Wizard Guard (anti-poisoning sensor)
        # Pre-checks FastRouter for wizard domain BEFORE consulting the vector cache.
        # Prevents stale vector cache entries (e.g. job_management for "criar vaga")
        # from overriding a strong wizard-domain signal from the fast router.
        # R-025: harness-engineering sensor — computacional, feedforward.
        _t25_fast_prefetch = self.fast.match(message)
        if (
            _t25_fast_prefetch is not None
            and _t25_fast_prefetch.domain_id == "wizard"
            and _t25_fast_prefetch.confidence >= settings.ROUTER_FAST_CONFIDENCE_THRESHOLD
        ):
            _t25_result = RouteResult(
                domain_id="wizard",
                confidence=_t25_fast_prefetch.confidence,
                source="wizard_guard",
                matched_pattern=_t25_fast_prefetch.matched_pattern,
            )
            self._cache_store(cache_key, _t25_result)
            if _redis_cache_enabled:
                try:
                    await self._redis_cache.set(
                        _company_id_for_cache,
                        message,
                        {
                            "domain_id": "wizard",
                            "confidence": _t25_fast_prefetch.confidence,
                            "matched_pattern": _t25_fast_prefetch.matched_pattern,
                        },
                    )
                except Exception:
                    pass
            logger.debug(
                "CascadedRouter: [T2.5 wizard_guard] '%s...' → wizard (conf=%.2f)",
                message[:40],
                _t25_fast_prefetch.confidence,
            )
            return _t25_result

        # Tier 3 — VectorSemanticCache (pgvector, cosine similarity)
        if self._vector_cache is not None:
            async with _tracer.start_span("router.tier3_vector_cache", attributes={
                "tier_name": "tier3_vector_cache", "service": "cascaded_router", "match_type": "cosine_similarity",
            }) as _t3_span:
                try:
                    _t0 = time.perf_counter()
                    vector_hit = await self._vector_cache.get(
                        message,
                        company_id=(_company_id_for_cache if _company_id_for_cache != "__unknown__" else None),
                    )
                    if vector_hit:
                        _elapsed_ms = (time.perf_counter() - _t0) * 1000
                        self._stats["vector_hits"] += 1
                        _confidence = vector_hit.get("confidence", 0.7)
                        if _hit_counter:
                            _hit_counter.labels(tier="vector").inc()
                        if _latency_hist:
                            _latency_hist.labels(tier="vector").observe(_elapsed_ms)
                        if _conf_hist:
                            _conf_hist.labels(model="vector").observe(_confidence)
                        _t3_span.set_attribute("hit", "true")
                        _t3_span.set_attribute("confidence_score", str(_confidence))
                        _t3_span.set_attribute("domain_id", vector_hit.get("domain_id", ""))
                        _t3_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")
                        logger.debug(
                            "CascadedRouter: vector hit for '%s...' → %s (sim >= %.2f)",
                            message[:40],
                            vector_hit.get("domain_id"),
                            self._vector_cache.threshold,
                        )
                        result = RouteResult(
                            domain_id=vector_hit.get("domain_id", "recruiter_assistant"),
                            confidence=_confidence,
                            source="vector_cache",
                            cached=True,
                        )
                        self._cache_store(cache_key, result)
                        return result
                    _t3_span.set_attribute("hit", "false")
                    _t3_span.set_attribute("confidence_score", "0.0")
                    _t3_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")
                except Exception as _vec_exc:
                    _t3_span.set_attribute("hit", "false")
                    _t3_span.set_attribute("confidence_score", "0.0")
                    _t3_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")
                    _t3_span.set_attribute("error_detail", str(_vec_exc))
                    logger.debug("CascadedRouter: vector cache skipped: %s", _vec_exc)

        _partial_candidates: list[dict] = []

        # Tier 4 — FastRouter (regex/keyword)
        async with _tracer.start_span("router.tier4_fast_router", attributes={
            "tier_name": "tier4_fast_router", "service": "cascaded_router", "match_type": "regex_keyword",
        }) as _t4_span:
            _t0 = time.perf_counter()
            fast_result = self.fast.match(message)
            if fast_result and fast_result.confidence >= settings.ROUTER_FAST_CONFIDENCE_THRESHOLD:
                _elapsed_ms = (time.perf_counter() - _t0) * 1000
                self._stats["fast_hits"] += 1
                if _hit_counter:
                    _hit_counter.labels(tier="fast_router").inc()
                if _latency_hist:
                    _latency_hist.labels(tier="fast_router").observe(_elapsed_ms)
                if _conf_hist:
                    _conf_hist.labels(model="fast_router").observe(fast_result.confidence)
                result = RouteResult(
                    domain_id=fast_result.domain_id,
                    confidence=fast_result.confidence,
                    source="fast_router",
                    matched_pattern=fast_result.matched_pattern,
                )
                result = await self._apply_adaptive_adjustments(result, (context or {}).get("company_id"))
                _t4_span.set_attribute("hit", "true")
                _t4_span.set_attribute("confidence_score", str(result.confidence))
                _t4_span.set_attribute("domain_id", result.domain_id)
                _t4_span.set_attribute("matched_pattern", result.matched_pattern or "")
                _t4_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")
                self._cache_store(cache_key, result)
                if _redis_cache_enabled:
                    await self._redis_cache.set(
                        _company_id_for_cache,
                        message,
                        {
                            "domain_id": result.domain_id,
                            "confidence": result.confidence,
                            "matched_pattern": result.matched_pattern,
                        },
                    )
                if self._vector_cache is not None:
                    try:
                        await self._vector_cache.set(
                            message,
                            {"domain_id": result.domain_id, "confidence": result.confidence, "source": result.source},
                            company_id=(_company_id_for_cache if _company_id_for_cache != "__unknown__" else None),
                        )
                    except Exception:
                        pass
                logger.debug("CascadedRouter: fast match for '%s...' → %s", message[:40], result.domain_id)
                return result
            if fast_result and fast_result.confidence > 0:
                _partial_candidates.append({"domain_id": fast_result.domain_id, "confidence": fast_result.confidence})
            _t4_span.set_attribute("hit", "false")
            _t4_span.set_attribute("confidence_score", "0.0")
            _t4_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")

        # Tier 5 — LLM Cascade (Haiku → Sonnet → Opus)
        # A/B testing: select system prompt variant based on user_id hash
        _ab_variant_id: str | None = None
        _ab_prompt_hash: str | None = None
        try:
            from app.shared.prompt_experiment import get_experiment
            _exp = get_experiment(AB_EXPERIMENT_ID)
            if _exp:
                _user_id_ab = (context or {}).get("user_id") or session_id or "anonymous"
                _selected_variant = _exp.select_variant(_user_id_ab)
                _ab_variant_id = _selected_variant.variant_id
                _ab_prompt_hash = hashlib.sha256(_selected_variant.prompt_text.encode("utf-8")).hexdigest()[:12]
                logger.debug(
                    "[A/B] CascadeRouter user=%s → variant=%s hash=%s",
                    _user_id_ab, _ab_variant_id, _ab_prompt_hash,
                )
        except Exception as _ab_exc:
            logger.debug("[A/B] CascadeRouter variant selection skipped: %s", _ab_exc)

        # Threshold: only accept Tier 5 result when confidence is sufficient;
        # low-confidence Tier 5 falls through to Tier 7 (Studio Agent) then clarification — Tier 6 removed Sprint 12.3-B.
        import os as _os_t5
        _TIER5_MIN_CONFIDENCE = float(_os_t5.getenv("ROUTER_LLM_CASCADE_MIN_CONFIDENCE", "0.5"))
        async with _tracer.start_span("router.tier5_llm_cascade", attributes={
            "tier_name": "tier5_llm_cascade", "service": "cascaded_router", "match_type": "llm",
        }) as _t5_span:
            try:
                company_id = (context or {}).get("company_id")
                _t0 = time.perf_counter()
                cascade_result = await self._route_via_llm_cascade(message, context, company_id, ab_variant_id=_ab_variant_id)
                if cascade_result:
                    _elapsed_ms = (time.perf_counter() - _t0) * 1000
                    _tier_name = cascade_result.source.split(":")[-1] if ":" in cascade_result.source else "llm_cascade"
                    cascade_result = await self._apply_adaptive_adjustments(
                        cascade_result, (context or {}).get("company_id")
                    )
                    _t5_span.set_attribute("confidence_score", str(cascade_result.confidence))
                    _t5_span.set_attribute("domain_id", cascade_result.domain_id)
                    _t5_span.set_attribute("model_tier", _tier_name)
                    _t5_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")
                    if cascade_result.confidence < _TIER5_MIN_CONFIDENCE:
                        _partial_candidates.append({"domain_id": cascade_result.domain_id, "confidence": cascade_result.confidence})
                        _t5_span.set_attribute("hit", "false")
                        _t5_span.set_attribute("below_threshold", "true")
                        logger.info(
                            "CascadedRouter: Tier 5 confidence %.2f < %.2f for '%s...' — falling to Tier 7 (Tier 6 removed Sprint 12.3-B)",
                            cascade_result.confidence, _TIER5_MIN_CONFIDENCE, message[:40],
                        )
                    else:
                        _t5_span.set_attribute("hit", "true")
                        self._cache_store(cache_key, cascade_result)
                        if _redis_cache_enabled:
                            await self._redis_cache.set(
                                _company_id_for_cache,
                                message,
                                {"domain_id": cascade_result.domain_id, "confidence": cascade_result.confidence},
                            )
                        if self._vector_cache is not None:
                            try:
                                await self._vector_cache.set(
                                    message,
                                    company_id=(_company_id_for_cache if _company_id_for_cache != "__unknown__" else None),
                                    result={
                                        "domain_id": cascade_result.domain_id,
                                        "confidence": cascade_result.confidence,
                                        "source": cascade_result.source,
                                    },
                                )
                            except Exception as exc:
                                logger.debug(
                                    "[cascaded_router] vector_cache.set failed: %s", exc, exc_info=True,
                                )
                        if _ab_variant_id:
                            if cascade_result.intent_details is None:
                                cascade_result.intent_details = OrchestratorIntentResult(
                                    intent_id="unknown",
                                    confidence=cascade_result.confidence,
                                    source="llm",
                                )
                            cascade_result.intent_details.ab_variant = _ab_variant_id
                            cascade_result.intent_details.ab_prompt_hash = _ab_prompt_hash
                            _t5_span.set_attribute("ab_variant", _ab_variant_id)
                        self._stats["llm_hits"] += 1
                        if _hit_counter:
                            _hit_counter.labels(tier="llm_cascade").inc()
                        if _latency_hist:
                            _latency_hist.labels(tier="llm_cascade").observe(_elapsed_ms)
                        if _conf_hist:
                            _conf_hist.labels(model=_tier_name).observe(cascade_result.confidence)
                        logger.debug("CascadedRouter: LLM cascade for '%s...' → %s", message[:40], cascade_result.domain_id)
                        return cascade_result
                else:
                    _t5_span.set_attribute("hit", "false")
                    _t5_span.set_attribute("confidence_score", "0.0")
                    _t5_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")
            except Exception as e:
                _t5_span.set_attribute("hit", "false")
                _t5_span.set_attribute("confidence_score", "0.0")
                _t5_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")
                _t5_span.set_attribute("error_detail", str(e))
                logger.error("CascadedRouter: LLM cascade failed: %s", e)

        # Tier 6 — REMOVED in Sprint 12.3-B (2026-05-24).
        # Histórico: Tier 6 invocava AutonomousReActAgent (cross-domain ReAct fallback)
        # via env AUTONOMOUS_REACT_ENABLED + flag per-tenant tier6_canary_enabled.
        # Em prod env nunca foi SET (default false) -- Tier 6 invocations = 0 nos canary metrics.
        # Decisão: estrutura removida do hot path (low-risk, env-gated already-off).
        # autonomous_react_agent.py e test files removidos em T13 (Sprint 12.6).
        # Refs: PHASE_2_V1_ARCHITECTURE_AUDIT.md (decisão Batch 1), W4-041 (canary doc).

        # Tier 7 — Studio Agent Matcher (custom agents bound to current context)
        _ctx = context or {}
        _ctx_job_id = _ctx.get("job_id") or _ctx.get("vacancy_id")
        _ctx_pool_id = _ctx.get("talent_pool_id")
        _ctx_company_id = _ctx.get("company_id")

        # Tier 7 dual-mode (Fase C.2 2026-06-09):
        #   Federated mode (LIA_FEDERATED_PRIMARY=true): emit ScopeHint for first-party
        #     agents and tenant deployments alike. The scope resolver already augmented
        #     the federated agent tool set via studio_scope_extension; no runtime fork.
        #   Legacy mode: instantiate CustomAgentRuntime directly (unchanged behavior).
        if (_ctx_job_id or _ctx_pool_id) and _ctx_company_id:
            async with _tracer.start_span("router.tier7_studio_agent", attributes={
                "tier_name": "tier7_studio_agent", "service": "cascaded_router",
                "match_type": "studio_deployment",
            }) as _t7_span:
                try:
                    _t0 = time.perf_counter()
                    from app.tools.scope_config import federated_primary_enabled as _fed_enabled
                    _is_federated_mode = _fed_enabled()

                    # --- Federated fast path: domain-based first-party/deployment check ---
                    if _is_federated_mode:
                        _classified_domain = (context or {}).get("classified_domain") or ""
                        if _classified_domain:
                            from app.orchestrator.studio_scope_extension import get_studio_covered_domains
                            if _classified_domain in get_studio_covered_domains():
                                from app.orchestrator.routing.scope_hint import ScopeHint
                                from app.domains.agent_studio.repositories.custom_agent_repository import (
                                    CustomAgentRepository,
                                )
                                from lia_config.database import AsyncSessionLocal
                                async with AsyncSessionLocal() as _hint_db:
                                    _agent_repo = CustomAgentRepository(_hint_db)
                                    _fp_agents = await _agent_repo.list_active_for_context(
                                        company_id=_ctx_company_id,
                                        domain=_classified_domain,
                                        include_first_party=True,
                                    )
                                if _fp_agents:
                                    _matched = _fp_agents[0]
                                    _is_fp = (
                                        getattr(getattr(_matched, "agent_type", None), "value", "")
                                        == "first_party"
                                    )
                                    _scope_hint = ScopeHint(
                                        domain=_classified_domain,
                                        source="studio_first_party" if _is_fp else "studio_deployment",
                                        tools=list(_matched.allowed_tools or []),
                                    )
                                    _elapsed_ms = (time.perf_counter() - _t0) * 1000
                                    self._stats["studio_agent_hits"] += 1
                                    _t7_span.set_attribute("hit", "true")
                                    _t7_span.set_attribute("mode", "federated_scope_hint")
                                    _t7_span.set_attribute("domain", _classified_domain)
                                    _t7_span.set_attribute("agent_id", str(getattr(_matched, "id", "")))
                                    _t7_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")
                                    logger.info(
                                        "CascadedRouter: Tier 7 (federated) ScopeHint domain=%s"
                                        " agent=%s in %.0fms",
                                        _classified_domain,
                                        getattr(_matched, "name", ""),
                                        _elapsed_ms,
                                    )
                                    # ScopeHint is NOT a RouteResult; callers check isinstance.
                                    # The federated agent continues with augmented scope.
                                    return _scope_hint

                    # --- Legacy / deployment-based path (also handles federated fallback) ---
                    from app.services.agent_deployment_service import agent_deployment_service
                    from lia_config.database import AsyncSessionLocal

                    _studio_deployments = []
                    async with AsyncSessionLocal() as _studio_db:
                        if _ctx_job_id:
                            _studio_deployments = await agent_deployment_service.find_active_deployments_for_trigger(
                                db=_studio_db,
                                company_id=_ctx_company_id,
                                target_type="job",
                                target_id=_ctx_job_id,
                                trigger_mode="manual",
                            )
                        if not _studio_deployments and _ctx_pool_id:
                            _studio_deployments = await agent_deployment_service.find_active_deployments_for_trigger(
                                db=_studio_db,
                                company_id=_ctx_company_id,
                                target_type="talent_pool",
                                target_id=_ctx_pool_id,
                                trigger_mode="manual",
                            )

                        if _studio_deployments:
                            _dep = _studio_deployments[0]
                            from sqlalchemy import select
                            from lia_models.custom_agent import CustomAgent
                            _agent_result = await _studio_db.execute(
                                select(CustomAgent).where(CustomAgent.id == _dep.agent_id)
                            )
                            _studio_agent = _agent_result.scalar_one_or_none()

                            if _studio_agent and _studio_agent.status == "active":
                                if _is_federated_mode:
                                    # Federated + deployment: emit ScopeHint, skip runtime fork.
                                    from app.orchestrator.routing.scope_hint import ScopeHint
                                    _dep_domains = list(_studio_agent.domains or [])
                                    _dep_domain = _dep_domains[0] if _dep_domains else "general"
                                    _dep_hint = ScopeHint(
                                        domain=_dep_domain,
                                        source="studio_deployment",
                                        tools=list(_studio_agent.allowed_tools or []),
                                    )
                                    _elapsed_ms = (time.perf_counter() - _t0) * 1000
                                    self._stats["studio_agent_hits"] += 1
                                    await agent_deployment_service.record_execution(
                                        _studio_db, str(_dep.id)
                                    )
                                    await _studio_db.commit()
                                    _t7_span.set_attribute("hit", "true")
                                    _t7_span.set_attribute("mode", "federated_scope_hint_deployment")
                                    _t7_span.set_attribute("agent_id", str(_studio_agent.id))
                                    _t7_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")
                                    logger.info(
                                        "CascadedRouter: Tier 7 (federated dep) ScopeHint agent=%s"
                                        " in %.0fms",
                                        _studio_agent.name,
                                        _elapsed_ms,
                                    )
                                    return _dep_hint

                                # Legacy mode: instantiate CustomAgentRuntime directly.
                                from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

                                _runtime = get_or_create_runtime(
                                    agent_id=str(_studio_agent.id),
                                    agent_name=_studio_agent.name,
                                    system_prompt=_studio_agent.system_prompt,
                                    allowed_tools=_studio_agent.allowed_tools or [],
                                    domain=_studio_agent.domain or "general",
                                    max_steps=_studio_agent.max_steps or 8,
                                    temperature=_studio_agent.temperature or 0.7,
                                    model_override=_studio_agent.model_override,
                                    company_id=_ctx_company_id,
                                    enable_memory=getattr(_studio_agent, "enable_memory", True),
                                    excluded_tools=getattr(_studio_agent, "excluded_tools", None),
                                    context_level=getattr(_studio_agent, "context_level", "full"),
                                )

                                _output = await _runtime.execute(
                                    message=message,
                                    user_id=_ctx.get("user_id", ""),
                                    company_id=_ctx_company_id,
                                    session_id=session_id or "",
                                    context=_ctx,
                                )

                                _elapsed_ms = (time.perf_counter() - _t0) * 1000
                                self._stats["studio_agent_hits"] += 1

                                # Record deployment execution
                                await agent_deployment_service.record_execution(
                                    _studio_db, str(_dep.id)
                                )
                                await _studio_db.commit()

                                _t7_span.set_attribute("hit", "true")
                                _t7_span.set_attribute("confidence_score", "0.70")
                                _t7_span.set_attribute("domain_id", f"custom:{_studio_agent.name}")
                                _t7_span.set_attribute("agent_id", str(_studio_agent.id))
                                _t7_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")

                                logger.info(
                                    "CascadedRouter: Tier 7 (legacy) resolved '%s...' via agent=%s"
                                    " in %.0fms",
                                    message[:40],
                                    _studio_agent.name,
                                    _elapsed_ms,
                                )

                                _studio_result = RouteResult(
                                    domain_id=f"custom:{_studio_agent.name}",
                                    confidence=0.70,
                                    source="studio_agent",
                                    intent_details=OrchestratorIntentResult(
                                        intent_id=f"studio:{_studio_agent.name}",
                                        confidence=0.70,
                                        source="studio_agent",
                                        routing_metadata={
                                            "agent_id": str(_studio_agent.id),
                                            "agent_name": _studio_agent.name,
                                            "deployment_id": str(_dep.id),
                                            "response": _output.message,
                                        },
                                    ),
                                )
                                return _studio_result

                    _t7_span.set_attribute("hit", "false")
                    _t7_span.set_attribute("confidence_score", "0.0")
                    _t7_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")
                except Exception as _studio_exc:
                    _t7_span.set_attribute("hit", "false")
                    _t7_span.set_attribute("error_detail", str(_studio_exc))
                    logger.warning("CascadedRouter: Tier 7 (studio) failed: %s", _studio_exc)
        # Fallback final — clarification_needed (Gap #2)
        async with _tracer.start_span("router.fallback_clarification", attributes={
            "tier_name": "fallback_clarification", "service": "cascaded_router", "match_type": "clarification",
        }) as _fb_span:
            logger.warning("CascadedRouter: nenhum tier resolveu '%s...', emitindo clarificação", message[:60])
            self._stats["clarification_issued"] += 1
            if _hit_counter:
                _hit_counter.labels(tier="clarification_needed").inc()
            _fb_span.set_attribute("confidence_score", "0.0")
            _user_name = context.get("user_name", "") if context else ""
            _clar_question, _clar_options = _build_clarification_question(
                message,
                partial_matches=_partial_candidates if _partial_candidates else None,
                user_name=_user_name,
            )
            return RouteResult(
                domain_id="recruiter_assistant",
                confidence=0.0,
                source="clarification_needed",
                needs_clarification=True,
                clarification_question=_clar_question,
                clarification_options=_clar_options,
            )

    async def _apply_adaptive_adjustments(
        self, route_result: "RouteResult", company_id: str | None
    ) -> "RouteResult":
        """Apply adaptive routing confidence adjustments from learning history.

        E9 — CascadedRouter Aprende: adjusts confidence based on correction signals
        stored in RoutingFeedback. Uses Redis-cached adjustments (computed by
        routing.recompute_adjustments Celery task daily at 07h UTC).

        Fail-open: any error returns the original route_result unchanged.
        """
        import os
        if os.getenv("USE_ADAPTIVE_ROUTING", "true").lower() != "true":
            return route_result
        try:
            from app.shared.services.routing_learning_service import routing_learning_service
            cid = company_id or 'global'
            adjustments = await routing_learning_service.get_cached_adjustments(cid)
            if route_result.domain_id in adjustments:
                factor = adjustments[route_result.domain_id]
                original_conf = route_result.confidence
                route_result.confidence = round(original_conf * factor, 4)
                logger.debug(
                    "[CascadedRouter][E9] adaptive adjustment domain=%s factor=%.3f conf %.4f→%.4f",
                    route_result.domain_id, factor, original_conf, route_result.confidence,
                )
        except Exception as exc:
            logger.debug(
                "[cascaded_router][E9] adaptive_confidence lookup failed: %s", exc, exc_info=True,
            )
        return route_result

    # _route_via_autonomous_agent — REMOVED in Sprint 12.3-B (2026-05-24).
    # Helper invocava AutonomousReActAgent via Tier 6 (removido em T13).
    # Tier 6 removido (env never set in prod). Helper era dead code.
    # imports — cleanup completo em Sprint 12.6.

    async def _route_via_llm_cascade(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        company_id: str | None = None,
        ab_variant_id: str | None = None,
    ) -> RouteResult | None:
        """Usa LLMCascadeRouter (Haiku→Sonnet→Opus) para roteamento de intent.

        When an A/B variant is active, injects the selected prompt variant into
        the cascade router call so that different users see different system prompts.
        """
        try:
            from app.orchestrator.routing.llm_cascade import llm_cascade_router

            ab_system_prompt: str | None = None
            if ab_variant_id:
                try:
                    from app.shared.prompt_experiment import get_experiment
                    _exp = get_experiment(AB_EXPERIMENT_ID)
                    if _exp:
                        for v in _exp.variants:
                            if v.variant_id == ab_variant_id:
                                ab_system_prompt = v.prompt_text
                                break
                except Exception as exc:
                    logger.debug(
                        "[cascaded_router] A/B variant prompt lookup failed: %s", exc, exc_info=True,
                    )

            if ab_system_prompt:
                result = await llm_cascade_router.route(
                    message, context, company_id,
                    system_prompt_override=ab_system_prompt,
                )
            else:
                result = await llm_cascade_router.route(message, context, company_id)

            domain_id = result.get("domain", "recruiter_assistant")
            confidence = result.get("confidence", 0.5)
            return RouteResult(
                domain_id=domain_id,
                confidence=confidence,
                source=f"llm_cascade:{result.get('tier', 'unknown')}",
                intent_details=OrchestratorIntentResult(
                    intent_id=result.get("domain", "unknown"),
                    confidence=confidence,
                    source="llm",
                    routing_metadata={
                        "model_used": result.get("model_used"),
                        "tier": result.get("tier"),
                        "tokens_est": result.get("tokens_est"),
                        "reason": result.get("reason"),
                    },
                ),
            )
        except Exception as exc:
            logger.debug("[CascadedRouter] llm_cascade falhou: %s", exc)
            return None

    def _intent_to_domain(self, intent: str) -> str:
        return resolve_domain(intent)

    def _cache_store(self, key: str, result: RouteResult) -> None:
        if len(self._memory_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
        self._memory_cache[key] = result

    def clear_cache(self) -> None:
        self._memory_cache.clear()
        logger.info("CascadedRouter cache cleared")

    def get_stats(self) -> dict[str, Any]:
        total = self._stats["total"] or 1
        return {
            **self._stats,
            "cache_size": len(self._memory_cache),
            "memory_hit_rate": self._stats["memory_hits"] / total,
            "redis_hit_rate": self._stats["redis_hits"] / total,
            "vector_hit_rate": self._stats["vector_hits"] / total,
            "fast_hit_rate": self._stats["fast_hits"] / total,
            "llm_hit_rate": self._stats["llm_hits"] / total,
            "autonomous_hit_rate": self._stats["autonomous_hits"] / total,
            "clarification_rate": self._stats["clarification_issued"] / total,
        }

    def __repr__(self) -> str:
        return f"<CascadedRouter cache_size={len(self._memory_cache)} stats={self._stats}>"


_ROUTER_SINGLETON: "CascadedRouter | None" = None


def get_router() -> "CascadedRouter":
    """Returns the process-level singleton CascadedRouter.

    Keeps the in-process LRU cache alive across SSE turns so Tier-1 hits
    work in practice (previously a new CascadedRouter() per request made
    the LRU useless). Thread-safety: CPython GIL covers dict reads/writes;
    async workers share one event loop per process so no concurrent mutation.
    """
    global _ROUTER_SINGLETON
    if _ROUTER_SINGLETON is None:
        _ROUTER_SINGLETON = CascadedRouter()
    return _ROUTER_SINGLETON
