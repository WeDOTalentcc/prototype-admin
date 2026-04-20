"""
Wizard ReAct Agent - Autonomous agent for job creation wizard.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistencia.
Migracao completa concluida -- path legado ReActLoop removido.
"""
import logging

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    NavigationCommand,
)
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.job_management.agents.stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
)
from app.domains.job_management.agents.wizard_system_prompt import build_system_prompt, WIZARD_DOMAIN_SPECIFIC, WIZARD_REASONING_PROMPT
from app.domains.job_management.agents.wizard_tool_registry import (
    get_wizard_tools,
)

logger = logging.getLogger(__name__)


from contextlib import contextmanager


@contextmanager
def _wizard_tenant_scope(company_id: str | None):
    """Set _current_company_id contextvar for LangGraph ReAct execution.

    Mirrors _wsi_tenant_scope from wsi_interview_graph.py — ensures that
    get_current_llm_tenant() resolves correctly inside wizard tool calls
    without asking the user for company_id.
    """
    token = None
    try:
        from app.middleware.auth_enforcement import _current_company_id
        cid = str(company_id or "")
        if cid and not _current_company_id.get(""):
            token = _current_company_id.set(cid)
    except Exception as _exc:
        logger.debug("[WizardReActAgent] tenant_scope skipped: %s", _exc)
    try:
        yield
    finally:
        if token is not None:
            try:
                from app.middleware.auth_enforcement import _current_company_id
                _current_company_id.reset(token)
            except Exception:
                pass

_CONFIRMATION_WORDS = {
    "sim", "pode", "vamos", "avanca", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "confirmo", "positivo",
}


from app.shared.agents.agent_registry import register_agent

@register_agent("wizard", aliases=["job_management", "job_mgmt"])
class WizardReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    DOMAIN_INSTRUCTIONS = WIZARD_DOMAIN_SPECIFIC + "\n\n" + WIZARD_REASONING_PROMPT.format(memory_summary="", stage_context="")

    """Autonomous agent for the job creation wizard via LangGraph nativo."""

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_wizard_tools()]
        self._setup_enhanced(domain="wizard")
        # Per-request wizard state — loaded async in process() before LangGraph run
        self._current_wizard_state = None
        logger.info("[WizardReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "wizard"

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)

    def _get_tools(self) -> list:
        """Todos os tools do dominio Wizard (LangGraph usa set completo)."""
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_wizard_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """Extend base system prompt with WizardState snippet when available."""
        base = super()._get_system_prompt(input)
        if self._current_wizard_state is not None:
            try:
                snippet = self._current_wizard_state.to_prompt_snippet()
                return f"{base}\n\n---\n\n{snippet}"
            except Exception as exc:
                logger.debug("[WizardReActAgent] wizard_state snippet failed: %s", exc)
        return base

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
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        current_stage = input.context.get("current_stage", "input-evaluation")
        navigation = None
        try:
            stage_def = STAGE_DEFINITIONS.get(current_stage, {})
            next_stage = stage_def.get("next_stage", "")
            if next_stage:
                user_msgs = [
                    (m.content if hasattr(m, "content") else m.get("content", "")).lower()
                    for m in messages
                    if (getattr(m, "type", "") == "human" or (isinstance(m, dict) and m.get("role") == "user"))
                ]
                last_user = user_msgs[-1] if user_msgs else ""
                if any(w in last_user for w in _CONFIRMATION_WORDS):
                    navigation = NavigationCommand(
                        target_stage=next_stage,
                        reason=stage_def.get("transition_criteria", "Criterios atendidos"),
                        auto_navigate=False,
                    )
        except Exception:
            pass

        return AgentOutput(
            message=response,
            actions=actions,
            navigation=navigation,
            confidence=0.85,
            metadata={"source": "langgraph_native", "domain": self.domain_name},
        )

    async def process(self, input: AgentInput) -> AgentOutput:
        _blocked_msg = await self._fairness_pre_check(input.message or "")
        if _blocked_msg:
            return AgentOutput(
                message=_blocked_msg,
                confidence=1.0,
                metadata={"source": "fairness_guard", "domain": self.domain_name},
            )

        # --- WizardState: load persisted fields before building system prompt ---
        conversation_id = str(input.session_id or "")
        try:
            from app.orchestrator.wizard_state import WizardState, get_wizard_state
            self._current_wizard_state = await get_wizard_state(conversation_id)
            if self._current_wizard_state is None:
                # First turn — seed state with auth context
                self._current_wizard_state = WizardState(
                    conversation_id=conversation_id,
                    company_id=str(input.company_id or ""),
                    recruiter_id=str(input.user_id or ""),
                )
            logger.debug(
                "[WizardReActAgent] wizard_state loaded step=%s title=%s conversation=%s",
                self._current_wizard_state.step,
                self._current_wizard_state.title,
                conversation_id,
            )
        except Exception as exc:
            logger.warning("[WizardReActAgent] wizard_state load failed (fail-safe): %s", exc)
            self._current_wizard_state = None

        with _wizard_tenant_scope(str(input.company_id or "")):
            output = await self._process_langgraph(input)

        # --- WizardState: extract collected fields from tool calls and persist ---
        if self._current_wizard_state is not None:
            await self._update_and_persist_wizard_state(input, output, conversation_id)

        return output

    async def _update_and_persist_wizard_state(
        self,
        input: AgentInput,
        output: AgentOutput,
        conversation_id: str,
    ) -> None:
        """Extract fields from context/tool results and persist wizard state."""
        try:
            from app.orchestrator.wizard_state import set_wizard_state
            state = self._current_wizard_state
            ctx = input.context or {}

            # Merge any fields explicitly provided in input context
            # (some callers pass pre-extracted fields via context)
            field_map = {
                "title": "title",
                "department": "department",
                "location": "location",
                "seniority": "seniority",
                "work_model": "work_model",
                "salary_min": "salary_min",
                "salary_max": "salary_max",
                "skills": "skills",
                "description": "description",
                "draft_id": "draft_id",
            }
            for ctx_key, attr in field_map.items():
                val = ctx.get(ctx_key)
                if val is not None:
                    setattr(state, attr, val)

            # Advance step based on collected fields
            if state.step == "init" and (state.title or state.department):
                state.step = "collecting"
            elif state.draft_id and state.step in ("init", "collecting"):
                state.step = "saved"

            await set_wizard_state(conversation_id, state)
        except Exception as exc:
            logger.debug("[WizardReActAgent] wizard_state persist failed (fail-safe): %s", exc)

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
        }
