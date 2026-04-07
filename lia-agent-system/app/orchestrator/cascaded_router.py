"""
Cascaded Router - 7-tier routing: memory → redis → vector → fast → LLM → autonomous → clarification.

Hierarquia de resolução (custo crescente):
  Tier 0: MemoryResolver       — pronomes/referências de contexto
  Tier 1: LRU in-process       — hash MD5 em memória local (O(1))
  Tier 2: Redis hash cache      — distribuído, exato, compartilhado entre workers
  Tier 3: VectorSemanticCache   — pgvector, cosine similarity >= 0.85
  Tier 4: FastRouter            — regex/keyword (O(n) patterns)
  Tier 5: LLM Cascade           — Haiku→Sonnet→Opus (caro)
  Tier 6: AutonomousReActAgent  — agente cross-domain, fallback final antes de clarification
  Fallback: clarification_needed — pergunta ao usuário quando tudo falha

Coexiste com IntentRouter legado — usa como fallback do Tier 5 quando disponível.
"""
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.orchestrator.fast_router import FastRouter
from app.orchestrator.semantic_cache import SemanticCache
from app.shared.tracing import trace_span

logger = logging.getLogger(__name__)


def _get_metrics():
    """Metrics stub — Prometheus removed (Task #138). Returns None."""
    try:
        return None, None, None
    except Exception:
        return None, None, None


@dataclass
class RouteResult:
    domain_id: str
    confidence: float
    source: str
    matched_pattern: str | None = None
    intent_details: dict[str, Any] | None = None
    cached: bool = False
    resolved_at: datetime = field(default_factory=datetime.utcnow)
    # Campos de clarificação (Fase 2 — Gap #2)
    needs_clarification: bool = False
    clarification_question: str | None = None
    clarification_options: list[str] | None = None


AGENT_TYPE_TO_DOMAIN: dict[str, str] = {
    "job_planner": "job_management",
    "job_intake": "job_management",
    "sourcing": "sourcing",
    "cv_screening": "cv_screening",
    "screening": "cv_screening",
    "wsi_evaluator": "cv_screening",
    "interviewer": "interview_scheduling",
    "scheduling": "interview_scheduling",
    "analyst_feedback": "analytics",
    "analytics": "analytics",
    "communication": "communication",
    "ats_integrator": "ats_integration",
    "recruiter_assistant": "recruiter_assistant",
    "task_planner": "automation",
    # Z1-01: Kanban subagents
    "kanban_search": "kanban_search",
    "kanban_insight": "kanban_insight",
    "kanban_action": "kanban_action",
    # Z1-02: Pipeline subagents
    "pipeline_context": "pipeline_context",
    "pipeline_decision": "pipeline_decision",
    "pipeline_action": "pipeline_action",
    # Z2-02: Sourcing subagents
    "sourcing_planner": "sourcing_planner",
    "sourcing_search": "sourcing_search",
    "sourcing_enrich": "sourcing_enrich",
    "sourcing_engagement": "sourcing_engagement",
}

# Opções padrão de clarificação quando o router não sabe o domínio
_DEFAULT_CLARIFICATION_OPTIONS = [
    "Criar ou gerenciar uma vaga",
    "Buscar ou avaliar candidatos",
    "Acompanhar pipeline / triagem",
    "Agendar entrevistas",
    "Relatórios e analytics",
    "Outra solicitação",
]


def _build_clarification_question(message: str) -> str:
    """Gera uma pergunta de clarificação baseada na mensagem do usuário."""
    snippet = message.strip()[:80]
    if snippet:
        return (
            f"Não consegui identificar o que você precisa com '{snippet}'. "
            "O que você gostaria de fazer?"
        )
    return "Não entendi sua solicitação. O que você gostaria de fazer?"


class CascadedRouter:
    def __init__(
        self,
        fast_router: FastRouter | None = None,
        intent_router: Any | None = None,
        domain_registry: Any | None = None,
        cache_max_size: int = settings.ROUTER_CACHE_MAX_SIZE,
    ):
        self.fast = fast_router or FastRouter()
        self.llm_fallback = intent_router
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
            "clarification_issued": 0,
            "total": 0,
        }

    def _init_vector_cache(self):
        """Inicializa VectorSemanticCache (gracioso — nunca falha na init).

        Z5-03: respeita ROUTER_VECTOR_CACHE_ENABLED para A/B testing.
        Threshold injetado via settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD.
        """
        try:
            if not settings.ROUTER_VECTOR_CACHE_ENABLED:
                logger.debug("[CascadedRouter] Tier 3 (vector cache) desabilitado via ROUTER_VECTOR_CACHE_ENABLED=false")
                return None
            from app.orchestrator.vector_semantic_cache import VectorSemanticCache
            return VectorSemanticCache(
                similarity_threshold=settings.ROUTER_VECTOR_SIMILARITY_THRESHOLD,
            )
        except Exception as exc:
            logger.debug("[CascadedRouter] VectorSemanticCache não disponível: %s", exc)
            return None

    def _cache_key(self, message: str) -> str:
        normalized = message.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    @trace_span("router.route", attributes={"component": "cascaded_router"})
    async def route(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> RouteResult:
        self._stats["total"] += 1
        _hit_counter, _latency_hist, _conf_hist = _get_metrics()

        # Tier 0 — Resolver pronomes/referências via WorkingMemory antes de rotear
        if session_id:
            try:
                from app.orchestrator.memory_resolver import memory_resolver
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
            except Exception as _mem_exc:
                logger.debug("CascadedRouter: memory resolver skipped: %s", _mem_exc)

        cache_key = self._cache_key(message)

        # Tier 1 — LRU in-process (hash MD5, O(1))
        _t0 = time.perf_counter()
        cached = self._memory_cache.get(cache_key)
        if cached:
            _elapsed_ms = (time.perf_counter() - _t0) * 1000
            self._stats["memory_hits"] += 1
            if _hit_counter:
                _hit_counter.labels(tier="memory").inc()
            if _latency_hist:
                _latency_hist.labels(tier="memory").observe(_elapsed_ms)
            logger.debug("CascadedRouter: memory hit for '%s...' → %s", message[:40], cached.domain_id)
            return RouteResult(
                domain_id=cached.domain_id,
                confidence=cached.confidence,
                source="memory",
                matched_pattern=cached.matched_pattern,
                cached=True,
            )

        # Tier 2 — Redis hash cache (distribuído, exato)
        _t0 = time.perf_counter()
        redis_hit = await self._redis_cache.get(message)
        if redis_hit:
            _elapsed_ms = (time.perf_counter() - _t0) * 1000
            self._stats["redis_hits"] += 1
            if _hit_counter:
                _hit_counter.labels(tier="redis_hash").inc()
            if _latency_hist:
                _latency_hist.labels(tier="redis_hash").observe(_elapsed_ms)
            logger.debug("CascadedRouter: redis hit for '%s...' → %s", message[:40], redis_hit.get("domain_id"))
            return RouteResult(
                domain_id=redis_hit.get("domain_id", "recruiter_assistant"),
                confidence=redis_hit.get("confidence", 0.7),
                source="redis_cache",
                matched_pattern=redis_hit.get("matched_pattern"),
                cached=True,
            )

        # Tier 3 — VectorSemanticCache (pgvector, cosine similarity)
        if self._vector_cache is not None:
            try:
                _t0 = time.perf_counter()
                vector_hit = await self._vector_cache.get(message)
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
            except Exception as _vec_exc:
                logger.debug("CascadedRouter: vector cache skipped: %s", _vec_exc)

        # Tier 4 — FastRouter (regex/keyword)
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
            # E9 — apply adaptive confidence adjustments before caching
            result = await self._apply_adaptive_adjustments(result, (context or {}).get("company_id"))
            self._cache_store(cache_key, result)
            await self._redis_cache.set(
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
                    )
                except Exception:
                    pass
            logger.debug("CascadedRouter: fast match for '%s...' → %s", message[:40], result.domain_id)
            return result

        # Tier 5 — LLM Cascade (Haiku → Sonnet → Opus)
        # Threshold: only accept Tier 5 result when confidence is sufficient;
        # low-confidence Tier 5 falls through to Tier 6 (AutonomousReActAgent).
        import os as _os_t5
        _TIER5_MIN_CONFIDENCE = float(_os_t5.getenv("ROUTER_LLM_CASCADE_MIN_CONFIDENCE", "0.5"))
        try:
            company_id = (context or {}).get("company_id")
            _t0 = time.perf_counter()
            cascade_result = await self._route_via_llm_cascade(message, context, company_id)
            if cascade_result:
                _elapsed_ms = (time.perf_counter() - _t0) * 1000
                # Determinar modelo usado a partir da source ("llm_cascade:haiku", etc.)
                _tier_name = cascade_result.source.split(":")[-1] if ":" in cascade_result.source else "llm_cascade"
                # E9 — apply adaptive confidence adjustments before caching
                cascade_result = await self._apply_adaptive_adjustments(
                    cascade_result, (context or {}).get("company_id")
                )
                if cascade_result.confidence < _TIER5_MIN_CONFIDENCE:
                    logger.info(
                        "CascadedRouter: Tier 5 confidence %.2f < %.2f for '%s...' — falling to Tier 6",
                        cascade_result.confidence, _TIER5_MIN_CONFIDENCE, message[:40],
                    )
                else:
                    self._cache_store(cache_key, cascade_result)
                    await self._redis_cache.set(
                        message,
                        {"domain_id": cascade_result.domain_id, "confidence": cascade_result.confidence},
                    )
                    if self._vector_cache is not None:
                        try:
                            await self._vector_cache.set(
                                message,
                                {
                                    "domain_id": cascade_result.domain_id,
                                    "confidence": cascade_result.confidence,
                                    "source": cascade_result.source,
                                },
                            )
                        except Exception:
                            pass
                    self._stats["llm_hits"] += 1
                    if _hit_counter:
                        _hit_counter.labels(tier="llm_cascade").inc()
                    if _latency_hist:
                        _latency_hist.labels(tier="llm_cascade").observe(_elapsed_ms)
                    if _conf_hist:
                        _conf_hist.labels(model=_tier_name).observe(cascade_result.confidence)
                    logger.debug("CascadedRouter: LLM cascade for '%s...' → %s", message[:40], cascade_result.domain_id)
                    return cascade_result
        except Exception as e:
            logger.error("CascadedRouter: LLM cascade failed: %s", e)

        # LLM fallback legado (IntentRouter) se cascade não disponível
        # Apply the same confidence threshold as Tier 5 — low-confidence results fall to Tier 6.
        if self.llm_fallback:
            try:
                _t0 = time.perf_counter()
                intent_result = await self._route_via_llm(message, context)
                if intent_result:
                    _elapsed_ms = (time.perf_counter() - _t0) * 1000
                    if intent_result.confidence < _TIER5_MIN_CONFIDENCE:
                        logger.info(
                            "CascadedRouter: legacy LLM fallback confidence %.2f < %.2f for '%s...' — falling to Tier 6",
                            intent_result.confidence, _TIER5_MIN_CONFIDENCE, message[:40],
                        )
                    else:
                        self._cache_store(cache_key, intent_result)
                        self._stats["llm_hits"] += 1
                        if _hit_counter:
                            _hit_counter.labels(tier="llm_cascade").inc()
                        if _latency_hist:
                            _latency_hist.labels(tier="llm_cascade").observe(_elapsed_ms)
                        if _conf_hist:
                            _conf_hist.labels(model="llm_fallback").observe(intent_result.confidence)
                        logger.debug("CascadedRouter: LLM fallback for '%s...' → %s", message[:40], intent_result.domain_id)
                        return intent_result
            except Exception as e:
                logger.error("CascadedRouter: LLM fallback failed: %s", e)

        # Tier 6 — AutonomousReActAgent (cross-domain fallback antes de clarification)
        import os as _os
        if _os.getenv("AUTONOMOUS_REACT_ENABLED", "true").lower() == "true":
            try:
                _t0 = time.perf_counter()
                autonomous_result = await self._route_via_autonomous_agent(message, context, session_id)
                if autonomous_result:
                    _elapsed_ms = (time.perf_counter() - _t0) * 1000
                    self._stats["autonomous_hits"] += 1
                    if _hit_counter:
                        _hit_counter.labels(tier="autonomous_react").inc()
                    if _latency_hist:
                        _latency_hist.labels(tier="autonomous_react").observe(_elapsed_ms)
                    if _conf_hist:
                        _conf_hist.labels(model="autonomous_react").observe(autonomous_result.confidence)
                    logger.info(
                        "CascadedRouter: Tier 6 (autonomous) resolved '%s...' in %.0fms",
                        message[:40], _elapsed_ms,
                    )
                    return autonomous_result
            except Exception as _auto_exc:
                logger.error("CascadedRouter: Tier 6 (autonomous) failed: %s", _auto_exc)

        # Fallback final — clarification_needed (Gap #2)
        # Não retorna silenciosamente recruiter_assistant: pergunta ao usuário.
        logger.warning("CascadedRouter: nenhum tier resolveu '%s...', emitindo clarificação", message[:60])
        self._stats["clarification_issued"] += 1
        if _hit_counter:
            _hit_counter.labels(tier="clarification_needed").inc()
        return RouteResult(
            domain_id="recruiter_assistant",
            confidence=0.0,
            source="clarification_needed",
            needs_clarification=True,
            clarification_question=_build_clarification_question(message),
            clarification_options=_DEFAULT_CLARIFICATION_OPTIONS,
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
            from app.services.routing_learning_service import routing_learning_service
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
        except Exception:
            pass
        return route_result

    async def _route_via_autonomous_agent(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> RouteResult | None:
        """
        Tier 6: invoca o AutonomousReActAgent para queries cross-domain.

        O agente processa a query e retorna uma resposta completa.
        Quando bem-sucedido, roteia para o domínio 'autonomous' com confiança >= 0.5.
        Budget controlado por AUTONOMOUS_REACT_MAX_STEPS (env var, padrão 10).
        """
        try:
            from app.domains.autonomous.agents.autonomous_react_agent import get_autonomous_react_agent
            from lia_agents_core.agent_interface import AgentInput

            agent = get_autonomous_react_agent()
            agent_input = AgentInput(
                message=message,
                session_id=session_id or "cascaded_router",
                user_id=(context or {}).get("user_id", ""),
                company_id=(context or {}).get("company_id", ""),
                context=context or {},
                conversation_history=(context or {}).get("conversation_history", []),
            )
            output = await agent.process(agent_input)

            if output.confidence >= 0.5:
                return RouteResult(
                    domain_id="autonomous",
                    confidence=output.confidence,
                    source="autonomous_react:tier6",
                    intent_details={
                        "response": output.message,
                        "tool_calls": len(output.actions or []),
                        "tier": 6,
                        "metadata": output.metadata or {},
                    },
                )
            logger.debug(
                "[CascadedRouter][Tier6] Autonomous confidence %.2f < 0.5 — skipping",
                output.confidence,
            )
            return None
        except Exception as exc:
            logger.debug("[CascadedRouter][Tier6] autonomous agent error: %s", exc)
            return None

    async def _route_via_llm_cascade(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        company_id: str | None = None,
    ) -> RouteResult | None:
        """Usa LLMCascadeRouter (Haiku→Sonnet→Opus) para roteamento de intent."""
        try:
            from app.orchestrator.llm_cascade import llm_cascade_router
            result = await llm_cascade_router.route(message, context, company_id)
            domain_id = result.get("domain", "recruiter_assistant")
            confidence = result.get("confidence", 0.5)
            return RouteResult(
                domain_id=domain_id,
                confidence=confidence,
                source=f"llm_cascade:{result.get('tier', 'unknown')}",
                intent_details={
                    "model_used": result.get("model_used"),
                    "tier": result.get("tier"),
                    "tokens_est": result.get("tokens_est"),
                    "reason": result.get("reason"),
                },
            )
        except Exception as exc:
            logger.debug("[CascadedRouter] llm_cascade falhou: %s", exc)
            return None

    async def _route_via_llm(self, message: str, context: dict[str, Any] | None = None) -> RouteResult | None:
        if not self.llm_fallback:
            return None

        try:
            # IntentRouter.route() já usa cascade internamente (Haiku→Sonnet→Opus)
            if hasattr(self.llm_fallback, 'route'):
                result = await self.llm_fallback.route(message, context)
            elif hasattr(self.llm_fallback, 'classify_intent'):
                result = await self.llm_fallback.classify_intent(message)
            elif hasattr(self.llm_fallback, 'classify'):
                result = await self.llm_fallback.classify(message)
            else:
                logger.warning("LLM fallback has no compatible classify/route method")
                return None

            if isinstance(result, dict):
                intent = result.get("intent", result.get("agent_type", ""))
                confidence = result.get("confidence", 0.5)
                model_used = result.get("model_used", "unknown")
            elif hasattr(result, 'intent'):
                intent = result.intent
                confidence = getattr(result, 'confidence', 0.5)
                model_used = "unknown"
            else:
                intent = str(result)
                confidence = 0.5
                model_used = "unknown"

            domain_id = self._intent_to_domain(intent)
            return RouteResult(
                domain_id=domain_id,
                confidence=confidence,
                source="llm_fallback",
                intent_details={"raw_intent": intent, "model_used": model_used},
            )
        except Exception as e:
            logger.error("LLM routing failed: %s", e)
            return None

    def _intent_to_domain(self, intent: str) -> str:
        intent_lower = str(intent).lower().strip()

        if intent_lower in AGENT_TYPE_TO_DOMAIN:
            return AGENT_TYPE_TO_DOMAIN[intent_lower]

        for agent_key, domain_id in AGENT_TYPE_TO_DOMAIN.items():
            if agent_key in intent_lower or intent_lower in agent_key:
                return domain_id

        return "recruiter_assistant"

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
