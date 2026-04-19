"""Candidate Self-Service ReAct Agent — read-only, FairnessGuard, HITL-aware."""
import logging
from typing import Any

from lia_agents_core.agent_interface import AgentAction, AgentInput, AgentOutput
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.candidate_self_service.agents.candidate_system_prompt import (
    CSS_DOMAIN_SPECIFIC,
    CSS_FEW_SHOT_EXAMPLES,
)
from app.domains.candidate_self_service.agents.candidate_tool_registry import get_candidate_tools
from app.shared.agents.agent_registry import register_agent
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.services.confidence_policy_service import confidence_policy_service

logger = logging.getLogger(__name__)


@register_agent("candidate_self_service")
class CandidateSelfServiceAgent(LangGraphReActBase, EnhancedAgentMixin):
    """Read-only agent: candidate queries own recruitment status.

    LLM: Claude Haiku 4.5 (volume candidate traffic, lower cost).
    Tool whitelist: 3 read-only tools only (ADR enforced in tool registry).
    FairnessGuard: mandatory on all rejection/feedback responses.
    HITL: triggered when feedback state_updates are present.
    """

    DOMAIN_INSTRUCTIONS = CSS_DOMAIN_SPECIFIC + "\n\n" + CSS_FEW_SHOT_EXAMPLES

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._setup_enhanced(domain="candidate_self_service")
        self._fairness_guard = FairnessGuard()
        self._all_tool_names = [t.name for t in get_candidate_tools()]
        logger.info("[CSS Agent] Initialized with %d tools", len(self._all_tool_names))

    @property
    def domain_name(self) -> str:
        return self.__dict__.get("_domain_name_override", "candidate_self_service")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__["_domain_name_override"] = value

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)

    def _get_tools(self) -> list:
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_candidate_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    async def _request_hitl_if_needed(self, output: AgentOutput) -> None:
        """Request HITL for feedback responses. Fail-safe: never blocks."""
        if output.state_updates:
            try:
                from app.domains.cv_screening.services.hitl_service import hitl_service
                await hitl_service.request_approval(output.state_updates)
            except Exception as exc:
                logger.warning("[CSS Agent] HITL unavailable, prosseguindo: %s", exc)

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (
                m.get("content", "") if isinstance(m, dict) else ""
            )
            if content and not getattr(m, "tool_call_id", None):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Não consegui obter informações neste momento. Tente novamente em alguns instantes."

        actions = []
        for m in messages:
            for tc in getattr(m, "tool_calls", None) or []:
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        confidence = 0.80 if actions else 0.65
        if state.get("error"):
            confidence = 0.40
        conf_action = confidence_policy_service.get_action_for_confidence(confidence)

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=confidence,
            metadata={
                "source": "langgraph_native",
                "domain": self.domain_name,
                "confidence_action": conf_action.value,
                "candidate_self_service": True,
            },
        )

    async def process(self, input: AgentInput) -> AgentOutput:
        return await self._process_langgraph(input)

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "model_tier": "fast",
            "max_tools": 3,
        }
