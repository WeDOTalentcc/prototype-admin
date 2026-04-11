import contextvars
import functools
import logging
import time
from typing import Any, Optional

from lia_agents_core.agent_interface import AgentInput, AgentOutput, AgentAction
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase

logger = logging.getLogger(__name__)

_CURRENT_COMPANY_ID: contextvars.ContextVar[str] = contextvars.ContextVar(
    "custom_agent_company_id", default=""
)

PLATFORM_TOOLS_REGISTRY: dict[str, str] = {
    "search_candidates": "read",
    "list_jobs": "read",
    "get_job_details": "read",
    "get_candidate_details": "read",
    "get_pipeline_summary": "read",
    "search_talent_pool": "read",
    "get_analytics_summary": "read",
    "get_company_culture": "read",
    "get_evaluation_criteria": "read",
    "summarize_context": "read",
    "clarify_request": "read",
    "move_candidate": "write",
    "send_email": "write",
    "update_candidate_field": "write",
    "schedule_interview": "write",
    "create_note": "write",
}


def get_available_tool_names() -> list[str]:
    return list(PLATFORM_TOOLS_REGISTRY.keys())


class CustomAgentRuntime(LangGraphReActBase, EnhancedAgentMixin):

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        system_prompt: str,
        allowed_tools: list[str],
        domain: str = "custom",
        max_steps: int = 8,
        temperature: float = 0.7,
        model_override: Optional[str] = None,
        company_id: str = "",
    ) -> None:
        super().__init__()
        self._agent_id = agent_id
        self._agent_name = agent_name
        self._system_prompt_template = system_prompt
        self._allowed_tools = allowed_tools
        self._domain = domain
        self._max_steps = max_steps
        self._temperature = temperature
        self._model_override = model_override
        self._company_id = company_id
        self._setup_enhanced(domain=f"custom:{agent_name}")
        logger.info(
            "[CustomAgentRuntime] Initialized agent=%s tools=%d max_steps=%d",
            agent_name,
            len(allowed_tools),
            max_steps,
        )

    @property
    def domain_name(self) -> str:
        return f"custom:{self._agent_name}"

    @property
    def available_tools(self) -> list[str]:
        return list(self._allowed_tools)

    def _get_tools(self) -> list:
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool

        try:
            from app.domains.autonomous.agents.autonomous_tool_registry import get_autonomous_tools
            all_tools = get_autonomous_tools()
        except Exception:
            all_tools = []

        enhanced_tools = self._get_all_enhanced_tools()
        all_available = {td.name: td for td in all_tools + enhanced_tools}

        filtered = []
        for tool_name in self._allowed_tools:
            if tool_name in all_available:
                td = all_available[tool_name]
                original_fn = td.function
                _is_write = PLATFORM_TOOLS_REGISTRY.get(tool_name, "read") == "write"

                @functools.wraps(original_fn)
                async def _tenant_safe_wrapper(
                    *args: Any,
                    _fn=original_fn,
                    _write=_is_write,
                    **kwargs: Any,
                ) -> Any:
                    request_company_id = _CURRENT_COMPANY_ID.get("")
                    if request_company_id:
                        kwargs["company_id"] = request_company_id
                    else:
                        kwargs.pop("company_id", None)

                    if _write and not kwargs.get("confirm"):
                        return {
                            "success": False,
                            "message": "Operação de escrita bloqueada: confirm=True necessário.",
                        }
                    return await _fn(*args, **kwargs)

                try:
                    wrapped_td = td.model_copy(update={"function": _tenant_safe_wrapper})
                except AttributeError:
                    wrapped_td = td
                filtered.append(wrapped_td)

        return [tool_definition_to_langchain_tool(td) for td in filtered]

    async def _run_graph(
        self,
        initial_state: dict,
        session_id: str,
        audit_callback: Any = None,
        streaming_callback: Any = None,
    ) -> dict:
        compiled = self._get_compiled_graph()
        if compiled is None:
            raise RuntimeError(f"[CustomAgentRuntime:{self._agent_name}] Grafo LangGraph não disponível")

        config: dict[str, Any] = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": self._max_steps * 2 + 1,
        }
        callbacks = [cb for cb in [audit_callback, streaming_callback] if cb is not None]
        if callbacks:
            config["callbacks"] = callbacks

        return await compiled.ainvoke(initial_state, config=config)

    def _get_system_prompt(self, input: AgentInput) -> str:
        context_snippet = ""
        if input.context:
            for key, value in input.context.items():
                if value and isinstance(value, str) and len(value) < 500:
                    context_snippet += f"\n{key}: {value}"
        return self._system_prompt_template + context_snippet

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
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
            response = "Não consegui processar sua solicitação. Por favor, tente reformular."

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=0.8,
            metadata={
                "source": "custom_agent_runtime",
                "agent_id": self._agent_id,
                "agent_name": self._agent_name,
                "domain": self._domain,
                "tool_calls": len(actions),
            },
        )

    async def execute(
        self,
        message: str,
        user_id: str = "system",
        company_id: str = "",
        session_id: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> AgentOutput:
        effective_company_id = company_id or self._company_id
        _token = _CURRENT_COMPANY_ID.set(effective_company_id)

        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(message)
            if _fg_result.is_blocked:
                return AgentOutput(
                    message=_fg_result.educational_message or "Solicitação bloqueada por critérios de equidade.",
                    confidence=1.0,
                    metadata={"blocked": True, "reason": "fairness_guard"},
                )
        except Exception:
            pass

        try:
            agent_input = AgentInput(
                message=message,
                user_id=user_id,
                company_id=effective_company_id,
                session_id=session_id,
                context=context or {},
            )
            output = await self._process_langgraph(agent_input)
            return output
        except Exception as exc:
            _is_recursion = "recursion" in str(exc).lower()
            if _is_recursion:
                return AgentOutput(
                    message="O agente atingiu o limite máximo de passos. Tente reformular.",
                    confidence=0.0,
                    metadata={"budget_exhausted": True},
                )
            logger.error("[CustomAgentRuntime:%s] Error: %s", self._agent_name, exc, exc_info=True)
            return AgentOutput(
                message="Ocorreu um erro ao processar sua solicitação.",
                confidence=0.0,
                metadata={"error": str(exc)},
            )
        finally:
            _CURRENT_COMPANY_ID.reset(_token)


_runtime_cache: dict[str, CustomAgentRuntime] = {}


def get_or_create_runtime(
    agent_id: str,
    agent_name: str,
    system_prompt: str,
    allowed_tools: list[str],
    domain: str = "custom",
    max_steps: int = 8,
    temperature: float = 0.7,
    model_override: Optional[str] = None,
    company_id: str = "",
    force_new: bool = False,
) -> CustomAgentRuntime:
    cache_key = f"{agent_id}:{company_id}"
    if cache_key not in _runtime_cache or force_new:
        _runtime_cache[cache_key] = CustomAgentRuntime(
            agent_id=agent_id,
            agent_name=agent_name,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            domain=domain,
            max_steps=max_steps,
            temperature=temperature,
            model_override=model_override,
            company_id=company_id,
        )
    return _runtime_cache[cache_key]
