"""
Sourcing ReAct Agent - Autonomous agent for candidate search and screening.

Implements the BaseAgent interface using a ReAct loop with sourcing-specific
tools, prompts and stage context. Each call to ``process`` runs a full
Reason-Act-Observe cycle and returns a structured AgentOutput.
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

from app.domains.sourcing.agents.sourcing_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
    get_transition_prompt,
)
from app.domains.sourcing.agents.sourcing_system_prompt import get_sourcing_system_prompt
from app.domains.sourcing.agents.sourcing_tool_registry import (
    get_stage_tools,
    get_sourcing_tools,
)

logger = logging.getLogger(__name__)

_CONFIRMATION_WORDS = {
    "sim", "pode", "vamos", "avanca", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "confirmo", "positivo",
    "buscar", "enviar",
}


class SourcingReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """Autonomous agent for talent sourcing and candidate screening.

    Implements the BaseAgent interface using a ReAct loop with
    sourcing-specific tools, prompts and stage context. Each call to
    ``process`` runs a full Reason-Act-Observe cycle and returns a
    structured AgentOutput.
    """

    def __init__(self) -> None:
        """Initialise the sourcing agent with working memory service."""
        super().__init__()  # inicializa LangGraphBase._checkpointer
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_sourcing_tools()]
        self._setup_enhanced(domain="sourcing")
        logger.info("[SourcingReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        """Return the domain identifier for this agent."""
        return "sourcing"

    @property
    def available_tools(self) -> List[str]:
        """Return the list of all tool names this agent can use."""
        return list(self._all_tool_names)

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tools(self) -> list:
        """Todos os tools do domínio Sourcing (LangGraph usa set completo)."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_sourcing_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Sourcing baseado no estágio atual."""
        current_stage = input.context.get("current_stage", "search-criteria")
        collected_fields = input.context.get("collected_data", {})
        stage_ctx = get_stage_context(current_stage, collected_fields)
        return get_sourcing_system_prompt(
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

        current_stage = input.context.get("current_stage", "search-criteria")
        collected_fields = input.context.get("collected_data", {})
        navigation = None
        try:
            stage_def = STAGE_DEFINITIONS.get(current_stage, {})
            next_stage = stage_def.get("next_stage", "")
            if next_stage:
                required = stage_def.get("required_fields", [])
                missing = [f for f in required if collected_fields.get(f) in (None, "", [])]
                if not missing:
                    user_msgs = [
                        (m.content if hasattr(m, "content") else m.get("content", "")).lower()
                        for m in messages
                        if (getattr(m, "type", "") == "human" or (isinstance(m, dict) and m.get("role") == "user"))
                    ]
                    last_user = user_msgs[-1] if user_msgs else ""
                    if any(w in last_user for w in _CONFIRMATION_WORDS):
                        transition_criteria = stage_def.get("transition_criteria", {})
                        reason = transition_criteria.get("description", "Criterios atendidos") if isinstance(transition_criteria, dict) else str(transition_criteria)
                        navigation = NavigationCommand(
                            target_stage=next_stage,
                            reason=reason,
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

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """Override: adiciona audit SEG-5 após execução LangGraph nativa."""
        output = await super()._process_langgraph(input)

        # SEG-5: AuditService — caminho LangGraph nativo
        try:
            from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
            current_stage = input.context.get("current_stage", "search-criteria")
            await audit_service.log_decision(
                company_id=str(input.company_id or ""),
                agent_name="sourcing_react_agent",
                decision_type="score_candidate",
                action=f"sourcing_langgraph:{current_stage}",
                decision="completed",
                reasoning=[f"Sourcing via LangGraph native no stage {current_stage}"],
                criteria_used=[current_stage],
                criteria_ignored=list(PROTECTED_CRITERIA),
                confidence=output.confidence,
            )
        except Exception as _audit_exc:
            logger.debug("[SourcingReActAgent][SEG-5/LG] AuditService skipped: %s", _audit_exc)

        return output

    # ------------------------------------------------------------------
    # Dual-path: LangGraph nativo ou ReActLoop legado
    # ------------------------------------------------------------------

    async def process(self, input: AgentInput) -> AgentOutput:
        """Dual-path: LangGraph nativo (USE_LANGGRAPH_NATIVE=True) ou ReActLoop."""
        # SEG-2: FairnessGuard — verificar viés discriminatório na mensagem do recrutador
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(input.message)
            if _fg_result.is_blocked:
                logger.warning(
                    "[SourcingReActAgent][SEG-2] FairnessGuard bloqueou mensagem "
                    "session=%s category=%s terms=%s",
                    input.session_id, _fg_result.category, _fg_result.blocked_terms,
                )
                try:
                    await _fg.log_check(
                        input_text=input.message,
                        result=_fg_result,
                        context={"session_id": str(input.session_id), "domain": "sourcing"},
                        company_id=str(input.company_id or ""),
                    )
                except Exception:
                    pass
                return AgentOutput(
                    message=_fg_result.educational_message or (
                        "Esta solicitação não pode ser processada pois contém critérios "
                        "que podem ser discriminatórios. Por favor, reformule com base em "
                        "competências e requisitos técnicos da vaga."
                    ),
                    confidence=1.0,
                    metadata={
                        "fairness_blocked": True,
                        "fairness_category": _fg_result.category,
                        "domain": self.domain_name,
                    },
                )
            _soft_warnings = _fg.check_implicit_bias(input.message)
            if _soft_warnings:
                logger.info(
                    "[SourcingReActAgent][SEG-2] FairnessGuard soft warnings session=%s: %s",
                    input.session_id, _soft_warnings,
                )
        except Exception as _fg_exc:
            logger.debug("[SourcingReActAgent] FairnessGuard check skipped: %s", _fg_exc)
            _soft_warnings = []

        from app.core.config import settings
        if settings.USE_LANGGRAPH_NATIVE:
            return await self._process_langgraph(input)
        return await self._process_react_loop(input)

    async def _process_react_loop(self, input: AgentInput) -> AgentOutput:
        """Process a user message through the sourcing ReAct loop.

        Args:
            input: Standardised agent input with message, context and metadata.

        Returns:
            Standardised agent output with response, actions and state updates.
        """
        start_time = time.time()
        current_stage = input.context.get("current_stage", "search-criteria")
        collected_fields: Dict[str, Any] = input.context.get("collected_data", {})

        logger.info(
            f"[SourcingReActAgent] Processing message for session={input.session_id} "
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

            tools = get_stage_tools(current_stage) + self._get_all_enhanced_tools()

            system_prompt = get_sourcing_system_prompt(
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
                    domain="sourcing",
                    agent_class="SourcingReActAgent",
                    company_id=input.company_id,
                    user_id=input.user_id,
                )
                observer.log.stage_before = current_stage
                observer.log.user_message_length = len(input.message)
                observer.log.model_provider = config.model_provider
            except Exception as obs_err:
                logger.warning(f"[SourcingReActAgent] Failed to create observer: {obs_err}")
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

            # SEG-5: AuditService — registrar resultado da busca/triagem de candidatos
            try:
                from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
                await audit_service.log_decision(
                    company_id=str(input.company_id or ""),
                    agent_name="sourcing_react_agent",
                    decision_type="score_candidate",
                    action=f"sourcing:{current_stage}",
                    decision="completed",
                    reasoning=[f"Sourcing no stage {current_stage}"],
                    criteria_used=[current_stage],
                    criteria_ignored=list(PROTECTED_CRITERIA),
                    confidence=output.confidence,
                )
            except Exception as _audit_exc:
                logger.debug("[SourcingReActAgent][SEG-5] AuditService skipped: %s", _audit_exc)

            await self._post_loop_learning(state=state, company_id=input.company_id, session_id=input.session_id, context={"stage": current_stage})

            await self._save_memory(
                state=state,
                output=output,
                session_id=input.session_id,
                current_stage=current_stage,
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[SourcingReActAgent] Completed in {duration_ms:.0f}ms "
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
                logger.warning(f"[SourcingReActAgent] Failed to finalize observer: {obs_err}")

            return output

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[SourcingReActAgent] Error processing message: {exc}",
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

    async def _load_memory(
        self,
        session_id: str,
        company_id: str,
        user_id: str,
    ):
        """Load or create working memory for the sourcing session.

        Args:
            session_id: The session identifier.
            company_id: Company ID for multi-tenancy.
            user_id: The user interacting with the agent.

        Returns:
            The AgentWorkingMemory instance.
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
            current_stage: Current sourcing stage.
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
                    f"[SourcingReActAgent] Updated memory: {list(updates.keys())}"
                )
        except Exception as exc:
            logger.warning(
                f"[SourcingReActAgent] Failed to update memory: {exc}"
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
            current_stage: Current sourcing stage.
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

            if tool_name == "set_search_criteria":
                data = result.get("data", {})
                if data.get("role"):
                    updates["role"] = data["role"]
                if data.get("skills"):
                    updates["skills"] = data["skills"]
                if data.get("location"):
                    updates["location"] = data["location"]
                if data.get("experience_level"):
                    updates["experience_level"] = data["experience_level"]
                if data.get("salary_range"):
                    updates["salary_range"] = data["salary_range"]

            elif tool_name == "search_candidates":
                data = result.get("data", {})
                updates["search_executed"] = True
                if data.get("total_results") is not None:
                    updates["results_count"] = data["total_results"]

            elif tool_name == "filter_results":
                data = result.get("data", {})
                updates["filters_applied"] = data.get("filters_applied", {})

            elif tool_name == "analyze_profile":
                updates["candidates_analyzed"] = True

            elif tool_name == "score_candidate":
                data = result.get("data", {})
                updates["scoring_results"] = data

            elif tool_name == "compare_candidates":
                data = result.get("data", {})
                updates["comparison_data"] = data

            elif tool_name == "add_to_shortlist":
                updates["shortlist_created"] = True

            elif tool_name == "send_outreach":
                updates["outreach_sent"] = True

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
            current_stage: Current sourcing stage.
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
                f"[SourcingReActAgent] Cannot navigate: missing required fields "
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
                f"[SourcingReActAgent] Required fields met for {current_stage} "
                f"but user has not confirmed advancement"
            )
            return None

        transition_criteria = stage_def.get("transition_criteria", {})
        if isinstance(transition_criteria, dict):
            reason = transition_criteria.get("description", "Criterios atendidos")
        else:
            reason = transition_criteria

        return NavigationCommand(
            target_stage=next_stage,
            reason=reason,
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
