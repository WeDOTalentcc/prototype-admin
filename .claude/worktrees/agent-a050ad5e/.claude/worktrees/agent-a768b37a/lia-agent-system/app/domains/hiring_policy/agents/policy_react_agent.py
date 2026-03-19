"""
Policy ReAct Agent - Autonomous agent for hiring policy configuration.

Implements the BaseAgent interface using a ReAct loop with policy-specific
tools, prompts and stage context. Manages hiring policy configuration through
an intelligent conversational interface with compliance validation.

Replaces the old linear PolicySetupAgent with a true ReAct agent that reasons
about compliance, explains trade-offs, and proactively validates policies.
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
from app.shared.compliance.fairness_guard import FairnessGuard

from app.domains.hiring_policy.agents.policy_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
)
from app.domains.hiring_policy.agents.policy_system_prompt import get_policy_system_prompt
from app.domains.hiring_policy.agents.policy_tool_registry import get_policy_tools

logger = logging.getLogger(__name__)

_CONFIRMATION_WORDS = {
    "sim", "pode", "confirmo", "salva", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "positivo", "vamos",
    "avancar", "continua",
}


class PolicyReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """Autonomous agent for hiring policy configuration.

    Implements the BaseAgent interface using a ReAct loop with
    policy-specific tools, compliance validation via FairnessGuard,
    and consultive reasoning about trade-offs and consequences.
    """

    def __init__(self) -> None:
        super().__init__()  # inicializa LangGraphBase._checkpointer
        self._memory_service = WorkingMemoryService()
        self._setup_enhanced(domain="policy")
        self._fairness_guard = FairnessGuard()
        self._all_tool_names = [t.name for t in get_policy_tools()]
        logger.info("[PolicyReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "policy"

    @property
    def available_tools(self) -> List[str]:
        return list(self._all_tool_names)

    # ------------------------------------------------------------------
    # LangGraph Phase 3 — overrides
    # ------------------------------------------------------------------

    def _get_tools(self) -> list:
        """Todos os tools do domínio Policy (LangGraph usa set completo)."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_policy_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_system_prompt(self, input: AgentInput) -> str:
        """System prompt do Policy baseado no estágio atual."""
        current_stage = input.context.get("current_stage", "onboarding")
        policy_state = input.context.get("policy_state", {})
        stage_ctx = get_stage_context(current_stage, policy_state)
        return get_policy_system_prompt(
            stage=current_stage,
            context={"stage_context": stage_ctx, "memory_summary": ""},
        )

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Converte MessagesState final em AgentOutput."""
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

        return AgentOutput(
            message=response,
            actions=actions,
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
        start_time = time.time()
        current_stage = input.context.get("current_stage", "onboarding")
        policy_state = input.context.get("policy_state", {})

        logger.info(
            f"[PolicyReActAgent] Processing message for session={input.session_id} "
            f"stage={current_stage}"
        )

        try:
            compliance_check = self._fairness_guard.check(input.message)
            if compliance_check.is_blocked:
                logger.warning(
                    f"[PolicyReActAgent] FairnessGuard blocked input: "
                    f"category={compliance_check.category}"
                )
                return AgentOutput(
                    message=compliance_check.educational_message or (
                        "Nao posso aceitar essa configuracao pois viola criterios de compliance."
                    ),
                    confidence=0.95,
                    metadata={
                        "compliance_blocked": True,
                        "category": compliance_check.category,
                        "duration_ms": round((time.time() - start_time) * 1000, 1),
                    },
                )

            memory = await self._load_memory(
                session_id=input.session_id,
                company_id=input.company_id,
                user_id=input.user_id,
            )

            memory_summary = await self._memory_service.get_context_summary(
                session_id=input.session_id,
                domain=self.domain_name,
            )

            extra_context = await self._get_memory_context(
                session_id=input.session_id,
                company_id=input.company_id,
            )

            guardrails = await self._resolve_guardrails(input.company_id)

            stage_ctx = get_stage_context(current_stage, policy_state)

            tools = get_policy_tools() + self._get_all_enhanced_tools()

            system_prompt = get_policy_system_prompt(
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
                    domain="policy",
                    agent_class="PolicyReActAgent",
                    company_id=input.company_id,
                    user_id=input.user_id,
                )
                observer.log.stage_before = current_stage
                observer.log.user_message_length = len(input.message)
                observer.log.model_provider = config.model_provider
            except Exception as obs_err:
                logger.warning(f"[PolicyReActAgent] Failed to create observer: {obs_err}")
                observer = None

            state = await loop.run(
                message=input.message,
                context={
                    "current_stage": current_stage,
                    "policy_state": policy_state,
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

            output = await self._build_output(state, current_stage, policy_state, input)

            await self._post_loop_learning(
                state=state,
                company_id=input.company_id,
                session_id=input.session_id,
                context={"stage": current_stage},
            )

            await self._save_memory(
                state=state,
                output=output,
                session_id=input.session_id,
                current_stage=current_stage,
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[PolicyReActAgent] Completed in {duration_ms:.0f}ms "
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
                logger.warning(f"[PolicyReActAgent] Failed to finalize observer: {obs_err}")

            return output

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[PolicyReActAgent] Error processing message: {exc}",
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

    async def process_legacy_format(
        self,
        message: str,
        company_id: str,
        session_id: str,
        current_policy: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Process a message using legacy format compatible with the old PolicySetupAgent API.

        This method bridges the new ReAct agent with the existing frontend
        that expects the old response format (reply, current_block, setup_progress, etc.).
        """
        agent_input = AgentInput(
            message=message,
            context={
                "current_stage": "onboarding",
                "policy_state": current_policy,
            },
            session_id=session_id,
            company_id=company_id,
            user_id="default_user",
            conversation_history=conversation_history or [],
        )

        output = await self.process(agent_input)

        current_block = None
        updated_fields = {}
        for tc in output.tool_results:
            if tc.get("tool_name") == "save_policy_field":
                result = tc.get("result", {})
                if result.get("success"):
                    data = result.get("data", {})
                    block = data.get("block", "")
                    field = data.get("field", "")
                    value = data.get("value")
                    if block and field:
                        if block not in updated_fields:
                            updated_fields[block] = {}
                        updated_fields[block][field] = value
                        current_block = block

        setup_progress = 0
        for tc in output.tool_results:
            if tc.get("tool_name") == "get_setup_progress":
                result = tc.get("result", {})
                if result.get("success"):
                    setup_progress = result.get("data", {}).get("overall_progress", 0)

        block_name_map = {
            "pipeline_rules": "Pipeline e Processo",
            "scheduling_rules": "Agendamento",
            "communication_rules": "Comunicacao",
            "screening_rules": "Triagem",
            "automation_rules": "Autonomia da LIA",
        }

        return {
            "reply": output.message,
            "current_block": block_name_map.get(current_block, current_block),
            "current_question": None,
            "total_questions": 19,
            "setup_progress": setup_progress,
            "updated_fields": updated_fields,
            "block_completed": False,
            "all_completed": setup_progress >= 100,
            "compliance_blocked": output.metadata.get("compliance_blocked", False),
        }

    async def _load_memory(self, session_id: str, company_id: str, user_id: str):
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
        try:
            updates: Dict[str, Any] = {}

            if output.state_updates:
                updates["collected_fields"] = output.state_updates

            if state.current_reasoning:
                updates["agent_notes"] = state.current_reasoning[:1000]

            if updates:
                await self._memory_service.update_memory(
                    session_id=session_id,
                    domain=self.domain_name,
                    updates=updates,
                )
        except Exception as exc:
            logger.warning(f"[PolicyReActAgent] Failed to update memory: {exc}")

    async def _build_output(
        self,
        state: ReActState,
        current_stage: str,
        policy_state: Dict[str, Any],
        input: AgentInput,
    ) -> AgentOutput:
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

        field_updates = self._extract_field_updates(state)

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
        elif any(tc.get("tool_name") == "validate_policy_compliance" for tc in state.tool_calls_made):
            confidence = 0.9

        return AgentOutput(
            message=message,
            actions=actions,
            state_updates=field_updates,
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

    def _extract_field_updates(self, state: ReActState) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        for tc in state.tool_calls_made:
            tool_name = tc.get("tool_name", "")
            result = tc.get("result", {})

            if not result.get("success", True):
                continue

            if tool_name == "save_policy_field":
                data = result.get("data", {})
                block = data.get("block", "")
                field = data.get("field", "")
                value = data.get("value")
                if block and field:
                    updates[f"{block}_configured"] = True
                    updates[f"{block}.{field}"] = value

        return updates

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
            "compliance_guard": "FairnessGuard",
        }
