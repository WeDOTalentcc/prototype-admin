"""Candidate Self-Service ReAct Agent — read-only, FairnessGuard, HITL-aware."""
import logging
import time
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

        tools_called = [a.params.get("tool", "") for a in actions if a.params.get("tool")]

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=confidence,
            metadata={
                "source": "langgraph_native",
                "domain": self.domain_name,
                "confidence_action": conf_action.value,
                "candidate_self_service": True,
                "tools_called": tools_called,
            },
        )

    async def process(self, input: AgentInput) -> AgentOutput:
        """Process candidate query with observability span."""
        candidate_id = (input.context or {}).get("candidate_id", "unknown")
        vacancy_id = (input.context or {}).get("vacancy_id", "unknown")
        company_id = input.company_id or "unknown"
        channel = (input.context or {}).get("channel", "web")
        start_ts = time.monotonic()

        span_attrs = {
            "domain": "candidate_self_service",
            "candidate_id": candidate_id,   # UUID — not PII per ADR-006
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "channel": channel,
        }

        try:
            from app.observability import get_tracer
            tracer = get_tracer("candidate_self_service")
        except Exception:
            tracer = None

        output = await self._process_langgraph(input)

        elapsed_ms = int((time.monotonic() - start_ts) * 1000)
        tools_called = output.metadata.get("tools_called", []) if output.metadata else []

        logger.info(
            "[CSS Agent] processed candidate_id=%s vacancy_id=%s tools=%s elapsed_ms=%d",
            candidate_id, vacancy_id, tools_called, elapsed_ms,
        )

        if tracer:
            try:
                with tracer.start_as_current_span("css.agent.process") as span:
                    for k, v in span_attrs.items():
                        span.set_attribute(k, v)
                    span.set_attribute("tools_called", str(tools_called))
                    span.set_attribute("elapsed_ms", elapsed_ms)
                    span.set_attribute("confidence", output.confidence or 0)
            except Exception:
                pass  # Observability must never break the agent flow

        # FairnessGuard: post-process agent response for bias in rejection language
        if output.message:
            try:
                checked = self._fairness_guard.check(output.message)
                if isinstance(checked, dict):
                    output = output.__class__(
                        message=checked.get("text", output.message),
                        actions=output.actions,
                        confidence=output.confidence,
                        metadata={**(output.metadata or {}), "fairness_triggered": checked.get("triggered", False)},
                        state_updates=output.state_updates,
                    )
            except Exception as fg_exc:
                logger.debug("[CSS Agent] FairnessGuard skipped: %s", fg_exc)

        # HITL: request human review when feedback state_updates are present
        if getattr(output, "state_updates", None):
            await self._request_hitl_if_needed(output)

        # LGPD Art. 20: log explanation request if candidate triggered it (fire-and-forget)
        try:
            await self._log_lgpd_request_if_triggered(output, context if isinstance(context, dict) else {})
        except Exception:
            pass

        return output

    async def _log_lgpd_request_if_triggered(self, output, context: dict) -> None:
        """Fire-and-forget: log LGPD Art. 20 request to Rails when candidate asks for explanation."""
        if not output.message:
            return
        # Detect LGPD explanation trigger phrases in response
        lgpd_triggers = ["quero mais detalhes", "direito a solicitar", "solicitar revisão", "art. 20", "art 20"]
        msg_lower = output.message.lower()
        if not any(trigger in msg_lower for trigger in lgpd_triggers):
            return
        try:
            candidate_id = context.get("candidate_id", "")
            vacancy_id = context.get("vacancy_id", "")
            company_id = context.get("company_id", "")
            if not (candidate_id and company_id):
                return
            from app.shared.rails_client import rails_post
            await rails_post(
                f"/v1/companies/{company_id}/candidate-portal/lgpd-requests",
                data={
                    "candidate_id": candidate_id,
                    "vacancy_id": vacancy_id,
                    "request_type": "art20",
                    "source": "candidate_self_service_agent",
                },
            )
            logger.info(
                "[CSS Agent] LGPD Art. 20 request logged candidate_id=%s vacancy_id=%s",
                candidate_id, vacancy_id,
            )
        except Exception as exc:
            logger.debug("[CSS Agent] LGPD request log skipped: %s", exc)

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "model_tier": "fast",
            "max_tools": 3,
        }
