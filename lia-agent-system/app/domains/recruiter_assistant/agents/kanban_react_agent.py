"""
Kanban ReAct Agent - Autonomous agent for strategic pipeline analysis.

Implements the BaseAgent interface using a ReAct loop with kanban-specific
tools, prompts and stage context. Provides macro-level analytics, bottleneck
identification, and pipeline optimization recommendations. Follows the same
pattern as PipelineReActAgent.
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

from app.domains.recruiter_assistant.agents.kanban_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
    get_transition_prompt,
    get_journey_insight_block,
    get_pipeline_prediction_block,
)
from app.domains.recruiter_assistant.agents.kanban_system_prompt import get_kanban_system_prompt
from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
    get_kanban_tools,
    GUARDRAIL_TOOLS,
)

logger = logging.getLogger(__name__)

_CONFIRMATION_WORDS = {
    "sim", "pode", "confirmo", "mover", "avanca", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "positivo", "vamos",
}


class KanbanReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """Autonomous agent for strategic pipeline analysis and optimization.

    Implements the BaseAgent interface using a ReAct loop with
    kanban-specific tools, prompts and stage context. Each call to
    ``process`` runs a full Reason-Act-Observe cycle and returns a
    structured AgentOutput.
    """

    def __init__(self) -> None:
        super().__init__()  # inicializa LangGraphBase._checkpointer
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_kanban_tools()]
        self._setup_enhanced(domain="kanban")
        logger.info("[KanbanReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "kanban"

    @property
    def available_tools(self) -> List[str]:
        return list(self._all_tool_names)

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tools(self) -> list:
        """Todos os tools do domínio Kanban (LangGraph usa set completo)."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_kanban_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Kanban baseado no estágio atual."""
        current_stage = input.context.get("current_stage", "pipeline_overview")
        collected_fields = input.context.get("collected_data", {})
        stage_ctx = get_stage_context(current_stage, collected_fields)
        return get_kanban_system_prompt(
            stage=current_stage,
            context={"stage_context": stage_ctx, "memory_summary": ""},
        )

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Converte MessagesState final em AgentOutput com NavigationCommand."""
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content and not getattr(m, "tool_call_id", None) and not (isinstance(m, dict) and m.get("tool_call_id")):
                response = content if isinstance(content, str) else str(content)
                break
        if not response:
            response = "Desculpe, não consegui processar sua solicitação."

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        current_stage = input.context.get("current_stage", "pipeline_overview")
        collected_fields = input.context.get("collected_data", {})
        navigation = None
        try:
            stage_def = STAGE_DEFINITIONS.get(current_stage, {})
            next_stage = stage_def.get("next_stage", "")
            if next_stage and next_stage != "complete":
                criteria = stage_def.get("transition_criteria", {})
                required = criteria.get("required", [])
                missing = [f for f in required if collected_fields.get(f) in (None, "", [])]
                if not missing:
                    user_msgs = [
                        (m.content if hasattr(m, "content") else m.get("content", "")).lower()
                        for m in messages
                        if (getattr(m, "type", "") == "human" or (isinstance(m, dict) and m.get("role") == "user"))
                    ]
                    last_user = user_msgs[-1] if user_msgs else ""
                    if any(w in last_user for w in _CONFIRMATION_WORDS):
                        navigation = NavigationCommand(
                            target_stage=next_stage,
                            reason=criteria.get("description", "Critérios atendidos"),
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
        # P0-A: FairnessGuard automático — bloqueia critérios discriminatórios antes do loop
        _blocked_msg = await self._fairness_pre_check(input.message or "")
        if _blocked_msg:
            return AgentOutput(
                message=_blocked_msg,
                confidence=1.0,
                metadata={"source": "fairness_guard", "domain": self.domain_name},
            )
        from app.core.config import settings
        if settings.USE_LANGGRAPH_NATIVE:
            return await self._process_langgraph(input)
        return await self._process_react_loop(input)

    async def _process_react_loop(self, input: AgentInput) -> AgentOutput:
        """Process a user message through the kanban ReAct loop.

        Args:
            input: Standardised agent input with message, context and metadata.

        Returns:
            Standardised agent output with response, actions and state updates.
        """
        start_time = time.time()
        current_stage = input.context.get("current_stage", "pipeline_overview")
        collected_fields: Dict[str, Any] = input.context.get("collected_data", {})

        logger.info(
            f"[KanbanReActAgent] Processing message for session={input.session_id} "
            f"stage={current_stage}"
        )

        try:
            memory = await self._load_memory(
                session_id=input.session_id,
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

            # Sprint 2C — injeção contextual de saúde do pipeline quando vacancy_id presente
            vacancy_id = input.context.get("vacancy_id") or collected_fields.get("vacancy_id")
            if vacancy_id:
                try:
                    from app.services.journey_intelligence_service import journey_intelligence_service
                    journey_data = await journey_intelligence_service.get_vacancy_metrics(
                        vacancy_id=vacancy_id,
                        company_id=input.company_id,
                    )
                    insight_block = get_journey_insight_block(journey_data)
                    if insight_block:
                        stage_ctx = insight_block + "\n\n" + stage_ctx
                except Exception as je:
                    logger.debug(f"[KanbanReActAgent] journey insight skipped: {je}")

            # Sprint 3A — injeção de previsão de fechamento quando vacancy_id presente
            if vacancy_id:
                try:
                    from app.services.pipeline_prediction_service import pipeline_prediction_service
                    prediction_data = await pipeline_prediction_service.get_vacancy_prediction(
                        vacancy_id=vacancy_id,
                        company_id=input.company_id,
                    )
                    pred_block = get_pipeline_prediction_block(prediction_data)
                    if pred_block:
                        stage_ctx = pred_block + "\n\n" + stage_ctx
                except Exception as pe:
                    logger.debug(f"[KanbanReActAgent] pipeline prediction skipped: {pe}")

            tools = get_kanban_tools(current_stage) + self._get_all_enhanced_tools()

            system_prompt = get_kanban_system_prompt(
                stage=current_stage,
                context={
                    "stage_context": stage_ctx,
                    "memory_summary": memory_summary,
                },
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
                    domain="kanban",
                    agent_class="KanbanReActAgent",
                    company_id=input.company_id,
                    user_id=input.user_id,
                )
                observer.log.stage_before = current_stage
                observer.log.user_message_length = len(input.message)
                observer.log.model_provider = config.model_provider
            except Exception as obs_err:
                logger.warning(f"[KanbanReActAgent] Failed to create observer: {obs_err}")
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

            await self._save_memory(
                state=state,
                output=output,
                session_id=input.session_id,
                current_stage=current_stage,
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[KanbanReActAgent] Completed in {duration_ms:.0f}ms "
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
                logger.warning(f"[KanbanReActAgent] Failed to finalize observer: {obs_err}")

            return output

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[KanbanReActAgent] Error processing message: {exc}",
                exc_info=True,
            )
            return self._build_error_output(exc, duration_ms)

    async def _load_memory(
        self,
        session_id: str,
        company_id: str,
        user_id: str,
    ):
        """Load or create working memory for the session.

        Args:
            session_id: Session identifier.
            company_id: Company ID for multi-tenancy.
            user_id: User interacting with the agent.

        Returns:
            AgentWorkingMemory instance.
        """
        return await self._memory_service.get_or_create(
            session_id=session_id,
            domain=self.domain_name,
            company_id=company_id,
            user_id=user_id,
        )

    async def _save_memory(
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
            current_stage: Current pipeline stage.
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
                    f"[KanbanReActAgent] Updated memory: {list(updates.keys())}"
                )
        except Exception as exc:
            logger.warning(
                f"[KanbanReActAgent] Failed to update memory: {exc}"
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
            current_stage: Current kanban analysis phase.
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

    def _build_error_output(self, exc: Exception, duration_ms: float) -> AgentOutput:
        """Build a standardised error output.

        Args:
            exc: The exception that caused the error.
            duration_ms: Time elapsed before the error.

        Returns:
            AgentOutput with error information.
        """
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

            if tool_name == "get_pipeline_summary":
                updates["pipeline_reviewed"] = True

            elif tool_name == "analyze_stage":
                updates["stage_analysis_completed"] = True

            elif tool_name == "identify_bottlenecks":
                updates["bottlenecks_identified"] = True
                updates["stage_analysis_completed"] = True

            elif tool_name == "get_candidate_aging":
                updates["aging_report_generated"] = True

            elif tool_name == "compare_stages":
                updates["stages_compared"] = True

            elif tool_name == "batch_move_candidates":
                updates["actions_executed"] = True

            elif tool_name == "send_batch_communication":
                updates["batch_communication_sent"] = True
                updates["actions_executed"] = True

            elif tool_name == "start_screening_batch":
                updates["screening_started"] = True
                updates["actions_executed"] = True

            elif tool_name == "generate_pipeline_report":
                updates["report_generated"] = True
                updates["actions_executed"] = True

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
            current_stage: Current kanban analysis phase.
            collected_fields: Fields collected so far.

        Returns:
            NavigationCommand if a transition is appropriate, else None.
        """
        stage_def = STAGE_DEFINITIONS.get(current_stage)
        if not stage_def:
            return None

        next_stage = stage_def.get("next_stage", "")
        if not next_stage or next_stage == "complete":
            return None

        criteria = stage_def.get("transition_criteria", {})
        required = criteria.get("required", [])
        missing_required = [
            f for f in required
            if collected_fields.get(f) in (None, "", [])
        ]

        if missing_required:
            logger.debug(
                f"[KanbanReActAgent] Cannot navigate: missing required fields "
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
                f"[KanbanReActAgent] Required fields met for {current_stage} "
                f"but user has not confirmed advancement"
            )
            return None

        return NavigationCommand(
            target_stage=next_stage,
            reason=criteria.get("description", "Criterios atendidos"),
            auto_navigate=False,
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
