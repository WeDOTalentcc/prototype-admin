"""
Company Settings ReAct Agent - Autonomous agent for company profile configuration.

Uses LangGraph native (create_react_agent) with PostgresSaver for persistence.
Handles company data, culture, tech stack, benefits, and workforce planning
via conversational interface.
"""
import logging
from typing import Any

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
)
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.company_settings.agents.company_system_prompt import (
    get_company_system_prompt,
    COMPANY_DOMAIN_SPECIFIC,
    COMPANY_FEW_SHOT_EXAMPLES,
    COMPANY_REASONING_PROMPT,
)
from app.domains.company_settings.agents.company_tool_registry import get_company_settings_tools
from app.shared.services.confidence_policy_service import confidence_policy_service
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)

from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer


@register_agent("company_settings")
class CompanySettingsReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    # W4-032 (2026-05-23): toggles, policies, fairness configs requerem HITL.
    # Even RBAC-gated, segunda camada de aprovação reduz risco.
    _HITL_ACTION_TYPES = frozenset({
        "update_company_policy",
        "toggle_lia_field",
        "update_culture_profile",
        "update_hiring_policy",
        "delete_company_data",
    })

    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="company_settings",
        domain_specific=COMPANY_DOMAIN_SPECIFIC,
        few_shot_examples=COMPANY_FEW_SHOT_EXAMPLES,
        reasoning_pattern=COMPANY_REASONING_PROMPT.format(memory_summary="", stage_context=""),
    ).text

    def _get_runtime_domain_instructions(self, input: AgentInput) -> str:
        """Sprint 2 Phase 4: substitute {memory_summary} + {stage_context}
        from input.context at runtime (vs empty class-attr default).

        Falls back to legacy DOMAIN_INSTRUCTIONS if PromptComposer fails.
        """
        try:
            ctx = input.context or {}
            return self._compose_runtime_prompt(
                input,
                agent_type="company_settings",
                domain_specific=COMPANY_DOMAIN_SPECIFIC,
            few_shot_examples=COMPANY_FEW_SHOT_EXAMPLES,
                reasoning_template=COMPANY_REASONING_PROMPT,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[company_settings] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._setup_enhanced(domain="company_settings")
        self._fairness_guard = FairnessGuard()
        self._all_tool_names = [t.name for t in get_company_settings_tools()]
        logger.info("[CompanySettingsReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return self.__dict__.get('_domain_name_override', "company_settings")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__['_domain_name_override'] = value

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)


    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.company_settings.agents.company_tool_registry import get_company_settings_tools
            return get_company_settings_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_company_settings_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content and not getattr(m, "tool_call_id", None) and not (isinstance(m, dict) and m.get("tool_call_id")):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Desculpe, nao consegui processar sua solicitacao."

        actions = []
        # PR6 (Task #1006) — Bridge IA→UI: pair AIMessage.tool_calls with the
        # subsequent ToolMessage by tool_call_id so we can surface
        # {tool_name, success, section?, field?} to the WS frame. The frontend
        # `useChatTransport` interceptor reads this list and dispatches
        # `lia:settings-updated` for canonical save tools (origin="agent").
        tool_call_index: dict[str, dict] = {}
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                if isinstance(tc, dict):
                    name = tc.get("name", "")
                    tc_id = tc.get("id", "")
                    args = tc.get("args") or {}
                else:
                    name = getattr(tc, "name", "")
                    tc_id = getattr(tc, "id", "")
                    args = getattr(tc, "args", None) or {}
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))
                if tc_id:
                    tool_call_index[tc_id] = {
                        "tool_name": name,
                        "section": (args or {}).get("section"),
                        "field": (args or {}).get("field"),
                    }

        tool_results: list[dict] = []
        for m in messages:
            tc_id = getattr(m, "tool_call_id", None) or (
                m.get("tool_call_id") if isinstance(m, dict) else None
            )
            if not tc_id or tc_id not in tool_call_index:
                continue
            raw = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            success = True
            try:
                import json as _json
                parsed = _json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(parsed, dict) and "success" in parsed:
                    success = bool(parsed["success"])
            except (ValueError, TypeError):
                pass
            entry = dict(tool_call_index[tc_id])
            entry["success"] = success
            tool_results.append(entry)

        _confidence = 0.75
        if actions:
            _confidence = 0.82
        if state.get("error"):
            _confidence = 0.40
        _conf_action = confidence_policy_service.get_action_for_confidence(_confidence)

        return AgentOutput(
            message=response,
            actions=actions,
            tool_results=tool_results,
            confidence=_confidence,
            metadata={
                "source": "langgraph_native",
                "domain": self.domain_name,
                "confidence_action": _conf_action.value,
            },
        )

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """P36 Full: 3-layer intelligence injection."""
        try:
            weights = await self.load_calibration_weights(str(input.company_id or ""), input.context.get("job_id"))
            if weights and weights != self._DEFAULT_WEIGHTS:
                input.context["calibration_weights"] = weights
        except Exception:  # ADR-031-R3-EXEMPT: carregamento opcional de calibration weights; falha nao bloqueia agente
            pass
        try:
            from app.shared.services.global_insights_service import get_global_insights
            svc = get_global_insights()
            snippet = svc.format_company_for_prompt(await svc.get_company_settings_insights())
            if snippet:
                existing = input.context.get("extra_instructions", "")
                input.context["extra_instructions"] = f"{existing}\n\n{snippet}" if existing else snippet
        except Exception:  # ADR-031-R3-EXEMPT: enriquecimento opcional de insights globais; falha nao bloqueia agente
            pass
        try:
            from app.domains.analytics.services.recruiter_personalization_service import get_recruiter_prompt_context
            ctx = await get_recruiter_prompt_context(str(input.user_id or ""), str(input.company_id or ""))
            if ctx:
                input.context["recruiter_context"] = ctx
        except Exception:  # ADR-031-R3-EXEMPT: carregamento opcional de contexto de recrutador; falha nao bloqueia agente
            pass
        return await super()._process_langgraph(input)

    async def process(self, input: AgentInput) -> AgentOutput:
        # W4-032 (2026-05-23): HITL gate em mudanças de policy / config
        from app.shared.hitl.agent_gate import maybe_request_hitl_approval
        _hitl_response = await maybe_request_hitl_approval(
            agent_input=input,
            domain=self.domain_name,
            action_types=self._HITL_ACTION_TYPES,
            agent_name="company_react_agent",
            description_template=(
                "Confirmar **{action_type}** nas configurações da empresa. "
                "Mudanças de policy afetam todas as operações downstream."
            ),
        )
        if _hitl_response is not None:
            return _hitl_response

        return await self._process_langgraph(input)

    async def process_legacy_format(
        self,
        message: str,
        company_id: str,
        session_id: str,
        current_data: Any = None,
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        agent_input = AgentInput(
            message=message,
            company_id=company_id,
            session_id=session_id,
            context={
                "company_data": current_data or {},
            },
            conversation_history=conversation_history or [],
        )
        output = await self.process(agent_input)
        updated_fields: dict[str, Any] = {}
        for action in (output.actions or []):
            if action.action_type == "update_company" and action.params:
                updated_fields.update(action.params)
        state_updates = output.state_updates or {}
        if state_updates:
            updated_fields.update(state_updates)
        return {
            "reply": output.message,
            "updated_fields": updated_fields,
            "section": output.metadata.get("section") if output.metadata else None,
        }

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "max_iterations": 5,
            "model_provider": "claude",
        }
