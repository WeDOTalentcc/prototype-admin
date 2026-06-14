"""
EnhancedAgentMixin - Provides memory, autonomy, and learning capabilities to ReAct agents.

All 6 domain agents can use this mixin to:
1. Enrich system prompts with long-term memories before reasoning
2. Resolve dynamic guardrails from CompanyHiringPolicy
3. Extract and save learnings after each ReAct loop execution
4. Automatic FairnessGuard pre-check before processing (P0-A — Inegociável #3)
"""
import logging
from typing import Any, Dict, List, Optional

from lia_agents_core.memory_integration import MemoryIntegration
from lia_agents_core.working_memory import WorkingMemoryService
from lia_agents_core.long_term_memory import LongTermMemoryService
from lia_agents_core.autonomy_engine import AutonomyEngine
from lia_agents_core.learning_extractor import LearningExtractor
from lia_agents_core.tool_adapter import ReActConfig, ReActState, ToolDefinition
from app.shared.tools.insight_tools import get_insight_tools
from app.shared.tools.proactive_tools import get_proactive_tools
from app.shared.tools.predictive_tools import get_predictive_tools

logger = logging.getLogger(__name__)


class EnhancedAgentMixin:
    """Mixin that adds memory, autonomy, learning, and enhanced tools to any ReAct agent.
    
    Provides access to three categories of shared tools:
    - Insight tools: Analytics and historical data analysis
    - Proactive tools: Risk detection and alerts
    - Predictive tools: Forecasting and recommendations
    
    Usage in agent __init__:
        self._setup_enhanced(domain="pipeline")
    
    Usage in agent process():
        extra_context = await self._get_memory_context(session_id, company_id)
        guardrails = await self._resolve_guardrails(company_id)
        tools = base_tools + self._get_all_enhanced_tools()
        # ... run ReAct loop ...
        await self._post_loop_learning(state, company_id, session_id)
    """
    
    _memory_integration: MemoryIntegration
    _autonomy_engine: AutonomyEngine
    _learning_extractor: LearningExtractor
    _enhanced_domain: str
    _calibration_weights: Dict[str, float]
    _calibration_cache_ts: float

    # Default weights used when CalibrationWeight has no data for the tenant/domain.
    _DEFAULT_WEIGHTS: Dict[str, float] = {
        "technical": 0.70,
        "behavioral": 0.30,
    }
    _CALIBRATION_CACHE_TTL: float = 300.0  # 5 minutes

    def _setup_enhanced(self, domain: str) -> None:
        """Initialize enhanced capabilities.

        Args:
            domain: The agent domain name (pipeline, sourcing, wizard, etc.)
        """
        self._enhanced_domain = domain
        self._calibration_weights = dict(self._DEFAULT_WEIGHTS)
        self._calibration_cache_ts = 0.0
        wm = WorkingMemoryService()
        ltm = LongTermMemoryService()
        self._memory_integration = MemoryIntegration(
            working_memory=wm,
            long_term_memory=ltm,
        )
        self._autonomy_engine = AutonomyEngine()
        self._learning_extractor = LearningExtractor()
        logger.info(f"[{domain}] Enhanced agent capabilities initialized")
    
    async def _get_memory_context(
        self,
        session_id: str,
        company_id: str,
    ) -> str:
        """Get enriched context from both working memory and long-term memory.
        
        Args:
            session_id: Current session ID.
            company_id: Company ID for multi-tenancy.
            
        Returns:
            Formatted string with memory context to inject into system prompt.
        """
        try:
            enriched = await self._memory_integration.get_enriched_context(
                session_id=session_id,
                domain=self._enhanced_domain,
                company_id=company_id,
            )
            if enriched:
                logger.debug(
                    f"[{self._enhanced_domain}] Memory context enriched "
                    f"({len(enriched)} chars) for session={session_id}"
                )
            return enriched
        except Exception as exc:
            logger.warning(
                f"[{self._enhanced_domain}] Failed to get memory context: {exc}"
            )
            return ""
    
    @property
    def calibration_weights(self) -> Dict[str, float]:
        """Current calibration weights for this agent's domain.

        Returns cached weights loaded by load_calibration_weights().
        If never loaded, returns defaults (technical=0.70, behavioral=0.30).
        """
        return self._calibration_weights

    async def load_calibration_weights(
        self,
        company_id: str,
        job_id: str | None = None,
    ) -> Dict[str, float]:
        """Load CalibrationWeight from DB for this tenant/domain.

        Cached for _CALIBRATION_CACHE_TTL seconds. Falls back to defaults
        when no calibrated weights exist (graceful — never breaks scoring).

        Call this in agent process() before scoring/ranking operations:
            weights = await self.load_calibration_weights(company_id, job_id)
            technical_weight = weights.get("technical", 0.70)

        Args:
            company_id: Tenant ID for multi-tenant isolation.
            job_id: Optional job-specific weights (falls back to global).

        Returns:
            Dict[dimension_name, adjusted_weight]
        """
        import time

        now = time.time()
        if (now - self._calibration_cache_ts) < self._CALIBRATION_CACHE_TTL:
            return self._calibration_weights

        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import and_, select
            from lia_models.calibration import CalibrationWeight

            async with AsyncSessionLocal() as db:
                # Try job-specific weights first
                query = select(CalibrationWeight).where(
                    and_(
                        CalibrationWeight.company_id == company_id,
                        CalibrationWeight.is_active == True,
                    )
                )
                if job_id:
                    query = query.where(CalibrationWeight.job_id == job_id)
                else:
                    query = query.where(CalibrationWeight.job_id.is_(None))

                result = await db.execute(query)
                weights = result.scalars().all()

                if weights:
                    self._calibration_weights = {
                        w.dimension: w.adjusted_weight for w in weights
                    }
                    logger.info(
                        "[%s] Loaded %d calibration weights (company=%s, job=%s)",
                        self._enhanced_domain, len(weights), company_id, job_id,
                    )
                else:
                    self._calibration_weights = dict(self._DEFAULT_WEIGHTS)
                    logger.debug(
                        "[%s] No calibration weights found, using defaults (company=%s)",
                        self._enhanced_domain, company_id,
                    )

                self._calibration_cache_ts = now

        except Exception as exc:
            logger.warning(
                "[%s] CalibrationWeight load failed (using defaults): %s",
                self._enhanced_domain, exc,
            )
            self._calibration_weights = dict(self._DEFAULT_WEIGHTS)
            self._calibration_cache_ts = now

        return self._calibration_weights

    async def _resolve_guardrails(self, company_id: str) -> List[str]:
        """Resolve dynamic guardrails based on company autonomy policy.

        Args:
            company_id: Company ID to look up policy.

        Returns:
            List of tool names requiring user confirmation.
        """
        # Defaults estáticos usados apenas se todas as fontes falharem
        _DEFAULT_GUARDRAIL_TOOLS = [
            "move_candidate",
            "batch_move",
            "finalize_hiring",
            "delete_job",
            "reject_candidate",
            "send_bulk_email",
            "update_candidate_field",
        ]

        # 1. Tenta autonomy engine (política da empresa)
        try:
            return await self._autonomy_engine.resolve_guardrails(
                company_id=company_id,
                domain=self._enhanced_domain,
            )
        except Exception as exc:
            logger.warning(
                f"[{self._enhanced_domain}] Autonomy engine guardrail resolve failed: {exc}"
            )

        # 2. Fallback: buscar do banco (GuardrailRepository)
        try:
            from lia_config.database import AsyncSessionLocal
            from app.shared.compliance.guardrail_repository import GuardrailRepository
            async with AsyncSessionLocal() as db:
                db_tools = await GuardrailRepository.get_blocked_tools(
                    db=db,
                    domain=self._enhanced_domain,
                    company_id=company_id,
                )
                if db_tools:
                    return db_tools
        except Exception as db_exc:
            logger.warning(
                f"[{self._enhanced_domain}] DB guardrail resolve failed: {db_exc}"
            )

        # 3. Último recurso: lista estática
        logger.warning(
            "[%s] All guardrail sources failed (autonomy engine + DB) — "
            "using static defaults. Verify AutonomyEngine and GuardrailRepository configs.",
            self._enhanced_domain,
        )
        return _DEFAULT_GUARDRAIL_TOOLS
    
    def _get_shared_insight_tools(self) -> List[ToolDefinition]:
        """Get the shared insight tools to add to domain-specific tools.
        
        Returns:
            List of ToolDefinition for insight analytics tools.
        """
        try:
            return get_insight_tools()
        except Exception as exc:
            logger.warning(
                f"[{self._enhanced_domain}] Failed to load insight tools: {exc}"
            )
            return []
    
    def _get_proactive_tools(self) -> List[ToolDefinition]:
        """Get proactive monitoring tools for risk detection and alerts.
        
        Returns:
            List of ToolDefinition for proactive alert tools.
        """
        try:
            return get_proactive_tools()
        except Exception as exc:
            logger.warning(
                f"[{self._enhanced_domain}] Failed to load proactive tools: {exc}"
            )
            return []

    def _get_predictive_tools(self) -> List[ToolDefinition]:
        """Get predictive analytics tools for forecasting and recommendations.
        
        Returns:
            List of ToolDefinition for predictive analytics tools.
        """
        try:
            return get_predictive_tools()
        except Exception as exc:
            logger.warning(
                f"[{self._enhanced_domain}] Failed to load predictive tools: {exc}"
            )
            return []

    def _get_all_enhanced_tools(self) -> List[ToolDefinition]:
        """Get all enhanced tools: insight + proactive + predictive.

        Convenience method that returns the full set of shared tools
        available to any enhanced agent.

        Returns:
            Combined list of all shared ToolDefinitions.
        """
        return (
            self._get_shared_insight_tools()
            + self._get_proactive_tools()
            + self._get_predictive_tools()
        )

    async def emit(
        self,
        to_agent: str,
        event_type: str,
        payload: Dict[str, Any],
        company_id: str,
    ) -> bool:
        """Emit event to another agent via AgentBus.

        Usage in any domain agent:
            await self.emit("pipeline", "candidate_imported", {...}, company_id)

        Returns True if published, False on failure (fail-open).
        """
        try:
            from lia_agents_core.agent_bus import agent_bus
            return await agent_bus.publish(
                from_agent=self._enhanced_domain,
                to_agent=to_agent,
                event_type=event_type,
                payload=payload,
                company_id=company_id,
            )
        except Exception as exc:
            logger.warning(
                "[%s][AgentBus] emit failed (fail-open): %s",
                self._enhanced_domain, exc,
            )
            return False

    def _validate_tool_scope(self, tool_name: str, active_scope: Optional[str]) -> bool:
        """Valida se uma tool está dentro do escopo ativo (E8).

        Fail-open: retorna True se scope não configurado ou em caso de exceção.
        Loga warning `[SCOPE-VIOLATION]` para auditoria quando fora do escopo.

        Args:
            tool_name: Nome da tool a validar.
            active_scope: PromptScope str (TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL) ou None.

        Returns:
            True se permitida ou scope não configurado, False se violação detectada.
        """
        if not active_scope:
            return True
        try:
            from app.tools.scope_config import PromptScope, is_tool_allowed_in_scope
            allowed = is_tool_allowed_in_scope(tool_name, PromptScope(active_scope))
            if not allowed:
                logger.warning(
                    "[%s][SCOPE-VIOLATION] tool=%s scope=%s — fora do escopo (fail-open)",
                    getattr(self, "_enhanced_domain", "unknown"), tool_name, active_scope,
                )
            return allowed
        except Exception as exc:
            logger.debug(
                "[%s] _validate_tool_scope erro (fail-open): %s",
                getattr(self, "_enhanced_domain", "unknown"), exc,
            )
            return True

    async def _fairness_pre_check(
        self,
        user_input: str,
        *,
        company_id: Optional[str] = None,
        recruiter_id: Optional[str] = None,
    ) -> Optional[str]:
        """Camada 1+2 FairnessGuard automático — executar antes de qualquer ReAct loop.

        Verifica se a mensagem do recrutador contém critérios discriminatórios
        explícitos (Camada 1: regex) ou implícitos (Camada 2: léxico). Retorna
        a mensagem educacional se bloqueado, None se limpo.

        Fail-safe: qualquer exceção é logada e o processamento continua.

        Args:
            user_input: Mensagem do recrutador a verificar.

        Returns:
            educational_message (str) se bloqueado, None se limpo.
        """
        if not user_input or not user_input.strip():
            return None
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _guard = FairnessGuard()
            result = _guard.check(user_input)

            if result.soft_warnings:
                logger.info(
                    "[%s][FairnessGuard] %d soft warning(s) — implicit bias detected (text_len=%d)",
                    self._enhanced_domain,
                    len(result.soft_warnings),
                    len(user_input),
                )

            if result.is_blocked:
                logger.warning(
                    "[%s][FairnessGuard] PRE-CHECK bloqueado: category=%s terms=%s",
                    self._enhanced_domain,
                    result.category,
                    result.blocked_terms,
                )
                import asyncio as _asyncio
                try:
                    _asyncio.get_event_loop().create_task(
                        _guard.log_check(
                            result=result,
                            context=self._enhanced_domain,
                            company_id=company_id or None,
                            recruiter_id=recruiter_id or None,
                        )
                    )
                except Exception as _lc_exc:
                    logger.debug(
                        "[%s][FairnessGuard] log_check enqueue failed (fail-open): %s",
                        self._enhanced_domain, _lc_exc,
                    )
                return result.educational_message or (
                    "Esta solicitação não pode ser processada pois contém critérios "
                    "que podem ser discriminatórios. Por favor, reformule com base em "
                    "competências e requisitos técnicos objetivos."
                )

            return None

        except Exception as exc:
            logger.warning(
                "[%s][FairnessGuard] pre-check falhou (fail-safe, continua): %s",
                self._enhanced_domain,
                exc,
            )
            return None

    def _record_confidence(self, state: ReActState) -> None:
        """Record calibrated confidence score to Prometheus (D2 — fail-silent).

        Uses state.confidence_score computed by ReActLoop (tool_success_ratio * 0.7
        + completion_ratio * 0.3). Falls back to 0.5 if metric unavailable.
        """
        pass

    @property
    def model_id(self) -> str:
        """Modelo LLM configurado para este agente (E5 — Multi-Model)."""
        try:
            from app.core.agent_model_config import get_model_for_agent
            domain = getattr(self, "_enhanced_domain", None) or getattr(self, "agent_name", "unknown")
            return get_model_for_agent(domain)
        except Exception:
            from app.core.agent_model_config import DEFAULT_MODEL
            return DEFAULT_MODEL

    async def _record_calibration_event(
        self,
        state: ReActState,
        company_id: str,
        context: Dict[str, Any] | None = None,
    ) -> None:
        """Record a CalibrationEvent capturing the agent's scoring decision.

        Automatically captures: domain, weights used, confidence, decision type.
        This is the LIA side of the calibration loop — recruiter feedback
        (explicit/implicit) comes from the CalibrationService API endpoints.

        Fail-open: errors are logged but never block the agent response.
        """
        try:
            from app.core.database import AsyncSessionLocal
            from lia_models.calibration import CalibrationEvent, FeedbackType, CalibrationStatus

            # Extract scoring info from state
            ctx = context or {}
            candidate_id = ctx.get("candidate_id", "")
            job_id = ctx.get("job_id")
            lia_score = getattr(state, "confidence_score", None)

            # Only record if there's meaningful scoring data
            if not candidate_id:
                return

            event_context = {
                "domain": self._enhanced_domain,
                "weights_used": dict(self._calibration_weights),
                "model_id": self.model_id,
                "tool_calls_count": len(getattr(state, "tool_calls", [])),
            }

            async with AsyncSessionLocal() as db:
                import uuid as _uuid
                event = CalibrationEvent(
                    id=str(_uuid.uuid4()),
                    company_id=company_id,
                    feedback_type=FeedbackType.EXPLICIT_AGREE,  # LIA self-report
                    status=CalibrationStatus.PENDING,
                    candidate_id=candidate_id,
                    job_id=job_id,
                    lia_score=lia_score,
                    lia_recommendation=ctx.get("recommendation"),
                    context=event_context,
                )
                db.add(event)
                await db.commit()

            logger.debug(
                "[%s] CalibrationEvent recorded: candidate=%s score=%s",
                self._enhanced_domain, candidate_id, lia_score,
            )

        except Exception as exc:
            # Fail-open: calibration logging never blocks the agent
            logger.debug(
                "[%s] CalibrationEvent record failed (fail-open): %s",
                self._enhanced_domain, exc,
            )

    async def _post_loop_learning(
        self,
        state: ReActState,
        company_id: str,
        session_id: str,
        context: Dict[str, Any] = None,
    ) -> None:
        """Extract learnings from completed ReAct loop and save to long-term memory.

        Also records CalibrationEvent for the scoring feedback loop.

        Args:
            state: Completed ReAct loop state.
            company_id: Company ID for storage.
            session_id: Session ID for tracking.
            context: Optional additional context for extraction.
        """
        self._record_confidence(state)  # D2 — Prometheus confidence histogram

        # Record calibration event (async, fail-open)
        await self._record_calibration_event(state, company_id, context)

        try:
            learnings = self._learning_extractor.extract(
                state=state,
                domain=self._enhanced_domain,
                context=context or {},
            )
            if learnings:
                await self._memory_integration.save_session_learnings(
                    session_id=session_id,
                    domain=self._enhanced_domain,
                    company_id=company_id,
                    learnings=learnings,
                )
                logger.info(
                    f"[{self._enhanced_domain}] Saved {len(learnings)} learnings "
                    f"for company={company_id} session={session_id}"
                )
        except Exception as exc:
            logger.warning(
                f"[{self._enhanced_domain}] Failed to save learnings: {exc}"
            )
