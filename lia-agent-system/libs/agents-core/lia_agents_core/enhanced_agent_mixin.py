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
from lia_agents_core.react_loop import ReActConfig, ReActState, ToolDefinition
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
    
    def _setup_enhanced(self, domain: str) -> None:
        """Initialize enhanced capabilities.
        
        Args:
            domain: The agent domain name (pipeline, sourcing, wizard, etc.)
        """
        self._enhanced_domain = domain
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
        # C4: Prometheus — registrar fallback para observabilidade
        try:
            from app.shared.observability.agent_metrics import record_agent_request
            record_agent_request(
                agent=self._enhanced_domain,
                domain=self._enhanced_domain,
                status="guardrail_fallback",
            )
        except Exception:
            pass
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
            from app.shared.agents.agent_bus import agent_bus
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

    async def _fairness_pre_check(self, user_input: str) -> Optional[str]:
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
        try:
            from app.shared.observability.agent_metrics import record_confidence
            domain = getattr(self, "_enhanced_domain", "unknown")
            record_confidence(
                agent=domain,
                domain=domain,
                confidence=getattr(state, "confidence_score", 0.5),
            )
        except Exception:
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

    async def _post_loop_learning(
        self,
        state: ReActState,
        company_id: str,
        session_id: str,
        context: Dict[str, Any] = None,
    ) -> None:
        """Extract learnings from completed ReAct loop and save to long-term memory.

        Args:
            state: Completed ReAct loop state.
            company_id: Company ID for storage.
            session_id: Session ID for tracking.
            context: Optional additional context for extraction.
        """
        self._record_confidence(state)  # D2 — Prometheus confidence histogram
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
