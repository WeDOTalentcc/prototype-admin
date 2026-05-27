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
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer


@register_agent("talent_pool", aliases=["voice_screening"])
class TalentPoolReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    """
    Autonomous ReAct agent for talent pool (live talent bank) management.

    Handles: listing pools, viewing candidates, creating pools, adding
    candidates, migrating to jobs, and creating jobs from pools.
    High-impact operations (migrate, create job) require HITL confirmation.
    """

    DOMAIN_INSTRUCTIONS = TALENT_POOL_DOMAIN_SPECIFIC

    def _get_runtime_domain_instructions(self, input: AgentInput) -> str:
        """T-D: injeta tenant_context_snippet via TenantAwareAgentMixin.

        Antes desta refatoração, ``DOMAIN_INSTRUCTIONS`` era apenas o bloco
        estático ``TALENT_POOL_DOMAIN_SPECIFIC`` — sem snippet de tenant,
        a LIA respondia "qual a empresa?" mesmo com JWT correto.

        Falls back to legacy DOMAIN_INSTRUCTIONS if PromptComposer fails.
        """
        try:
            ctx = input.context or {}
            return self._compose_runtime_prompt(
                input,
                agent_type="talent_pool",
                domain_specific=TALENT_POOL_DOMAIN_SPECIFIC,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[talent_pool] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

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
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool

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

        Wave C2.5 (2026-05-27): exception narrow. HitlServiceUnavailable =
        degraded mode (log + flag metadata + continua). Outras Exception =
        bug real, re-raise pra alarme nao mascarar como \"unavailability\".
        AUD-4 audit trail nos dois ramos (compliance LGPD Art. 20).
        """
        if not output.state_updates:
            return
        company_id = getattr(output, "company_id", None) or (
            output.metadata.get("company_id") if isinstance(output.metadata, dict) else None
        )
        try:
            from app.domains.cv_screening.services.hitl_service import (
                hitl_service,
                HitlServiceUnavailable,
            )
        except ImportError:
            # Module not importable — degraded mode (best-effort)
            logger.warning(
                "[TalentPoolReActAgent] HITL module not importable, degraded mode",
                extra={"company_id": company_id},
            )
            if isinstance(output.metadata, dict):
                output.metadata["hitl_bypassed"] = True
                output.metadata["hitl_bypass_reason"] = "import_error"
            return

        try:
            await hitl_service.request_approval(output.state_updates)
        except HitlServiceUnavailable as exc:
            logger.warning(
                "[TalentPoolReActAgent] HITL service unavailable, degraded mode",
                extra={"exception": str(exc), "company_id": company_id},
            )
            if isinstance(output.metadata, dict):
                output.metadata["hitl_bypassed"] = True
                output.metadata["hitl_bypass_reason"] = "service_unavailable"
            # AUD-4: registrar bypass como decisao auditavel
            try:
                from app.shared.services.audit_service import audit_service
                await audit_service.log_decision(
                    company_id=company_id or "unknown",
                    agent_name="talent_pool_react_agent",
                    decision_type="hitl_bypass",
                    action="hitl_bypass_degraded",
                    decision="continued_without_approval",
                    reasoning=[
                        f"HitlServiceUnavailable: {str(exc)[:200]}",
                        "AUD-4 degraded mode (service down)",
                    ],
                    criteria_used=["hitl_service_health"],
                    human_review_required=True,
                )
            except Exception as _audit_err:
                logger.warning(
                    "[TalentPoolReActAgent] audit log_decision failed: %s", _audit_err,
                )
        except Exception:
            # Bug real (TypeError/AttributeError/etc): re-raise nao mascarar
            logger.error(
                "[TalentPoolReActAgent] HITL request failed unexpectedly",
                exc_info=True,
                extra={"company_id": company_id},
            )
            raise

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
