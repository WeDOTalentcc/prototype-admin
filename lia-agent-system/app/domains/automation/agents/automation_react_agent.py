"""
Automation ReAct Agent — Task decomposition and planning via LangGraph nativo.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.

Domain: automation
"""
import logging
from typing import Any, Dict, List, Optional

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    BaseAgent,
)
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.react_loop import ReActConfig, ReActLoop, ReActState
from app.shared.compliance.audit_callback import AuditCallback
from lia_agents_core.working_memory import WorkingMemoryService
from lia_agents_core.observability import ReActObserver
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
    """ReAct agent for task decomposition, DAG planning and execution orchestration."""

    def __init__(self) -> None:
        super().__init__()
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

    def _get_tools(self) -> list:
        """Todos os tools do domínio Automation (LangGraph usa set completo)."""
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_automation_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        return get_automation_system_prompt()

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
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

        _confidence = 0.75
        if actions:
            _confidence = 0.82
        if state.get("error"):
            _confidence = 0.40
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

    async def process(self, input: AgentInput) -> AgentOutput:
        return await self._process_langgraph(input)

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
