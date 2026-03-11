"""
Wizard ReAct Agent - Autonomous agent for job creation wizard.

This is the reference implementation of a domain-specific agent.
It uses the ReAct loop with wizard-specific tools, prompts, and context.
Other domain agents (Pipeline, Sourcing, etc.) should follow this pattern.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from app.shared.agents.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    BaseAgent,
    NavigationCommand,
)
from app.shared.agents.enhanced_agent_mixin import EnhancedAgentMixin
from app.shared.agents.langgraph_react_base import LangGraphReActBase
from app.shared.agents.react_loop import ReActConfig, ReActLoop, ReActState
from app.shared.compliance.audit_callback import AuditCallback
from app.shared.agents.working_memory import WorkingMemoryService
from app.shared.agents.observability import ReActObserver

from app.domains.job_management.agents.stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
    get_transition_prompt,
)
from app.domains.job_management.agents.wizard_system_prompt import build_system_prompt
from app.domains.job_management.agents.wizard_tool_registry import (
    get_stage_tools,
    get_wizard_tools,
)

logger = logging.getLogger(__name__)

_CONFIRMATION_WORDS = {
    "sim", "pode", "vamos", "avanca", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "confirmo", "positivo",
}


class WizardReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """Autonomous agent for the job creation wizard.

    Dual-path: usa LangGraph nativo quando USE_LANGGRAPH_NATIVE=True,
    caso contrário mantém o ReActLoop customizado (Phase 2).
    """

    def __init__(self) -> None:
        """Initialise the wizard agent with working memory service."""
        super().__init__()  # inicializa LangGraphBase._checkpointer
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_wizard_tools()]
        self._setup_enhanced(domain="wizard")
        logger.info("[WizardReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        """Return the domain identifier for this agent."""
        return "wizard"

    @property
    def available_tools(self) -> List[str]:
        """Return the list of all tool names this agent can use."""
        return list(self._all_tool_names)

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tools(self) -> list:
        """Todos os tools do domínio Wizard (LangGraph usa set completo)."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_wizard_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Wizard baseado no estágio atual."""
        current_stage = input.context.get("current_stage", "input-evaluation")
        collected_fields = input.context.get("collected_data", {})
        stage_ctx = get_stage_context(current_stage, collected_fields)
        return build_system_prompt(stage_context=stage_ctx, memory_summary="")

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Converte MessagesState final em AgentOutput com NavigationCommand."""
        from app.core.config import settings as _s
        messages = state.get("messages", [])

        # Última mensagem do agente (sem tool_call_id = resposta final)
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content and not getattr(m, "tool_call_id", None) and not (isinstance(m, dict) and m.get("tool_call_id")):
                response = content if isinstance(content, str) else str(content)
                break
        if not response:
            response = "Desculpe, não consegui processar sua solicitação."

        # Extrair actions das tool calls
        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        # Tentar NavigationCommand (mesma lógica do path legado)
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
        except Exception:
            pass

        return AgentOutput(
            message=response,
            actions=actions,
            navigation=navigation,
            confidence=0.85,
            metadata={"source": "langgraph_native", "domain": self.domain_name},
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
        """Path legado Phase 2 — ReActLoop customizado (inalterado)."""
        start_time = time.time()
        current_stage = input.context.get("current_stage", "input-evaluation")
        collected_fields: Dict[str, Any] = input.context.get("collected_data", {})

        logger.info(
            f"[WizardReActAgent] Processing message for session={input.session_id} "
            f"stage={current_stage}"
        )

        try:
            memory = await self._memory_service.get_or_create(
                session_id=input.session_id,
                domain=self.domain_name,
                company_id=input.company_id,
                user_id=input.user_id,
            )

            if memory.current_stage != current_stage:
                await self._memory_service.update_memory(
                    session_id=input.session_id,
                    domain=self.domain_name,
                    updates={"current_stage": current_stage},
                )

            memory_summary = await self._memory_service.get_context_summary(
                session_id=input.session_id,
                domain=self.domain_name,
            )

            extra_context = await self._get_memory_context(session_id=input.session_id, company_id=input.company_id)
            guardrails = await self._resolve_guardrails(input.company_id)

            stage_ctx = get_stage_context(current_stage, collected_fields)

            tools = get_stage_tools(current_stage) + self._get_all_enhanced_tools()

            system_prompt = build_system_prompt(
                stage_context=stage_ctx,
                memory_summary=memory_summary,
            )

            audit_callback = AuditCallback(
                user_id=str(input.user_id or "system"),
                company_id=str(input.company_id or ""),
                session_id=str(input.session_id),
                domain=self.domain_name,
                agent_type="react",
            )

            config = ReActConfig(
                max_iterations=5,
                system_prompt=system_prompt,
                available_tools=tools,
                domain=self.domain_name,
                model_provider="claude",
                temperature=0.3,
                guardrails=guardrails,
                extra_context=extra_context,
                audit_callback=audit_callback,
            )

            loop = ReActLoop(config=config, working_memory_service=self._memory_service)

            observer = None
            try:
                observer = ReActObserver(
                    session_id=input.session_id,
                    domain="wizard",
                    agent_class="WizardReActAgent",
                    company_id=input.company_id,
                    user_id=input.user_id,
                )
                observer.log.stage_before = current_stage
                observer.log.user_message_length = len(input.message)
                observer.log.model_provider = config.model_provider
            except Exception as obs_err:
                logger.warning(f"[WizardReActAgent] Failed to create observer: {obs_err}")
                observer = None

            state = await loop.run(
                message=input.message,
                context={
                    "current_stage": current_stage,
                    "collected_data": collected_fields,
                    "company_id": input.company_id,
                    "user_id": input.user_id,
                    "conversation_history": [
                        {"role": m.get("role", "user"), "content": m.get("content", "")}
                        for m in input.conversation_history[-5:]
                    ],
                },
                session_id=input.session_id,
                observer=observer,
            )

            output = await self._build_output(state, current_stage, collected_fields, input)

            await self._post_loop_learning(state=state, company_id=input.company_id, session_id=input.session_id, context={"stage": current_stage})

            await self._update_memory_after_loop(
                state=state,
                output=output,
                session_id=input.session_id,
                current_stage=current_stage,
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[WizardReActAgent] Completed in {duration_ms:.0f}ms "
                f"iterations={state.iteration} tools={len(state.tool_calls_made)}"
            )
            output.metadata["duration_ms"] = round(duration_ms, 1)

            try:
                if observer:
                    observer.finalize(
                        confidence=output.confidence,
                        response_length=len(output.message),
                        stage_after=output.navigation.target_stage if output.navigation else current_stage,
                    )
            except Exception as obs_err:
                logger.warning(f"[WizardReActAgent] Failed to finalize observer: {obs_err}")

            return output

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[WizardReActAgent] Error processing message: {exc}",
                exc_info=True,
            )
            return AgentOutput(
                message=(
                    "Desculpe, encontrei um problema ao processar sua mensagem. "
                    "Pode tentar novamente? Se o problema persistir, tente "
                    "reformular sua solicitacao."
                ),
                error=str(exc),
                confidence=0.0,
                metadata={"duration_ms": round(duration_ms, 1)},
            )

    async def _build_output(
        self,
        state: ReActState,
        current_stage: str,
        collected_fields: Dict[str, Any],
        input: AgentInput,
    ) -> AgentOutput:
        """Convert ReActState into AgentOutput.

        Args:
            state: Final state from the ReAct loop.
            current_stage: Current wizard stage.
            collected_fields: Fields collected so far.
            input: Original agent input.

        Returns:
            Structured AgentOutput.
        """
        message = state.final_response or "Desculpe, nao consegui gerar uma resposta. Pode repetir?"

        actions = []
        for action_record in state.actions_taken:
            action_type = action_record.get("type", "unknown")
            params = {}
            if action_type == "call_tool":
                params = {
                    "tool": action_record.get("tool", ""),
                    "args": action_record.get("args", {}),
                }
            elif action_type == "guardrail_blocked":
                params = {
                    "tool": action_record.get("tool", ""),
                    "reason": action_record.get("reason", ""),
                }
            actions.append(
                AgentAction(
                    action_type=action_type,
                    params=params,
                    requires_confirmation=action_type == "guardrail_blocked",
                )
            )

        field_updates = await self._extract_field_updates(state, input.context)

        navigation = await self._check_navigation(state, current_stage, collected_fields)

        reasoning_steps = []
        if state.current_reasoning:
            reasoning_steps.append(state.current_reasoning[:500])
        for obs in state.observations:
            reasoning_steps.append(obs[:300])

        tool_results = []
        for tc in state.tool_calls_made:
            tool_results.append({
                "tool_name": tc.get("tool_name", ""),
                "result": tc.get("result", {}),
                "duration_ms": tc.get("duration_ms", 0),
            })

        confidence = 0.7
        if state.error:
            confidence = 0.3
        elif field_updates:
            confidence = 0.85
        elif navigation:
            confidence = 0.8

        return AgentOutput(
            message=message,
            actions=actions,
            state_updates=field_updates,
            navigation=navigation,
            confidence=confidence,
            reasoning_steps=reasoning_steps,
            tool_results=tool_results,
            error=state.error,
            metadata={
                "iterations": state.iteration,
                "tools_called": len(state.tool_calls_made),
                "stage": current_stage,
            },
        )

    async def _extract_field_updates(
        self,
        state: ReActState,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract field updates from tool results and reasoning.

        Args:
            state: Final ReAct loop state.
            context: Original input context.

        Returns:
            Dictionary of field name to updated value.
        """
        updates: Dict[str, Any] = {}

        for tc in state.tool_calls_made:
            tool_name = tc.get("tool_name", "")
            result = tc.get("result", {})

            if not result.get("success", True):
                continue

            if tool_name == "validate_job_fields":
                pass

            elif tool_name == "search_salary_benchmark":
                salary_range = result.get("salary_range", {})
                if salary_range:
                    updates["salary_benchmark"] = salary_range

            elif tool_name == "get_job_suggestions":
                suggestions = result.get("suggestions", [])
                field_name = result.get("field_name", "")
                if suggestions and field_name:
                    updates[f"{field_name}_suggestions"] = suggestions

            elif tool_name == "generate_enriched_jd":
                sections = result.get("sections", [])
                if sections:
                    updates["enrichment_data"] = result

            elif tool_name == "get_company_config":
                updates["company_config"] = {
                    k: v
                    for k, v in result.items()
                    if k not in ("company_id", "config_type", "source")
                }

        return updates

    async def _check_navigation(
        self,
        state: ReActState,
        current_stage: str,
        collected_fields: Dict[str, Any],
    ) -> Optional[NavigationCommand]:
        """Determine whether a stage transition should be suggested.

        Checks the final response text for confirmation signals and
        evaluates whether the transition criteria for the current stage
        are met. Never auto-navigates without explicit user confirmation.

        Args:
            state: Final ReAct loop state.
            current_stage: Current wizard stage.
            collected_fields: Fields collected so far.

        Returns:
            NavigationCommand if a transition is appropriate, else None.
        """
        stage_def = STAGE_DEFINITIONS.get(current_stage)
        if not stage_def:
            return None

        next_stage = stage_def.get("next_stage", "")
        if not next_stage:
            return None

        required = stage_def.get("required_fields", [])
        missing_required = [
            f for f in required
            if collected_fields.get(f) in (None, "", [])
        ]

        if missing_required:
            logger.debug(
                f"[WizardReActAgent] Cannot navigate: missing required fields "
                f"{missing_required} for stage {current_stage}"
            )
            return None

        user_messages = [
            m.get("content", "").lower()
            for m in (state.messages or [])
            if m.get("role") == "user"
        ]
        last_user_message = user_messages[-1] if user_messages else ""
        user_confirmed = any(word in last_user_message for word in _CONFIRMATION_WORDS)

        if not user_confirmed:
            logger.debug(
                f"[WizardReActAgent] Required fields met for {current_stage} "
                f"but user has not confirmed advancement"
            )
            return None

        return NavigationCommand(
            target_stage=next_stage,
            reason=stage_def.get("transition_criteria", "Criterios atendidos"),
            auto_navigate=False,
        )

    async def _update_memory_after_loop(
        self,
        state: ReActState,
        output: AgentOutput,
        session_id: str,
        current_stage: str,
    ) -> None:
        """Persist relevant information to working memory after a loop run.

        Args:
            state: Final ReAct loop state.
            output: Built agent output.
            session_id: Session identifier.
            current_stage: Current wizard stage.
        """
        try:
            updates: Dict[str, Any] = {}

            if output.state_updates:
                existing_fields: Dict[str, Any] = {}
                try:
                    memory = await self._memory_service.get_or_create(
                        session_id=session_id,
                        domain=self.domain_name,
                        company_id="",
                        user_id="",
                    )
                    raw_fields = memory.collected_fields
                    existing_fields = dict(raw_fields) if isinstance(raw_fields, dict) else {}
                except Exception:
                    pass
                existing_fields.update(output.state_updates)
                updates["collected_fields"] = existing_fields

            if output.navigation:
                updates["current_stage"] = output.navigation.target_stage

            if state.current_reasoning:
                updates["agent_notes"] = state.current_reasoning[:1000]

            if updates:
                await self._memory_service.update_memory(
                    session_id=session_id,
                    domain=self.domain_name,
                    updates=updates,
                )
                logger.debug(
                    f"[WizardReActAgent] Updated memory: {list(updates.keys())}"
                )
        except Exception as exc:
            logger.warning(
                f"[WizardReActAgent] Failed to update memory: {exc}"
            )

    async def get_status(self) -> dict:
        """Return the current status and health information of the agent.

        Returns:
            Dictionary with domain, tools, and health status.
        """
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
        }
