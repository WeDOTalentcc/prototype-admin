"""
EnhancedAgentMixin - Provides memory, autonomy, and learning capabilities to ReAct agents.

All 6 domain agents can use this mixin to:
1. Enrich system prompts with long-term memories before reasoning
2. Resolve dynamic guardrails from CompanyHiringPolicy
3. Extract and save learnings after each ReAct loop execution
"""
import logging
from typing import Any, Dict, List

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
