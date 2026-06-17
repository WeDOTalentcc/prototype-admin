"""
Wizard ReAct Agent - Autonomous agent for job creation wizard.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.
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

_CONFIRMATION_WORDS = {
    "sim", "pode", "vamos", "avanca", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "confirmo", "positivo",
}


from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer

@register_agent("wizard")
class WizardReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    """Wizard de criação de vaga — piloto canônico da TenantAwareAgentMixin (T-B).

    Wizard é fail-CLOSED por design: NUNCA pode operar sem tenant resolvido.
    Antes desta refatoração, o override de ``_get_runtime_domain_instructions``
    chamava ``PromptComposer.for_domain_runtime`` direto (sem
    ``tenant_context_snippet``) — derrubando o snippet que o
    ``MainOrchestrator`` / handlers SSE/WS injetavam em ``input.context``.
    Resultado em produção: a LIA perguntava "qual o ID da sua empresa?" no
    chat do wizard, mesmo com JWT correto.

    Refatoração:
        1. Herda de ``TenantAwareAgentMixin`` (primeiro no MRO) → ganha
           pre-resolução async em ``_process_langgraph`` + override sync de
           defesa em profundidade em ``_get_system_prompt``.
        2. ``tenant_strict_override = True`` → mesmo com
           ``LIA_AGENT_TENANT_STRICT=false`` em dev, o wizard fail-closes.
        3. ``_get_runtime_domain_instructions`` agora usa
           ``self._compose_runtime_prompt(...)`` em vez de chamar o composer
           direto — o helper auto-injeta ``tenant_context_snippet`` lido de
           ``input.context``.

    Origem da causa raiz e contrato canônico:
        ``app/shared/agents/tenant_aware_agent.py`` (T-A canônico).
    """

    # Wizard NUNCA degrada para "sua empresa" — força strict mesmo em dev.
    # Opt-out só via env auditável (LIA_AGENT_TENANT_STRICT) — bloqueado por
    # design no mixin (`tenant_strict_override` aceita True ou None).
    tenant_strict_override = True

    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="wizard",
        domain_specific=WIZARD_DOMAIN_SPECIFIC,
        reasoning_pattern=WIZARD_REASONING_PROMPT.format(memory_summary="", stage_context=""),
    ).text

    def _get_runtime_domain_instructions(self, input: AgentInput) -> str:
        """Substitui {memory_summary} + {stage_context} em runtime e
        propaga ``tenant_context_snippet`` via ``self._compose_runtime_prompt``
        (helper canônico do TenantAwareAgentMixin — T-B).

        Falls back to legacy DOMAIN_INSTRUCTIONS if PromptComposer fails.
        """
        try:
            ctx = input.context or {}
            return self._compose_runtime_prompt(
                input,
                domain_specific=WIZARD_DOMAIN_SPECIFIC,
                reasoning_template=WIZARD_REASONING_PROMPT,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[wizard] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    """Autonomous agent for the job creation wizard via LangGraph nativo."""

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_wizard_tools()]
        self._setup_enhanced(domain="wizard")
        logger.info("[WizardReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "wizard"

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)


    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.job_management.agents.wizard_tool_registry import get_wizard_tools
            return get_wizard_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """Todos os tools do domínio Wizard (LangGraph usa set completo)."""
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_wizard_tools() + self._get_all_enhanced_tools()
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
            response = "Desculpe, não consegui processar sua solicitação."

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
                        reason=stage_def.get("transition_criteria", "Critérios atendidos"),
                        auto_navigate=False,
                    )
        except Exception:  # ADR-031-R3-EXEMPT: deteccao opcional de navegacao por confirmacao do usuario; falha nao bloqueia resposta
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
        return await self._process_langgraph(input)

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
        }
