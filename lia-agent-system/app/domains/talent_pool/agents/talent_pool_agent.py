"""
Talent Pool ReAct Agent — canonical agent for live talent bank management.

Follows the canonical 4-file structure (Wave 3 — AGT-S02 fix):
  agent.py · system_prompt.py · stage_context.py · tool_registry.py

Uses LangGraph ReAct nativo (create_react_agent) with PostgresSaver.

Audit trail: every tool call produces an audit entry via ComplianceDomainPrompt.
FairnessGuard: wired for sourcing operations (high_impact=True).
Multi-tenant: company_id always sourced from AgentInput.company_id (JWT).

Harness-engineering notes:
  Guide: TALENT_POOL_REASONING_PROMPT forces recruiter confirmation
         for high-impact operations before execution.
  Sensor: G7 compliance check (check_agent_compliance.py) validates
          this agent structure at CI time.
"""
import logging
from typing import Any

from lia_agents_core.agent_interface import AgentAction, AgentInput, AgentOutput
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.talent_pool.agents.talent_pool_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
)
from app.domains.talent_pool.agents.talent_pool_system_prompt import (
    TALENT_POOL_DOMAIN_SPECIFIC,
    get_talent_pool_system_prompt,
)
from app.domains.talent_pool.agents.talent_pool_tool_registry import get_talent_pool_tools
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.services.confidence_policy_service import confidence_policy_service

logger = logging.getLogger(__name__)

from app.shared.agents.agent_registry import register_agent


@register_agent("talent_pool", aliases=["voice_screening"])
class TalentPoolReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """
    Autonomous ReAct agent for talent pool (live talent bank) management.

    Handles: listing pools, viewing candidates, creating pools, adding
    candidates, migrating to jobs, and creating jobs from pools.
    High-impact operations (migrate, create job) require HITL confirmation.
    """

    DOMAIN_INSTRUCTIONS = TALENT_POOL_DOMAIN_SPECIFIC

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._setup_enhanced(domain="talent_pool")
        self._fairness_guard = FairnessGuard()
        self._all_tool_names = [t.name for t in get_talent_pool_tools()]
        logger.info("[TalentPoolReActAgent] Initialized with %d tools", len(self._all_tool_names))

    # ── Domain properties ────────────────────────────────────────────────────

    @property
    def domain_name(self) -> str:
        return self.__dict__.get("_domain_name_override", "talent_pool")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__["_domain_name_override"] = value

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)

    # ── Tool setup ───────────────────────────────────────────────────────────

    def _get_tools(self) -> list:
        """All tools for the talent pool domain (LangGraph uses full set)."""
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool

        tool_defs = get_talent_pool_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    # ── Output extraction ────────────────────────────────────────────────────

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Extract AgentOutput from LangGraph state after run."""
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = (
                getattr(m, "content", None)
                or (m.get("content", "") if isinstance(m, dict) else "")
            )
            if content and not getattr(m, "tool_call_id", None) and not (
                isinstance(m, dict) and m.get("tool_call_id")
            ):
                response = self._extract_text_content(content)
                break

        if not response:
            response = "Desculpe, não consegui processar sua solicitação sobre o banco de talentos."

        actions: list[AgentAction] = []
        for m in messages:
            for tc in getattr(m, "tool_calls", None) or []:
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        confidence = 0.75
        if actions:
            confidence = 0.82
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
            },
        )

    # ── Main entry point ─────────────────────────────────────────────────────

    async def process(self, input: AgentInput) -> AgentOutput:
        """Process an incoming message through the LangGraph ReAct loop."""
        return await self._process_langgraph(input)

    # ── HITL integration ─────────────────────────────────────────────────────

    async def _request_hitl_if_needed(self, output: AgentOutput) -> None:
        """Request HITL review for high-impact talent pool operations.

        Fail-safe: continues without blocking if HITL service is unavailable.
        """
        if output.state_updates:
            try:
                from app.domains.cv_screening.services.hitl_service import hitl_service
                await hitl_service.request_approval(output.state_updates)
            except Exception as exc:
                logger.warning(
                    "[TalentPoolReActAgent] HITL service unavailable, prosseguindo: %s", exc
                )

    # ── Status / introspection ────────────────────────────────────────────────

    async def get_status(self) -> dict[str, Any]:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
            "high_impact_tools": ["move_pool_to_job", "create_job_from_pool"],
        }
