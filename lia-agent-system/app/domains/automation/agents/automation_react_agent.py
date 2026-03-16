"""
Automation ReAct Agent — Task decomposition and planning via ReAct loop.

Replaces TaskPlannerAgent (deprecated Sprint 5).
Follows the canonical 4-file ReAct pattern: agent | tool_registry | system_prompt | stage_context.

Domain: automation
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

from app.domains.automation.agents.automation_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
    get_transition_prompt,
)
from app.domains.automation.agents.automation_system_prompt import get_automation_system_prompt
from app.domains.automation.agents.automation_tool_registry import (
    get_automation_tools,
    get_stage_tools,
)

logger = logging.getLogger(__name__)


class AutomationReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """ReAct agent for task decomposition, DAG planning and execution orchestration.

    Each call to ``process`` runs a full Reason-Act-Observe cycle using the
    automation-specific tools (decompose_task, prioritize_tasks, get_execution_plan,
    build_dag, check_dependencies, get_next_tasks).
    """

    def __init__(self) -> None:
        super().__init__()  # inicializa LangGraphBase._checkpointer
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_automation_tools()]
        self._setup_enhanced(domain="automation")
        logger.info("[AutomationReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "automation"

    @property
    def available_tools(self) -> List[str]:
        return list(self._all_tool_names)

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tools(self) -> list:
        """Todos os tools do domínio Automation (LangGraph usa set completo)."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_automation_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Automation."""
        return get_automation_system_prompt()

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Converte MessagesState final em AgentOutput."""
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content and not getattr(m, "tool_call_id", None) and not (isinstance(m, dict) and m.get("tool_call_id")):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Planejamento concluído."

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
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
        from app.core.config import settings
        if settings.USE_LANGGRAPH_NATIVE:
            return await self._process_langgraph(input)
        return await self._process_react_loop(input)

    async def _process_react_loop(self, input: AgentInput) -> AgentOutput:
        """Process a task planning request through the automation ReAct loop."""
        start_time = time.time()
        session_id = input.session_id
        company_id = input.company_id
        stage = input.context.get("current_stage", "decompose")

        logger.info(
            f"[AutomationReActAgent] process session={session_id} stage={stage} company={company_id}"
        )

        try:
            tools = get_stage_tools(stage)
            if not tools:
                tools = get_automation_tools()

            system_prompt = get_automation_system_prompt()
            stage_ctx = get_stage_context(stage)

            # Enrich input with company context for tools
            enriched_message = input.message
            if company_id and "company_id" not in enriched_message:
                enriched_message = f"[company_id: {company_id}] {enriched_message}"

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
                    domain="automation",
                    agent_class="AutomationReActAgent",
                    company_id=company_id,
                    user_id=input.user_id,
                )
            except Exception as obs_err:
                logger.warning(f"[AutomationReActAgent] Failed to create observer: {obs_err}")

            final_state = await loop.run(
                message=enriched_message,
                context={
                    **input.context,
                    "stage": stage,
                    "stage_description": stage_ctx.get("description", ""),
                    "company_id": company_id,
                    "user_id": input.user_id,
                },
                session_id=session_id,
                observer=observer,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[AutomationReActAgent] Done session={session_id} "
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

            confidence = 0.3 if final_state.error else (0.85 if tool_results else 0.7)

            return AgentOutput(
                message=final_state.final_response or "Planejamento concluído.",
                actions=actions,
                tool_results=tool_results,
                confidence=confidence,
                error=final_state.error,
                metadata={
                    "stage": stage,
                    "iterations": final_state.iteration,
                    "domain": "automation",
                    "elapsed_ms": elapsed_ms,
                },
            )

        except Exception as exc:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[AutomationReActAgent] ReActLoop failed: {exc}", exc_info=True)
            return AgentOutput(
                message="Erro ao processar planejamento de tarefas. Tente novamente.",
                confidence=0.0,
                error=str(exc),
                metadata={"elapsed_ms": elapsed_ms},
            )

    # ------------------------------------------------------------------
    # Compatibility shim for task_planner.py API endpoints
    # ------------------------------------------------------------------

    async def decompose_task(
        self,
        task_description: str,
        company_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        deadline: Any = None,
        persist: bool = True,
        additional_context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Direct call for API endpoints — bypasses ReAct loop for deterministic results."""
        from app.domains.automation.agents.automation_tool_registry import _wrap_decompose_task
        return await _wrap_decompose_task(
            task_description=task_description,
            company_id=company_id,
            goal_id=goal_id,
            parent_task_id=parent_task_id,
            deadline=deadline,
            persist=persist,
            user_id=user_id,
        )

    async def prioritize_tasks(
        self,
        task_ids: Optional[List[str]] = None,
        goal_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Direct call for API endpoints — bypasses ReAct loop for deterministic results."""
        from app.domains.automation.agents.automation_tool_registry import _wrap_prioritize_tasks
        return await _wrap_prioritize_tasks(task_ids=task_ids or [], goal_id=goal_id)
