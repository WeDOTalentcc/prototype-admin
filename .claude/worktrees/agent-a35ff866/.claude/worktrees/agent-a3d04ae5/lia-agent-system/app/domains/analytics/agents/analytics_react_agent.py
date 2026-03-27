"""
Analytics ReAct Agent — KPI analysis, reports and hiring predictions via ReAct loop.

Follows the canonical 4-file ReAct pattern: agent | tool_registry | system_prompt | stage_context.

Domain: analytics
"""
import logging
import time
from typing import Any, Dict, List, Optional

from app.shared.agents.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    BaseAgent,
)
from app.shared.agents.enhanced_agent_mixin import EnhancedAgentMixin
from app.shared.agents.langgraph_react_base import LangGraphReActBase
from app.shared.agents.react_loop import ReActConfig, ReActLoop, ReActState
from app.shared.compliance.audit_callback import AuditCallback
from app.shared.agents.working_memory import WorkingMemoryService
from app.shared.agents.observability import ReActObserver
from app.services.confidence_policy_service import confidence_policy_service

from app.domains.analytics.agents.analytics_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
    get_transition_prompt,
)
from app.domains.analytics.agents.analytics_system_prompt import get_analytics_system_prompt
from app.domains.analytics.agents.analytics_tool_registry import (
    get_analytics_tools,
    get_stage_tools,
)

logger = logging.getLogger(__name__)


class AnalyticsReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """ReAct agent for analytics: KPI analysis, reports, predictions and agent monitoring.

    Each call to ``process`` runs a full Reason-Act-Observe cycle using the
    analytics-specific tools (get_job_insights, predict_hiring_metrics,
    generate_job_report, generate_candidate_report, get_search_analytics,
    get_agent_performance).
    """

    def __init__(self) -> None:
        super().__init__()  # inicializa LangGraphBase._checkpointer
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_analytics_tools()]
        self._setup_enhanced(domain="analytics")
        logger.info("[AnalyticsReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "analytics"

    @property
    def available_tools(self) -> List[str]:
        return list(self._all_tool_names)

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tools(self) -> list:
        """Todos os tools do domínio Analytics (LangGraph usa set completo)."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_analytics_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Analytics."""
        return get_analytics_system_prompt()

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Converte MessagesState final em AgentOutput."""
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (
                m.get("content", "") if isinstance(m, dict) else ""
            )
            if content and not getattr(m, "tool_call_id", None) and not (
                isinstance(m, dict) and m.get("tool_call_id")
            ):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Análise concluída."

        actions = []
        for m in messages:
            for tc in getattr(m, "tool_calls", None) or []:
                name = (
                    tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                )
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        # Calcular confidence baseado no resultado e calibrar via ConfidencePolicyService
        _confidence = 0.75  # base para ações completadas com sucesso
        if actions:
            _confidence = 0.82  # tool foi chamada com sucesso
        if state.get("error"):
            _confidence = 0.40  # houve erro
        _conf_action = confidence_policy_service.get_action_for_confidence(_confidence)

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=_confidence,
            metadata={
                "source": "langgraph_native",
                "domain": self.domain_name,
                "confidence_action": _conf_action.value,
            },
        )

    # ------------------------------------------------------------------
    # Dual-path: LangGraph nativo ou ReActLoop legado
    # ------------------------------------------------------------------

    async def process(self, input: AgentInput) -> AgentOutput:
        """Dual-path: LangGraph nativo (USE_LANGGRAPH_NATIVE=True) ou ReActLoop."""
        try:
            from app.core.config import settings
            if settings.USE_LANGGRAPH_NATIVE:
                return await self._process_langgraph(input)
            return await self._process_react_loop(input)
        except Exception as exc:
            logger.error(f"[AnalyticsReActAgent] Unhandled error: {exc}", exc_info=True)
            return AgentOutput(
                message="Erro ao processar análise. Tente novamente.",
                confidence=0.0,
                error=str(exc),
            )

    async def _process_react_loop(self, input: AgentInput) -> AgentOutput:
        """Process an analytics request through the analytics ReAct loop."""
        start_time = time.time()
        session_id = input.session_id
        company_id = input.company_id
        stage = input.context.get("current_stage", "query-understanding")

        logger.info(
            f"[AnalyticsReActAgent] process session={session_id} stage={stage} company={company_id}"
        )

        try:
            tools = get_stage_tools(stage)
            if not tools:
                tools = get_analytics_tools()

            system_prompt = get_analytics_system_prompt()
            stage_ctx = get_stage_context(stage)

            # Enrich input with company context for tools
            enriched_message = input.message
            if company_id and "company_id" not in enriched_message:
                enriched_message = f"[company_id: {company_id}] {enriched_message}"

            # Injetar benchmark setorial para anti-sycophancy (II.7)
            _benchmark_context = ""
            try:
                from app.services.sector_benchmark_service import SectorBenchmarkService
                company_sector = input.context.get("company_sector", "")
                if company_sector:
                    _benchmark = await SectorBenchmarkService().get_benchmark(
                        sector=company_sector,
                        db=None,
                    )
                    if _benchmark:
                        _benchmark_context = f"\n\n## Benchmark Setorial\nCompare SEMPRE com o benchmark setorial antes de avaliar performance ou validar métricas.\n{_benchmark}\n"
            except Exception:
                _benchmark_context = ""

            audit_callback = AuditCallback(
                user_id=str(input.user_id or "system"),
                company_id=str(company_id or ""),
                session_id=str(session_id),
                domain=self.domain_name,
                agent_type="react",
            )

            config = ReActConfig(
                max_iterations=6,
                system_prompt=system_prompt,
                available_tools=tools,
                domain=self.domain_name,
                model_provider="claude",
                temperature=0.3,
                audit_callback=audit_callback,
            )

            loop = ReActLoop(config=config, working_memory_service=self._memory_service)

            observer = None
            try:
                observer = ReActObserver(
                    session_id=session_id,
                    domain="analytics",
                    agent_class="AnalyticsReActAgent",
                    company_id=company_id,
                    user_id=input.user_id,
                )
            except Exception as obs_err:
                logger.warning(f"[AnalyticsReActAgent] Failed to create observer: {obs_err}")

            final_state = await loop.run(
                message=enriched_message,
                context={
                    **input.context,
                    "stage": stage,
                    "stage_description": stage_ctx.get("description", ""),
                    "company_id": company_id,
                    "user_id": input.user_id,
                    "benchmark_context": _benchmark_context,
                },
                session_id=session_id,
                observer=observer,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[AnalyticsReActAgent] Done session={session_id} "
                f"iterations={final_state.iteration} elapsed={elapsed_ms}ms"
            )

            self._record_confidence(final_state)  # D2 — calibrated confidence

            actions = [
                AgentAction(
                    action_type=a.get("type", "call_tool"),
                    params={"tool": a.get("tool", ""), "args": a.get("args", {})},
                    requires_confirmation=a.get("type") == "guardrail_blocked",
                )
                for a in final_state.actions_taken
            ]

            tool_results = [
                {
                    "tool_name": tc.get("tool_name", ""),
                    "result": tc.get("result", {}),
                    "duration_ms": tc.get("duration_ms", 0),
                }
                for tc in final_state.tool_calls_made
            ]

            confidence = 0.0 if final_state.error else (0.88 if tool_results else 0.7)

            return AgentOutput(
                message=final_state.final_response or "Análise concluída.",
                actions=actions,
                tool_results=tool_results,
                confidence=confidence,
                error=final_state.error,
                metadata={
                    "stage": stage,
                    "iterations": final_state.iteration,
                    "domain": "analytics",
                    "elapsed_ms": elapsed_ms,
                },
            )

        except Exception as exc:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[AnalyticsReActAgent] ReActLoop failed: {exc}", exc_info=True)
            return AgentOutput(
                message="Erro ao processar análise. Tente novamente.",
                confidence=0.0,
                error=str(exc),
                metadata={"elapsed_ms": elapsed_ms},
            )
